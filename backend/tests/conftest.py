import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-1234")
_test_dir = Path(tempfile.mkdtemp())
(_test_dir / "test.db").touch()
os.environ["DATABASE_URL"] = f"sqlite:///{_test_dir / 'test.db'}"
os.environ["JOBS_DATABASE_URL"] = f"sqlite:///{_test_dir / 'jobs.db'}"
os.environ["JOB_INGEST_ENABLED"] = "false"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
