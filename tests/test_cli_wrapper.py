import pytest
from unittest.mock import patch, MagicMock
from scripts.cli_wrapper import AkashCLI

@pytest.fixture
def cli():
    return AkashCLI()

def test_run_command_success(cli):
    with patch('subprocess.Popen') as mock_popen:
        process_mock = MagicMock()
        process_mock.communicate.return_value = ('success', '')
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        
        code, stdout, stderr = cli._run_command(['test', 'command'])
        assert code == 0
        assert stdout == 'success'
        assert stderr == ''

def test_get_deployments_success(cli):
    with patch.object(cli, '_run_command') as mock_run:
        mock_run.return_value = (0, '{"deployments": []}', '')
        result = cli.get_deployments()
        assert result == {"deployments": []}

def test_get_deployment_balance_success(cli):
    with patch.object(cli, '_run_command') as mock_run:
        mock_run.return_value = (0, '{"escrow_account": {"funds": {"denom": "uakt", "amount": "1000"}}}', '')
        result = cli.get_deployment_balance("akash1test1", "1")
        assert result == 1000

def test_top_up_deployment_success(cli):
    with patch.dict('os.environ', {'AKASH_ACCOUNT_ADDRESS': 'akash1test1'}):
        with patch.object(cli, '_run_command') as mock_run:
            mock_run.return_value = (0, 'success', '')
            result = cli.top_up_deployment("akash1test1", "1", 1000)
            assert result is True
