"""Reuse server fixtures without putting mobile-only tests into the web service."""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# These overrides precede app import: never connect this suite to the user's DB/services.
os.environ.update(DATABASE_URL="sqlite://", DEBUG="false", USE_S3="false",
                  OPENAI_API_KEY="", FISH_AUDIO_API_KEY="", ELEVENLABS_API_KEY="",
                  INVESTOR_DEMO_MODE="false", SMTP_HOST="", RESEND_API_KEY="")
sys.path.insert(0, str(ROOT / "backend"))
spec = importlib.util.spec_from_file_location("mobile_backend_fixtures", ROOT / "backend/tests/conftest.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
for name in ("db_session", "client", "registered_user", "auth_headers", "auth_client", "second_user_headers",
             "_bypass_billing", "_bypass_rate_limit"):
    globals()[name] = getattr(fixtures, name)


@pytest.fixture(autouse=True)
def isolate_uploads_and_external_services(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import app.api.auth as auth
    import app.api.memorials as memorials
    from app.config import settings
    monkeypatch.setattr(auth, "send_verification_email", lambda *a, **kw: None)
    monkeypatch.setattr(settings, "USE_S3", False)
    monkeypatch.setattr(memorials, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(memorials, "THUMBNAILS_DIR", tmp_path)
    monkeypatch.setitem(sys.modules, "app.workers.worker", SimpleNamespace(
        create_memory_embedding_task=SimpleNamespace(delay=lambda **kw: None)))
