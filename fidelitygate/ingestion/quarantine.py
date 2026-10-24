import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone


class QuarantineManager:
    """Isolates malformed, corrupted, or schema-violating records for human review."""

    def __init__(self, quarantine_dir: Path):
        self.quarantine_dir = quarantine_dir
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def get_quarantine_path(self, ingestion_id: str) -> Path:
        return self.quarantine_dir / f"{ingestion_id}_quarantine.jsonl"

    def record_quarantine(
        self,
        ingestion_id: str,
        row_index: int,
        raw_row: Any,
        category: str,
        reason: str
    ) -> None:
        target_file = self.get_quarantine_path(ingestion_id)
        entry = {
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
            "ingestion_id": ingestion_id,
            "row_index": row_index,
            "category": category,
            "reason": reason,
            "raw_payload": raw_row,
        }
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def load_quarantine(self, ingestion_id: str) -> List[Dict[str, Any]]:
        target_file = self.get_quarantine_path(ingestion_id)
        if not target_file.exists():
            return []
        records = []
        with open(target_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line.strip()))
        return records

