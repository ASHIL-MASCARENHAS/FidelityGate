# Antigravity handoff prompt

Inspect the full repository before editing. Run the tests first and identify missing original modules/data.

Improve the Streamlit UI into a polished, dark engineering control room: restrained navy surfaces, cyan highlights, amber for GATHER_EVIDENCE, red for ABSTAIN, strong typography, responsive layouts. Keep the Decision Workspace, Run History, Evaluation Lab, and Settings & Diagnostics as distinct screens.

Use real outputs from `orchestrator.py`; do not hardcode a successful result. Keep the `DEMO DATA — NOT LIVE INFRASTRUCTURE` disclosure visible until real telemetry is connected. Do not invent benchmark findings. Preserve deterministic gate semantics and add tests for behavior changes. Keep the app offline-capable; do not add external services or LLM calls unless asked. Run `python -m pytest -q` and report issues. The included network model and fixtures are illustrative, not operationally validated.
