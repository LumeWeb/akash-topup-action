import os
import pytest
from decimal import Decimal
from pytest_mock import MockerFixture
from scripts.utils import calculate_transaction_fee, get_gas_config
from scripts.balance_manager import DeploymentManager

@pytest.fixture
def setup_env_vars():
    """Setup test environment variables"""
    os.environ['AKASH_GAS_PRICES'] = '0.025uakt'
    os.environ['AKASH_GAS'] = 'auto'
    os.environ['AKASH_GAS_ADJUSTMENT'] = '1.75'
    yield
    # Clean up
    del os.environ['AKASH_GAS_PRICES']
    del os.environ['AKASH_GAS']
    del os.environ['AKASH_GAS_ADJUSTMENT']

def test_get_gas_config(setup_env_vars):
    """Test getting gas configuration from environment"""
    gas_prices, gas, gas_adjustment = get_gas_config()
    assert gas_prices == '0.025uakt'
    assert gas == 'auto'
    assert gas_adjustment == '1.75'

def test_calculate_transaction_fee(setup_env_vars):
    """Test transaction fee calculation"""
    # For gas_limit=200000, price=0.025uakt, adjustment=1.75
    # Fee should be: 200000 * 0.025 * 1.75 = 8750 uakt
    fee = calculate_transaction_fee(gas_limit=200000)
    assert fee == 8750

def test_needs_funding_with_fees(setup_env_vars):
    """Test needs_funding including transaction fees"""
    manager = DeploymentManager(min_threshold=10000, top_up_amount=5000)
    
    # Mock deployment with balance just above min_threshold
    deployment = {
        "deployment": {"state": "active"},
        "escrow_account": {
            "funds": {
                "denom": "uakt",
                "amount": "15000"
            }
        }
    }
    
    # Should need funding because balance < (min_threshold + tx_fee)
    assert manager.needs_funding(deployment, include_fees=True)
    
    # Should not need funding when fees are excluded
    assert not manager.needs_funding(deployment, include_fees=False)

def test_verify_top_up_with_fees(setup_env_vars, mocker: MockerFixture):
    """Test verify_top_up accounting for transaction fees"""
    manager = DeploymentManager(min_threshold=10000, top_up_amount=5000)
    
    # Mock CLI responses
    mock_cli = mocker.patch.object(manager, 'cli')
    mock_cli.get_deployment_balance.side_effect = [10000, 14250]  # Initial, After
    mock_cli.top_up_deployment.return_value = True
    
    deployment_id = {"owner": "test_owner", "dseq": "1234"}
    
    # Should verify successfully when new balance accounts for fees
    # 10000 + 5000 - 750 (fee) = 14250
    assert manager.verify_top_up(deployment_id, 5000, include_fees=True)
    
    # Reset mock
    mock_cli.get_deployment_balance.side_effect = [10000, 14250]
    
    # Should fail verification when fees aren't accounted for
    assert not manager.verify_top_up(deployment_id, 5000, include_fees=False)
