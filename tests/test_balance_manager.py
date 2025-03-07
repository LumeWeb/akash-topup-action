import pytest
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from scripts.balance_manager import DeploymentManager
from scripts.utils import safe_get
from . import sample_deployment

@pytest.fixture
def manager():
    return DeploymentManager(
        min_threshold=1_000_000,  # 1 AKT
        top_up_amount=500_000,    # 0.5 AKT
        block_buffer=1000
    )

def test_get_active_deployments_success(manager, sample_deployment):
    mock_deployments = {
        "deployments": [
            dict(sample_deployment),
            {
                "deployment": {
                    "deployment_id": {
                        "owner": "akash1test2",
                        "dseq": "2"
                    },
                    "state": "active",
                    "version": "test_version",
                    "created_at": "12345"
                },
                "escrow_account": {
                    "id": {
                        "scope": "deployment",
                        "xid": "akash1test2/2"
                    },
                    "owner": "akash1test2",
                    "state": "open",
                    "balance": {"denom": "uakt", "amount": "0"},
                    "transferred": {"denom": "uakt", "amount": "200"},
                    "settled_at": "12346",
                    "depositor": "akash1test2",
                    "funds": {"denom": "uakt", "amount": "2000000"}
                }
            }
        ],
        "pagination": {
            "next_key": None,
            "total": "2"
        }
    }
    
    with patch.object(manager.cli, 'get_deployments') as mock_get:
        mock_get.return_value = mock_deployments
        result = manager.get_active_deployments()
        
        assert len(result) == 2
        assert safe_get(result[0], "deployment", "deployment_id", "dseq") == "1"
        assert safe_get(result[0], "escrow_account", "funds", "amount") == "2000000"

def test_calculate_burn_rate_success(manager):
    deployment = {
        "groups": [
            {
                "group_spec": {
                    "resources": [
                        {"price": {"amount": "100"}, "count": 1},
                        {"price": {"amount": "200"}, "count": 1}
                    ]
                }
            }
        ]
    }
    
    result = manager.calculate_burn_rate(deployment)
    assert result == Decimal("300")

def test_estimate_closure_success(manager):
    deployment = {
        "escrow_account": {
            "funds": {"denom": "uakt", "amount": "1000"}
        }
    }
    burn_rate = Decimal("10")
    
    result = manager.estimate_closure(deployment, burn_rate)
    assert result == 100

def test_needs_funding_low_balance(manager):
    deployment = {
        "deployment": {"state": "active"},
        "escrow_account": {
            "funds": {"denom": "uakt", "amount": "500000"}
        }
    }  # Below threshold
    
    result = manager.needs_funding(deployment)
    assert result is True

def test_needs_funding_low_blocks(manager):
    deployment = {
        "deployment": {"state": "active"},
        "escrow_account": {
            "funds": {"denom": "uakt", "amount": "2000000"}
        },
        "groups": [
            {
                "group_spec": {
                    "resources": [
                        {"price": {"amount": "2000"}, "count": 1}
                    ]
                }
            }
        ]
    }
    
    result = manager.needs_funding(deployment)
    assert result is True

def test_validate_amount_success(manager):
    assert manager.validate_amount(500_000) is True  # 0.5 AKT
    assert manager.validate_amount(1_000_000) is True  # 1.0 AKT
    assert manager.validate_amount(400_000) is False  # 0.4 AKT

def test_verify_top_up_success(manager):
    deployment_id = {
        "owner": "akash1test1",
        "dseq": "1"
    }
    with patch.object(manager.cli, 'get_deployment_balance') as mock_balance:
        mock_balance.side_effect = [1_000_000, 1_500_000]  # Initial, after top-up
        with patch.object(manager.cli, 'top_up_deployment') as mock_top_up:
            mock_top_up.return_value = True
            
            assert manager.verify_top_up(deployment_id, 500_000) is True

def test_needs_funding_closed_deployment(manager, sample_deployment):
    sample_deployment["deployment"]["state"] = "closed"
    sample_deployment["escrow_account"]["funds"]["amount"] = "500000"
    assert manager.needs_funding(sample_deployment) is False

def test_needs_funding_invalid_state(manager, sample_deployment):
    sample_deployment["deployment"]["state"] = "invalid_state"
    sample_deployment["escrow_account"]["funds"]["amount"] = "500000"
    assert manager.needs_funding(sample_deployment) is False

def test_verify_top_up_missing_owner(manager):
    deployment_id = {
        "dseq": "1"
    }
    assert manager.verify_top_up(deployment_id, 500_000) is False

def test_verify_top_up_missing_dseq(manager):
    deployment_id = {
        "owner": "akash1test1"
    }
    assert manager.verify_top_up(deployment_id, 500_000) is False

def test_verify_top_up_failure(manager):
    deployment_id = {
        "owner": "akash1test1",
        "dseq": "1"
    }
    with patch.object(manager.cli, 'get_deployment_balance') as mock_balance:
        mock_balance.side_effect = [1_000_000] * 4  # Initial + 3 retries
        with patch.object(manager.cli, 'top_up_deployment') as mock_top_up:
            mock_top_up.return_value = True
            
            assert manager.verify_top_up(deployment_id, 500_000) is False

def test_manage_balances_skips_sufficient_funds(manager, sample_deployment):
    # Create a second deployment based on the sample
    # Create modified copy of sample deployment
    second_deployment = json.loads(json.dumps(sample_deployment))  # Deep copy
    second_deployment["deployment"]["deployment_id"] = {"owner": "akash1test2", "dseq": "2"}
    second_deployment["escrow_account"]["id"]["xid"] = "akash1test2/2"
    second_deployment["escrow_account"]["owner"] = "akash1test2"
    second_deployment["escrow_account"]["depositor"] = "akash1test2"
    second_deployment["escrow_account"]["funds"]["amount"] = "500000"  # Below threshold
    
    # Create deployment with funds well above threshold
    sample_deployment["escrow_account"]["funds"]["amount"] = "5000000"  # 5 AKT
    
    deployments = {
        "deployments": [sample_deployment],
        "pagination": {"next_key": None, "total": "1"}
    }
    
    with patch.object(manager.cli, 'get_deployments') as mock_get:
        mock_get.return_value = deployments
        with patch.object(manager, 'verify_top_up') as mock_verify:
            # verify_top_up should never be called
            mock_verify.assert_not_called()
            
            result = manager.manage_balances()
            
            assert result["checked"] == 1
            assert result["funded"] == 0  # Should not fund
            assert result["failed"] == 0
            assert result["skipped"] == 0

def test_manage_balances_invalid_amount(manager):
    manager.top_up_amount = 400_000  # Below minimum
    
    result = manager.manage_balances()
    
    assert result["checked"] == 0
    assert result["funded"] == 0
