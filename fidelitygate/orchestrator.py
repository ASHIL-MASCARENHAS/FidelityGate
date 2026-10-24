from .decision_gate import decide
from .scenarios import DEMO_SCENARIOS
from .storage import RunStore
from .uncertainty import run_sweep


def investigate(scenario_key: str, database_path="fidelitygate.db", evaluations=25):
    if scenario_key not in DEMO_SCENARIOS:
        raise ValueError(f"Unknown demo scenario: {scenario_key}")
    scenario = DEMO_SCENARIOS[scenario_key]
    gate = decide(scenario, run_sweep(scenario, evaluations))
    run_id = RunStore(database_path).save(scenario, gate)
    return scenario, gate, run_id
