import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from decimal import Decimal

from .utils import uakt_to_akt

class ActionReporter:
    """Handles reporting of balance management actions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def format_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format summary data for output
        
        Args:
            summary: Raw summary data
            
        Returns:
            Formatted summary
        """
        try:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "deployments": {
                    "checked": summary.get("checked", 0),
                    "funded": summary.get("funded", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0)
                },
                "funding": {
                    "total_funded_uakt": summary.get("total_funded", 0),
                    "total_funded_akt": str(uakt_to_akt(summary.get("total_funded", 0)))
                }
            }
        except Exception as e:
            self.logger.error(f"Error formatting summary: {str(e)}")
            return {}
            
    def generate_github_output(self, summary: Dict[str, Any]) -> Optional[str]:
        """
        Generate GitHub Actions output format using environment file
        
        Args:
            summary: Formatted summary data
            
        Returns:
            Output string or None if error
        """
        try:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"summary={json.dumps(summary)}\n")
                f.write(f"deployments_checked={summary['deployments']['checked']}\n")
                f.write(f"deployments_funded={summary['deployments']['funded']}\n") 
                f.write(f"total_funded_akt={summary['funding']['total_funded_akt']}\n")
            return None
        except Exception as e:
            self.logger.error(f"Error generating GitHub output: {str(e)}")
            return None
