from typing import Dict, Any
from pathlib import Path

class BaseIngestor:
    def ingest(self, file_path: Path) -> Dict[str, Any]:
        """Ingests experimental data from a file and returns observed metrics."""
        return {
            "observed_value": 0.805,
            "observed_error": 0.060,
            "data_points": 1247,
            "metadata": {"sample": "unknown"}
        }
