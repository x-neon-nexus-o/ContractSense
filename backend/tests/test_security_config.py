from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _import_config(**overrides: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "production",
            "SECRET_KEY": "s" * 48,
            "CORS_ORIGINS": "https://contracts.example",
            **overrides,
        }
    )
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", "from backend.app.config import settings; print(settings.app_env)"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_development_defaults_to_same_origin_only_cors() -> None:
    env = os.environ.copy()
    env.update({"APP_ENV": "development", "SECRET_KEY": "d" * 48})
    env.pop("CORS_ORIGINS", None)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", "from backend.app.config import settings; print(repr(settings.cors_origins))"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "''"


def test_production_rejects_placeholder_secret() -> None:
    result = _import_config(SECRET_KEY="replace-with-a-long-random-secret")
    assert result.returncode != 0
    assert "private SECRET_KEY" in result.stderr


def test_production_rejects_wildcard_cors() -> None:
    result = _import_config(CORS_ORIGINS="https://contracts.example,*")
    assert result.returncode != 0
    assert "explicit CORS_ORIGINS" in result.stderr


def test_production_rejects_empty_cors() -> None:
    result = _import_config(CORS_ORIGINS="  ,  ")
    assert result.returncode != 0
    assert "empty and wildcard origins" in result.stderr


def test_production_accepts_explicit_origins_and_strong_secret() -> None:
    result = _import_config()
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "production"
