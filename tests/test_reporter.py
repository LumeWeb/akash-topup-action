import pytest
import json
from datetime import datetime
from unittest.mock import patch
from scripts.reporter import ActionReporter

@pytest.fixture
def reporter():
    return ActionReporter()

def test_format_summary_success(reporter):
    summary = {
        "checked": 2,
        "funded": 1,
        "failed": 0,
        "skipped": 0,
        "total_funded": 1_000_000
    }
    
    result = reporter.format_summary(summary)
    
    assert result["deployments"]["checked"] == 2
    assert result["deployments"]["funded"] == 1
    assert result["funding"]["total_funded_uakt"] == 1_000_000
    assert result["funding"]["total_funded_akt"] == "1.0"
    assert "timestamp" in result

def test_generate_github_output_success(reporter, tmp_path):
    summary = {
        "deployments": {
            "checked": 2,
            "funded": 1,
            "failed": 0,
            "skipped": 0
        },
        "funding": {
            "total_funded_uakt": 1_000_000,
            "total_funded_akt": "1.0"
        }
    }
    
    output_file = tmp_path / "github_output"
    with patch.dict('os.environ', {'GITHUB_OUTPUT': str(output_file)}):
        result = reporter.generate_github_output(summary)
        assert result is None
        
        with open(output_file) as f:
            content = f.read()
            assert f"summary={json.dumps(summary)}" in content
            assert "deployments_checked=2" in content
            assert "total_funded_akt=1.0" in content
