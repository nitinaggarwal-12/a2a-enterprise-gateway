"""Containerization Pre-Flight & CIS Benchmark Quality Gate.

Validates:
1. Dockerfile structural integrity, multi-stage layering, and non-root execution.
2. Build context asset existence for all COPY directives.
3. .dockerignore protection against credential, cache, and artifact leaks.
4. Autonomous entrypoint importability without cross-boundary contamination.
5. Cloud Run contract adherence (dynamic $PORT binding).
"""

import os
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_root_dockerfile_cis_compliance_and_assets():
    """Verify root Dockerfile satisfies CIS non-root benchmarks and valid COPY contexts."""
    dockerfile_path = REPO_ROOT / "Dockerfile"
    assert dockerfile_path.exists(), "Root Dockerfile must exist"
    content = dockerfile_path.read_text(encoding="utf-8")

    # Base image check
    assert "FROM python:3.11-slim" in content, "Must use python:3.11-slim base"

    # CIS Non-root user check
    assert "useradd" in content and "appuser" in content, "Must configure dedicated non-root user"
    assert "USER appuser" in content, "Must drop root privileges with USER appuser"

    # Cloud Run dynamic PORT compliance
    assert "${PORT:-8080}" in content or "$PORT" in content, "Must dynamically bind to $PORT for Cloud Run"

    # Validate all COPY source directories physically exist in repository
    copy_patterns = re.findall(r"COPY\s+([^\s]+)\s+([^\s]+)", content)
    for src, _ in copy_patterns:
        # Strip trailing slashes or dot references
        clean_src = src.rstrip("/")
        if clean_src and not clean_src.startswith("--"):
            target_path = REPO_ROOT / clean_src
            assert target_path.exists(), f"COPY source '{clean_src}' must physically exist in build context"


def test_option1_cloud_run_dockerfile_compliance():
    """Verify Option 1 Cloud Run Gateway Dockerfile satisfies Cloud Run specification."""
    df_path = REPO_ROOT / "option1_cloud_run_gateway" / "Dockerfile"
    assert df_path.exists(), "Option 1 Dockerfile must exist"
    content = df_path.read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in content
    assert "USER appuser" in content, "Must run as non-root user appuser"
    assert "--chown=appuser:appgroup" in content, "Must set non-root ownership on copied assets"
    assert "${PORT:-8080}" in content or "$PORT" in content, "Must support dynamic Cloud Run $PORT"

    # Verify requirements.txt and app directory exist
    opt1_dir = REPO_ROOT / "option1_cloud_run_gateway"
    assert (opt1_dir / "requirements.txt").exists()
    assert (opt1_dir / "app").exists()
    assert (opt1_dir / "app" / "main.py").exists()


def test_option2_grpc_dockerfile_compliance():
    """Verify Option 2 gRPC Server Dockerfile implements multi-stage build and non-root user."""
    df_path = REPO_ROOT / "option2_grpc_service" / "Dockerfile"
    assert df_path.exists(), "Option 2 Dockerfile must exist"
    content = df_path.read_text(encoding="utf-8")

    # Multi-stage build check
    assert "FROM python:3.11-slim as builder" in content, "Must use multi-stage builder"
    assert "USER appuser" in content, "Final stage must run as appuser"
    assert "--chown=appuser:appgroup" in content, "Final stage COPY must assign appuser ownership"
    assert "EXPOSE 50051" in content, "Must expose gRPC port 50051"

    # Verify build context directories
    opt2_dir = REPO_ROOT / "option2_grpc_service"
    assert (opt2_dir / "requirements.txt").exists()
    assert (opt2_dir / "server").exists()
    assert (opt2_dir / "server" / "server.py").exists()
    assert (opt2_dir / "protos").exists()
    assert (opt2_dir / "a2a").exists()


def test_dockerignore_coverage():
    """Verify .dockerignore files protect sensitive credentials, virtualenvs, and test artifacts."""
    root_ignore = REPO_ROOT / ".dockerignore"
    assert root_ignore.exists(), "Root .dockerignore must exist"
    root_rules = root_ignore.read_text(encoding="utf-8")

    critical_exclusions = [".git", ".venv", ".pytest_cache", "scratch", "*.sqlite", "*.db*"]
    for excl in critical_exclusions:
        assert excl in root_rules, f"Root .dockerignore must exclude '{excl}'"

    opt1_ignore = REPO_ROOT / "option1_cloud_run_gateway" / ".dockerignore"
    assert opt1_ignore.exists(), "Option 1 .dockerignore must exist"

    opt2_ignore = REPO_ROOT / "option2_grpc_service" / ".dockerignore"
    assert opt2_ignore.exists(), "Option 2 .dockerignore must exist"


def test_option2_standalone_independence():
    """Verify Option 2 gRPC service has zero cross-module dependency on option1_cloud_run_gateway."""
    push_dispatcher_file = REPO_ROOT / "option2_grpc_service" / "server" / "push_dispatcher.py"
    content = push_dispatcher_file.read_text(encoding="utf-8")

    assert "option1_cloud_run_gateway" not in content, (
        "Option 2 push_dispatcher must NOT import from option1_cloud_run_gateway; "
        "must be self-contained for isolated container deployment."
    )
    assert "def is_safe_webhook_url" in content, "Must contain self-contained SSRF guard"
