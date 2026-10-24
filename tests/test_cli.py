import json
import subprocess
import sys

def test_cli_list_scenarios():
    res = subprocess.run([sys.executable, "-m", "fidelitygate.cli", "list-scenarios"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "success"
    assert "wan_congestion" in data["data"]
    assert "fiber_drift" in data["data"]

def test_cli_investigate():
    res = subprocess.run([sys.executable, "-m", "fidelitygate.cli", "investigate", "wan_congestion", "10"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "success"
    assert "gate" in data
    assert "sweep_points" in data
    assert len(data["sweep_points"]) == 10
