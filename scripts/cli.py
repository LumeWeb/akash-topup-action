#!/usr/bin/env python3

import argparse
from argparse import ArgumentTypeError
import logging
import sys
from decimal import Decimal, DecimalException

from .balance_manager import DeploymentManager
from .utils import setup_logging, akt_to_uakt

def validate_akt_amount(value: str) -> Decimal:
    """
    Validate and convert AKT amount string to Decimal
    
    Args:
        value: Amount string in AKT
        
    Returns:
        Decimal amount
        
    Raises:
        ArgumentTypeError: If value is invalid
    """
    try:
        amount = Decimal(value)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return amount
    except (DecimalException, ValueError) as e:
        raise ArgumentTypeError(f"'{value}' is not a valid AKT amount: {str(e)}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Manage Akash deployment balances"
    )
    
    parser.add_argument(
        "--min-balance",
        type=validate_akt_amount,
        default="1.0",
        help="Minimum balance threshold in AKT (default: 1.0)"
    )
    
    parser.add_argument(
        "--top-up",
        type=validate_akt_amount,
        default="0.5",
        help="Amount to top up in AKT (default: 0.5, minimum: 0.5)"
    )
    
    parser.add_argument(
        "--block-buffer",
        type=int,
        default=1000,
        help="Safety margin in blocks before estimated closure (default: 1000)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Setup logging
    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)
    
    # Convert AKT amounts to uakt
    min_balance = akt_to_uakt(Decimal(str(args.min_balance)))
    top_up = akt_to_uakt(Decimal(str(args.top_up)))
    
    # Create and run manager
    manager = DeploymentManager(
        min_threshold=min_balance,
        top_up_amount=top_up,
        block_buffer=args.block_buffer
    )
    
    try:
        summary = manager.manage_balances()
        sys.exit(0 if summary["failed"] == 0 else 1)
    except Exception as e:
        logging.error(f"Failed to manage balances: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
