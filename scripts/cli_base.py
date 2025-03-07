import subprocess
import json
import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

class AkashCLIBase:
    """Base class for Akash CLI operations"""
    
    def __init__(self):
        """Initialize base CLI handler"""
        self.logger = logging.getLogger(__name__)

    def _run_command(self, command: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """
        Execute a CLI command and return its output
        
        Args:
            command: List of command parts to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd_str = ' '.join(command)
        self.logger.debug(f"Executing command: {cmd_str}")
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return process.returncode, stdout.strip(), stderr.strip()
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.error(f"Command timed out after {timeout}s: {cmd_str}")
                return 1, "", f"Command timed out after {timeout}s"
                
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute command {cmd_str}: {str(e)}")
            return 1, "", str(e)
        except Exception as e:
            self.logger.error(f"Unexpected error executing {cmd_str}: {str(e)}")
            return 1, "", str(e)

