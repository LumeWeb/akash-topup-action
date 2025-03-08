import json
import logging
import os
from typing import Optional, Dict, List, Any
from .cli_base import AkashCLIBase
from .utils import parse_escrow_amount

class AkashCLI(AkashCLIBase):
    """Wrapper for Akash CLI commands"""

    def __init__(self):
        super().__init__()

    def get_account_balance(self, account: str = None) -> Optional[int]:
        """
        Get balance for an account
        
        Args:
            account: Account address (uses AKASH_ACCOUNT_ADDRESS if None)
            
        Returns:
            Balance in uakt or None if error
        """
        account = account or os.environ.get("AKASH_ACCOUNT_ADDRESS")
        if not account:
            return None
            
        cmd = [
            "query", "bank", "balances",
            account,
            "--denom", "uakt",
            "--output", "json"
        ]
        code, stdout, stderr = self._run_command(cmd)
        
        if code != 0:
            self.logger.error(f"Failed to get account balance: {stderr}")
            return None
            
        try:
            data = json.loads(stdout)
            balances = data.get("balances", [])
            for balance in balances:
                if balance.get("denom") == "uakt":
                    return int(balance.get("amount", "0"))
            return 0
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse account balance: {str(e)}")
            return None

    def get_deployments(self) -> Optional[Dict[str, Any]]:
        """
        Get list of all active deployments for the current account
        
        Returns:
            Dictionary containing deployments or None if error
        """
        cmd = [
            "provider-services", "query", "deployment", "list",
            "--state", "active",
            "--owner", os.environ.get("AKASH_ACCOUNT_ADDRESS", ""),
            "--output", "json"
        ]
        code, stdout, stderr = self._run_command(cmd)
        
        if code != 0:
            self.logger.error(f"Failed to get deployments: {stderr}")
            return None
            
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse deployment JSON: {str(e)}")
            return None

    def get_deployment_balance(self, owner: str, dseq: str) -> Optional[int]:
        """
        Get balance for a specific deployment
        
        Args:
            owner: Deployment owner address
            dseq: Deployment sequence number
            
        Returns:
            Balance in uakt or None if error
        """
        cmd = [
            "provider-services", "query", "deployment", "get",
            "--owner", owner,
            "--dseq", dseq,
            "--output", "json"
        ]
        code, stdout, stderr = self._run_command(cmd)
        
        if code != 0:
            self.logger.error(f"Failed to get deployment {dseq} balance: {stderr}")
            return None
            
        try:
            data = json.loads(stdout)
            escrow = data.get("escrow_account", {})
            return parse_escrow_amount(escrow)
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse balance for deployment {dseq}: {str(e)}")
            return None

    def top_up_deployment(self, owner: str, dseq: str, amount: int) -> bool:
        """
        Add funds to a deployment
        
        Args:
            owner: Deployment owner address
            dseq: Deployment sequence number
            amount: Amount to add in uakt
            
        Returns:
            True if successful, False otherwise
        """
        account = os.environ.get("AKASH_ACCOUNT_ADDRESS")
        if not account:
            self.logger.error("AKASH_ACCOUNT_ADDRESS not set")
            return False
            
        cmd = [
            "provider-services", "tx", "deployment", "deposit",
            f"{amount}uakt",  # Add denomination to amount
            "--owner", owner,
            "--dseq", dseq,
            "--from", account,
            "--yes",  # Auto-confirm
            "--gas", os.environ.get('AKASH_GAS', 'auto'),
            "--gas-adjustment", os.environ.get('AKASH_GAS_ADJUSTMENT', '1.75'),
            "--gas-prices", os.environ.get('AKASH_GAS_PRICES', '0.025uakt')
        ]
        code, stdout, stderr = self._run_command(cmd)
        
        if code != 0:
            self.logger.error(f"Failed to top up deployment {dseq}: {stderr}")
            return False
            
        return True
