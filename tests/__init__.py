"""Test suite for Akash deployment balance management"""

import pytest
from typing import Dict, Any

@pytest.fixture
def sample_deployment() -> Dict[str, Any]:
    """Fixture providing a sample deployment with standard test data"""
    return {
        "deployment": {
            "deployment_id": {
                "owner": "akash1test1",
                "dseq": "1"
            },
            "state": "active",
            "version": "test_version",
            "created_at": "12345"
        },
        "escrow_account": {
            "id": {
                "scope": "deployment",
                "xid": "akash1test1/1"
            },
            "owner": "akash1test1",
            "state": "open",
            "balance": {"denom": "uakt", "amount": "0"},
            "transferred": {"denom": "uakt", "amount": "100"},
            "settled_at": "12346",
            "depositor": "akash1test1",
            "funds": {"denom": "uakt", "amount": "2000000"}  # Well above threshold (2x min threshold)
        }
    }
