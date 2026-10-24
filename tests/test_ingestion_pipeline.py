import hashlib
import json
import os
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from fidelitygate.api.app import app
from fidelitygate.config import settings
from fidelitygate.ingestion.cisco_adapter import CiscoTelemetryAdapter
from fidelitygate.ingestion.models import (
    DataMode,
    DataQualityIssue,
    DatasetSourceManifest,
    IngestionReport,
    IngestionRequest,
    NormalizedObservation,
)
from fidelitygate.ingestion.pipeline import IngestionPipeline, IngestionSecurityError
from fidelitygate.storage import StorageEngine

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def test_storage(tmp_path):
    db_file = tmp_path / "test_fidelitygate.db"
    return StorageEngine(str(db_file))


@pytest.fixture
def test_pipeline(test_storage, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "DATABASE_PATH", str(tmp_path / "test_fidelitygate.db"))
    return IngestionPipeline(test_storage)


@pytest.fixture
def api_client(test_storage, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "DATABASE_PATH", str(tmp_path / "test_fidelitygate.db"))
    return TestClient(app)


# 1. Successful ingestion of a valid documented CSV
def test_01_successful_ingestion_valid_csv(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_valid.csv",
        dataset_version="v1.0-test",
    )
    report = test_pipeline.run_ingestion(req)
    assert report.status in ["SUCCESS", "PARTIAL_SUCCESS"]
    assert report.source_row_count == 3
    assert report.accepted_count > 0
    assert report.source_checksum != "NONE"
    assert len(report.output_artifacts) >= 2


# 2. Invalid or missing required columns
def test_02_invalid_or_missing_required_columns(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_missing_columns.csv",
    )
    report = test_pipeline.run_ingestion(req)
    assert report.status == "FAILED"
    assert report.accepted_count == 0
    missing_issues = [i for i in report.quality_issues if i.category == "MISSING_REQUIRED_COLUMN"]
    assert len(missing_issues) > 0
    assert missing_issues[0].severity == "CRITICAL"


# 3. Malformed numeric values
def test_03_malformed_numeric_values(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_malformed.csv",
    )
    report = test_pipeline.run_ingestion(req)
    num_issues = [i for i in report.quality_issues if i.category == "NUMERIC_PARSING_FAILURE"]
    assert len(num_issues) > 0
    assert num_issues[0].disposition == "QUARANTINED"
    assert report.quarantined_count > 0


# 4. Missing or invalid timestamps
def test_04_missing_or_invalid_timestamps(test_pipeline):
    adapter = CiscoTelemetryAdapter()
    iso, err = adapter.parse_timestamp_nanos("INVALID_CHARS")
    assert iso is None
    assert "Unparseable" in err

    iso_empty, err_empty = adapter.parse_timestamp_nanos("")
    assert iso_empty is None
    assert "Empty" in err_empty

    iso_valid, err_valid = adapter.parse_timestamp_nanos("1503019768316000000")
    assert iso_valid is not None
    assert err_valid is None
    assert iso_valid.startswith("2017-08-18")


# 5. Duplicate record detection
def test_05_duplicate_record_detection(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_duplicates.csv",
    )
    report = test_pipeline.run_ingestion(req)
    assert report.duplicate_count >= 1
    dup_issues = [i for i in report.quality_issues if i.category == "DUPLICATE_RECORD"]
    assert len(dup_issues) >= 1


# 6. Unknown units remaining explicitly unknown (None)
def test_06_unknown_units_remain_explicitly_unknown(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_valid.csv",
    )
    report = test_pipeline.run_ingestion(req)
    processed_path = Path(report.output_artifacts["processed_observations"])
    assert processed_path.exists()

    with open(processed_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    # Verify documented units exist
    bytes_records = [r for r in records if r["metric_name"] == "bytes-received"]
    assert len(bytes_records) > 0
    assert bytes_records[0]["unit"] == "bytes"

    # Verify unlisted/undocumented metrics do NOT invent units
    drops_records = [r for r in records if r["metric_name"] == "input-drops"]
    for r in drops_records:
        assert r["unit"] is None, f"Expected None for input-drops, got {r['unit']}"


# 7. Preservation of source row/file provenance
def test_07_preservation_of_source_row_file_provenance(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_valid.csv",
    )
    report = test_pipeline.run_ingestion(req)
    processed_path = Path(report.output_artifacts["processed_observations"])

    with open(processed_path, "r", encoding="utf-8") as f:
        first_line = json.loads(f.readline())

    prov = first_line["provenance"]
    assert prov["source_file"] == "cisco_sample_valid.csv"
    assert prov["source_row_index"] == 2
    assert prov["source_checksum"] == report.source_checksum
    assert prov["ingestion_id"] == report.ingestion_id


# 8. Correct source checksum generation
def test_08_correct_source_checksum_generation(test_pipeline):
    target = FIXTURES_DIR / "cisco_sample_valid.csv"
    hasher = hashlib.sha256()
    with open(target, "rb") as f:
        hasher.update(f.read())
    expected = hasher.hexdigest()

    computed = test_pipeline.compute_sha256(target)
    assert computed == expected


# 9. Ingestion idempotency
def test_09_ingestion_idempotency(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_valid.csv",
        dataset_version="v1.0",
        force_reingest=False,
    )
    report1 = test_pipeline.run_ingestion(req)
    report2 = test_pipeline.run_ingestion(req)

    # Identical run ID should be returned from cache
    assert report1.ingestion_id == report2.ingestion_id
    assert report1.source_checksum == report2.source_checksum


# 10. Unsafe file path rejection
def test_10_unsafe_file_path_rejection(test_pipeline):
    req1 = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="../../../etc/passwd",
    )
    report1 = test_pipeline.run_ingestion(req1)
    assert report1.status == "FAILED"
    assert any(i.category == "UNSAFE_PATH" for i in report1.quality_issues)

    req2 = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="/var/log/system.log",
    )
    report2 = test_pipeline.run_ingestion(req2)
    assert report2.status == "FAILED"
    assert any(i.category == "UNSAFE_PATH" for i in report2.quality_issues)


