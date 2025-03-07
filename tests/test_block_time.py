import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from scripts.calculate_block_time import BlockTimeCalculator

@pytest.fixture
def calculator():
    return BlockTimeCalculator(sample_size=3)

def test_get_block_times_success(calculator):
    def mock_run_command(cmd):
        if len(cmd) == 5:  # Initial current block query
            return (0, '{"block":{"header":{"height":"100"}}}', '')
        elif len(cmd) == 6:  # Block height queries
            height = cmd[3]
            responses = {
                "98": '{"block":{"header":{"height":"98","time":"2023-01-01T00:00:00Z"}}}',
                "99": '{"block":{"header":{"height":"99","time":"2023-01-01T00:00:06Z"}}}',
                "100": '{"block":{"header":{"height":"100","time":"2023-01-01T00:00:12Z"}}}'
            }
            return (0, responses.get(height, "{}"), '')
        return (1, "", "Invalid command")
    
    with patch.object(calculator.cli, '_run_command') as mock_run:
        mock_run.side_effect = mock_run_command
        result = calculator._get_block_times()
        
        assert result is not None
        assert len(result) == 3
        assert result[0][0] == 98
        assert result[-1][0] == 100

def test_calculate_average_time_success(calculator):
    times = [
        (98, datetime(2023, 1, 1, 0, 0, 0)),
        (99, datetime(2023, 1, 1, 0, 0, 6)),
        (100, datetime(2023, 1, 1, 0, 0, 12))
    ]
    
    with patch.object(calculator, '_get_block_times') as mock_get:
        mock_get.return_value = times
        result = calculator.calculate_average_time()
        
        assert result == 6.0  # 6 seconds between blocks

def test_calculate_average_time_with_outlier(calculator):
    times = [
        (98, datetime(2023, 1, 1, 0, 0, 0)),
        (99, datetime(2023, 1, 1, 0, 0, 6)),
        (100, datetime(2023, 1, 1, 0, 1, 0))  # Outlier: 54 second gap
    ]
    
    with patch.object(calculator, '_get_block_times') as mock_get:
        mock_get.return_value = times
        result = calculator.calculate_average_time()
        assert result == 6.0  # Should use median to ignore outlier

def test_calculate_average_time_with_custom_max_time():
    calculator = BlockTimeCalculator(sample_size=3, max_block_time=60)
    times = [
        (98, datetime(2023, 1, 1, 0, 0, 0)),
        (99, datetime(2023, 1, 1, 0, 0, 40)),  # 40s gap would be filtered with default
        (100, datetime(2023, 1, 1, 0, 1, 20))
    ]
    
    with patch.object(calculator, '_get_block_times') as mock_get:
        mock_get.return_value = times
        result = calculator.calculate_average_time()
        assert result == 40.0  # Should accept 40s gap with max_block_time=60

def test_calculate_average_time_failure(calculator):
    with patch.object(calculator, '_get_block_times') as mock_get:
        mock_get.return_value = None
        result = calculator.calculate_average_time()
        
        assert result is None
