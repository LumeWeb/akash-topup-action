import json
import logging
import statistics
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Any

from .cli_base import AkashCLIBase

class BlockTimeCalculator(AkashCLIBase):
    """Calculate average block time from recent blocks"""
    
    def __init__(self, sample_size: int = 100, cli: Optional[Any] = None, max_block_time: int = 30):
        """
        Initialize calculator
        
        Args:
            sample_size: Number of recent blocks to analyze
            cli: Optional CLI instance, will create if not provided
            max_block_time: Maximum reasonable block time in seconds
        """
        super().__init__()
        self.sample_size = sample_size
        self._cli = cli
        self.max_block_time = max_block_time
        
    @property
    def cli(self):
        """Lazy load CLI instance to avoid circular imports"""
        if self._cli is None:
            from .cli_wrapper import AkashCLI
            self._cli = AkashCLI()
        return self._cli

    def _get_block_times(self) -> Optional[List[Tuple[int, datetime]]]:
        """
        Get block heights and timestamps for recent blocks
        
        Returns:
            List of (height, timestamp) tuples or None if error
        """
        cmd = ["provider-services", "query", "block", "--output", "json"]
        code, stdout, stderr = self.cli._run_command(cmd)
        
        if code != 0:
            self.logger.error(f"Failed to get current block: {stderr}")
            return None
            
        try:
            current_block = json.loads(stdout)
            current_height = int(current_block["block"]["header"]["height"])
                
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def get_block(height: int) -> Optional[Tuple[int, datetime]]:
                cmd = ["provider-services", "query", "block", str(height), "--output", "json"]
                code, stdout, stderr = self.cli._run_command(cmd)
                if code != 0:
                    return None
                try:
                    block_data = json.loads(stdout)
                    # Parse ISO timestamp and ensure UTC timezone
                    timestamp = datetime.fromisoformat(
                        block_data["block"]["header"]["time"].replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
                    return (height, timestamp)
                except (json.JSONDecodeError, KeyError, ValueError):
                    return None

            block_times = []
            heights = list(range(current_height - self.sample_size, current_height + 1))
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_height = {executor.submit(get_block, h): h for h in heights}
                for future in as_completed(future_to_height):
                    result = future.result()
                    if result:
                        block_times.append(result)
            
            # Sort by height and return None if empty
            if not block_times:
                return None
            block_times.sort(key=lambda x: x[0])  # Sort by height before returning
            return block_times
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse block  {str(e)}")
            return None
    
    def calculate_average_time(self) -> Optional[float]:
        """
        Calculate average time between blocks in seconds
        
        Returns:
            Average block time in seconds or None if error
        """
        block_times = self._get_block_times()
        if not block_times or len(block_times) < 2:
            return None
            
        # Sort by height to ensure correct order
        block_times.sort(key=lambda x: x[0])
        
        # Calculate time differences between consecutive blocks
        time_diffs = []
        for i in range(1, len(block_times)):
            diff = (block_times[i][1] - block_times[i-1][1]).total_seconds()
            if 0 < diff < self.max_block_time:  # Filter out unreasonable values
                time_diffs.append(diff)
                
        if not time_diffs:
            return None
            
        # Use median to avoid outliers
        return statistics.median(time_diffs)