# 11. Empty or truncated input files
def test_11_empty_or_truncated_input_files(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_empty.csv",
    )
    report = test_pipeline.run_ingestion(req)
    assert report.status == "FAILED"
    assert report.source_row_count == 0
    assert any(i.category == "EMPTY_FILE" for i in report.quality_issues)


# 12. Partial data-quality failures and report generation
def test_12_partial_data_quality_failures_and_quarantine(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_malformed.csv",
    )
    report = test_pipeline.run_ingestion(req)
    # File has 1 bad row and 1 valid row -> PARTIAL_SUCCESS
    assert report.status == "PARTIAL_SUCCESS"
    assert report.accepted_count > 0
    assert report.quarantined_count > 0

    # Verify quarantine store contains the malformed payload
    quarantined = test_pipeline.quarantine_manager.load_quarantine(report.ingestion_id)
    assert len(quarantined) > 0
    assert quarantined[0]["category"] == "NUMERIC_PARSING_FAILURE"


# 13. Explicit distinction between public observations and synthetic fixtures
def test_13_explicit_distinction_public_observations_vs_synthetic(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_valid.csv",
    )
    report = test_pipeline.run_ingestion(req)
    processed_path = Path(report.output_artifacts["processed_observations"])

    with open(processed_path, "r", encoding="utf-8") as f:
        record = json.loads(f.readline())

    assert record["data_mode"] == DataMode.PUBLIC_DATA.value
    assert record["data_mode"] != DataMode.SYNTHETIC_FIXTURE.value


# 14. Reference/evaluator data not being exposed by the ingestion adapter
def test_14_reference_evaluator_data_not_exposed(test_pipeline):
    req = IngestionRequest(
        source_id="cisco-ie-telemetry",
        relative_path="tests/fixtures/cisco_sample_valid.csv",
    )
    report = test_pipeline.run_ingestion(req)
    processed_path = Path(report.output_artifacts["processed_observations"])

    with open(processed_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    for r in records:
        assert r.get("measurement_uncertainty") is None
        assert "hidden_reference" not in r
        assert "ground_truth_post_action" not in r


# 15. API response contract validation
def test_15_api_response_contract_validation(api_client):
    # Health endpoint check
    health_res = api_client.get("/api/v1/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] in ["healthy", "degraded"]
    assert "database" in health_data

    # Sources endpoint check
    sources_res = api_client.get("/api/v1/sources")
    assert sources_res.status_code == 200
    sources_data = sources_res.json()
    assert isinstance(sources_data, list)
    assert len(sources_data) >= 1
    assert "source_id" in sources_data[0]

    # Ingestion endpoint check
    ingest_payload = {
        "source_id": "cisco-ie-telemetry",
        "relative_path": "tests/fixtures/cisco_sample_valid.csv",
        "dataset_version": "v1.0-api",
        "force_reingest": True,
    }
    ingest_res = api_client.post("/api/v1/ingestions", json=ingest_payload)
    assert ingest_res.status_code in [201, 200]
    ingest_data = ingest_res.json()
    assert "ingestion_id" in ingest_data
    assert ingest_data["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]

    # Query report
    ing_id = ingest_data["ingestion_id"]
    report_res = api_client.get(f"/api/v1/ingestions/{ing_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["ingestion_id"] == ing_id
    assert "quality_issues" in report_data


# 16. No fabricated success response when an import fails
def test_16_no_fabricated_success_when_import_fails(api_client):
    invalid_payload = {
        "source_id": "cisco-ie-telemetry",
        "relative_path": "tests/fixtures/cisco_sample_missing_columns.csv",
        "dataset_version": "v1.0-fail",
        "force_reingest": True,
    }
    res = api_client.post("/api/v1/ingestions", json=invalid_payload)
    assert res.status_code == 400
    data = res.json()
    assert data["status"] == "FAILED"
    assert data["accepted_count"] == 0
    assert len(data["quality_issues"]) > 0

