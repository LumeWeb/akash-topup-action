import logging
import time
from decimal import Decimal
from typing import Optional, List, Dict, Any

from .cli_wrapper import AkashCLI
from .utils import uakt_to_akt, akt_to_uakt, safe_get, parse_escrow_amount, calculate_transaction_fee
from .reporter import ActionReporter

class DeploymentManager:
    """
    Manages Akash deployment balances
    
    This class handles monitoring and automatic top-up of Akash deployment balances.
    It follows the Akash deployment schema structure:
    - deployment: Contains deployment_id (owner, dseq) and state
    - groups: Contains resource specifications and pricing
    - escrow_account: Contains balance information in the funds field
    """
    
    def __init__(self, min_threshold: int, top_up_amount: int):
        """
        Initialize manager
        
        Args:
            min_threshold: Minimum balance threshold in uakt (1 AKT = 1,000,000 uakt)
            top_up_amount: Amount to top up in uakt (minimum 0.5 AKT = 500,000 uakt)
            
        Schema validation:
            - Deployments must have deployment.state = "active"
            - Balance is read from escrow_account.funds.amount
        """
        self.min_threshold = min_threshold
        self.top_up_amount = top_up_amount
        self.logger = logging.getLogger(__name__)
        self.cli = AkashCLI()
        self.reporter = ActionReporter()

    def get_active_deployments(self) -> List[Dict[str, Any]]:
        """
        Get all active deployments
        
        Returns:
            List of deployment data following the schema:
            {
                "deployment": {
                    "deployment_id": {
                        "owner": "akash1...",
                        "dseq": "123"
                    },
                    "state": "active"
                },
                "escrow_account": {
                    "funds": {
                        "amount": "1000000"
                    }
                },
                "groups": [...]
            }
        """
        deployments = self.cli.get_deployments()
        if not deployments:
            return []
        return deployments.get("deployments", [])


    def needs_funding(self, deployment: Dict[str, Any], include_fees: bool = True) -> bool:
        """
        Check if deployment needs additional funding
        
        A deployment needs funding if:
        1. It is in "active" state
        2. Current balance <= min_threshold
        
        Args:
            deployment: Deployment data following the schema
            
        Returns:
            True if funding needed, False otherwise
            
        Schema validation:
            - deployment.state must be "active"
            - Balance checked from escrow_account.funds.amount
        """
        try:
            # Check if deployment is active
            if safe_get(deployment, "deployment", "state") != "active":
                return False

            # Check current balance
            escrow = deployment.get("escrow_account", {})
            balance = parse_escrow_amount(escrow)
            if balance is None:
                return False
                
            # Log the funding decision
            deployment_id = safe_get(deployment, "deployment", "deployment_id", {}) or {}
            owner = deployment_id.get("owner", "unknown")
            dseq = deployment_id.get("dseq", "unknown")
            
            # Calculate minimum required balance including transaction fees if needed
            min_required = self.min_threshold
            if include_fees:
                tx_fee = calculate_transaction_fee()
                min_required += tx_fee
                self.logger.debug(f"Including transaction fee of {tx_fee} uakt in calculation")

            # Only fund if balance is strictly below threshold
            if balance < min_required:
                self.logger.info(
                    f"Deployment {owner}/{dseq} needs funding: "
                    f"balance={balance} < required={min_required} "
                    f"(threshold={self.min_threshold} + fees={tx_fee if include_fees else 0})"
                )
                return True
                
            self.logger.debug(
                f"Deployment {owner}/{dseq} has sufficient funds: "
                f"balance={balance} >= required={min_required}"
            )
            return False

        except (KeyError, ValueError) as e:
            self.logger.error(f"Error checking funding needs: {str(e)}")
            return False

    def verify_top_up(self, deployment_id: Dict[str, str], amount: int, max_retries: int = 3, include_fees: bool = True) -> bool:
        """
        Verify a top-up transaction was successful
        
        Args:
            deployment_id: Dictionary containing:
                - owner: Deployment owner address
                - dseq: Deployment sequence number
            amount: Expected amount added in uakt
            max_retries: Maximum verification attempts
            
        Returns:
            True if verified, False otherwise
            
        Schema validation:
            - Verifies using escrow_account.funds.amount
            - Both owner and dseq are required from deployment_id
        """
        owner = deployment_id.get("owner")
        dseq = deployment_id.get("dseq")
        if not owner or not dseq:
            return False
            
        initial_balance = self.cli.get_deployment_balance(owner, dseq)
        if initial_balance is None:
            return False
            
        for _ in range(max_retries):
            if not self.cli.top_up_deployment(owner, dseq, amount):
                continue
                
            # Wait for transaction to be processed
            time.sleep(6)  # Average block time
            
            new_balance = self.cli.get_deployment_balance(owner, dseq)
            if new_balance is None:
                continue
                
            # Calculate expected balance including fees
            expected = initial_balance + amount
            if include_fees:
                tx_fee = calculate_transaction_fee()
                expected -= tx_fee  # Subtract transaction fee from expected balance
            if new_balance >= expected:
                return True
                
        return False

    def validate_amount(self, amount: int) -> bool:
        """
        Validate top-up amount meets minimum requirements
        
        Args:
            amount: Amount in uakt
            
        Returns:
            True if valid, False otherwise
        """
        min_amount = 500_000  # 0.5 AKT in uakt
        return amount >= min_amount

    def manage_balances(self) -> Dict[str, Any]:
        """
        Check and top up deployment balances as needed
        
        Returns:
            Summary of actions taken
        """
        summary = {
            "checked": 0,
            "funded": 0,
            "failed": 0,
            "total_funded": 0,
            "skipped": 0
        }

        if not self.validate_amount(self.top_up_amount):
            self.logger.error(f"Top-up amount {self.top_up_amount} below minimum 0.5 AKT")
            return summary

        deployments = self.get_active_deployments()
        summary["checked"] = len(deployments)

        for deployment in deployments:
            try:
                deployment_id = safe_get(deployment, "deployment", "deployment_id")
                if not deployment_id:
                    summary["skipped"] += 1
                    continue

                if not self.needs_funding(deployment):
                    self.logger.debug(f"Deployment {deployment_id.get('owner', 'unknown')}/{deployment_id.get('dseq', 'unknown')} has sufficient funds, skipping")
                    continue
                    
                if self.verify_top_up(deployment_id, self.top_up_amount):
                    summary["funded"] += 1
                    summary["total_funded"] += self.top_up_amount
                else:
                    summary["failed"] += 1

            except Exception as e:
                deployment_id_str = f"{deployment_id.get('owner', 'unknown')}/{deployment_id.get('dseq', 'unknown')}" if deployment_id else "unknown"
                self.logger.error(f"Error managing deployment {deployment_id_str}: {str(e)}")
                summary["failed"] += 1

        formatted_summary = self.reporter.generate_github_output(
            self.reporter.format_summary(summary)
        )
        if formatted_summary:
            print(formatted_summary)
            
        return summary
