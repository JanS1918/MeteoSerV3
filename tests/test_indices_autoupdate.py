import json
from pathlib import Path

from core.indices import registry


def test_registry_status_written(tmp_path):
    # Force update writing to workspace data
    status_file = Path("data") / "indices_registry_status.json"
    # Ensure removal first
    try:
        if status_file.exists():
            status_file.unlink()
    except Exception:
        pass
    registry.update_registry_and_write_status()
    assert status_file.exists(), "Status file should be created"
    content = json.loads(status_file.read_text(encoding="utf-8"))
    assert "timestamp" in content
    assert "registered" in content
