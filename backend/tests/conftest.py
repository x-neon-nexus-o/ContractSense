"""Configure isolated, deterministic settings before importing the FastAPI app."""
import os
import tempfile

_TEST_DATA = tempfile.mkdtemp(prefix="contractsense-tests-")
os.environ["DATA_DIR"] = _TEST_DATA
os.environ["DB_BACKEND"] = "sqlite"
os.environ["ENABLE_CHROMA"] = "false"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["SECRET_KEY"] = "test-only-secret-key-not-for-production"
os.environ["MAX_UPLOAD_MB"] = "2"
os.environ["CORS_ORIGINS"] = ""
