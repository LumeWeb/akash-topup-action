import json
import logging
import os
from typing import Optional, Dict, List, Any
from .cli_base import AkashCLIBase
from .utils import parse_escrow_amount

class AkashCLI(AkashCLIBase):
    """Wrapper for Akash CLI commands"""
    _cache_duration = 300  # Cache block time for 5 minutes

    def __init__(self):
        super().__init__()
        from .calculate_block_time import BlockTimeCalculator
        self.block_calculator = BlockTimeCalculator()
        self._block_time_cache = None
        self._cache_time = None

    def get_average_block_time(self) -> Optional[float]:
        """
        Get average block time with caching
        
        Returns:
            Average block time in seconds or None if error
        """
        from time import time
        now = time()
        
        if (self._block_time_cache is None or 
            self._cache_time is None or
            now - self._cache_time > self._cache_duration):
            self._block_time_cache = self.block_calculator.calculate_average_time()
            self._cache_time = now
            
        return self._block_time_cache

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
        cmd = [
            "provider-services", "tx", "deployment", "deposit",
            str(amount),
            "--owner", owner,
            "--dseq", dseq,
            "--yes"  # Auto-confirm
        ]
        code, stdout, stderr = self._run_command(cmd)
        
        if code != 0:
            self.logger.error(f"Failed to top up deployment {dseq}: {stderr}")
            return False
            
        return True
