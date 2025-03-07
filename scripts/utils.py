import logging
import sys
from typing import Any, Optional, Dict
from decimal import Decimal, DecimalException

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the application
    
    Args:
        level: Logging level to use
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def uakt_to_akt(uakt: int) -> Decimal:
    """
    Convert microAKT to AKT
    
    Args:
        uakt: Amount in microAKT
        
    Returns:
        Amount in AKT as Decimal
    """
    return (Decimal(uakt) / Decimal(1_000_000)).quantize(Decimal('0.1'))

def akt_to_uakt(akt: Decimal) -> int:
    """
    Convert AKT to microAKT
    
    Args:
        akt: Amount in AKT
        
    Returns:
        Amount in microAKT as integer
    """
    return int(akt * Decimal(1_000_000))

def parse_escrow_amount(escrow_: Dict[str, Any]) -> Optional[int]:
    """
    Safely parse escrow amount from API response
    
    Args:
        escrow_ Raw escrow account data
        
    Returns:
        Amount in uakt as integer or None if invalid
    """
    try:
        funds = escrow_.get("funds", {})
        if not funds:
            return None
            
        denom = funds.get("denom")
        if denom is None or denom != "uakt":
            raise ValueError(f"Unexpected denomination: {denom}")
            
        amount = funds.get("amount")
        if amount is None:
            return None
            
        # Handle potential scientific notation
        return int(Decimal(amount))
    except (TypeError, ValueError, DecimalException) as e:
        logging.error(f"Failed to parse escrow amount: {str(e)}")
        return None

def safe_get(obj: dict, *keys: str, default: Any = None) -> Optional[Any]:
    """
    Safely get nested dictionary values
    
    Args:
        obj: Dictionary to traverse
        *keys: Keys to traverse
        default: Default value if path not found
        
    Returns:
        Value at path or default if not found
    """
    try:
        for key in keys:
            obj = obj[key]
        return obj
    except (KeyError, TypeError):
        return default
