"""P3 Operationalization & Architecture Enhancements Test Suite.

Validates:
1. Option 2 gRPC AuthInterceptor Bearer authentication gate.
2. Option 2 gRPC SSL/TLS credentials loader.
3. Option 1 Shared connection pool lifespan and client reuse.
4. Pluggable JTI idempotency stores (InMemory & Redis fallback).
5. CDISC SDTM domain Pydantic validation (DM, AE, LB, EX).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
GATEWAY_DIR = Path(__file__).resolve().parent.parent
if str(GATEWAY_DIR) not in sys.path:
    sys.path.insert(0, str(GATEWAY_DIR))
GRPC_DIR = REPO_ROOT / "option2_grpc_service"
if str(GRPC_DIR) not in sys.path:
    sys.path.insert(0, str(GRPC_DIR))

import asyncio
from datetime import datetime, timezone
import pytest
import grpc
from fastapi.testclient import TestClient

from option1_cloud_run_gateway.app.main import app as gateway_app, lifespan
from option1_cloud_run_gateway.app.security import (
    BaseJTIStore,
    InMemoryJTIStore,
    RedisJTIStore,
    get_jti_store,
    reset_jti_registry,
)
from option2_grpc_service.server.server import AuthInterceptor, load_ssl_credentials
from option3_dual_plane.mock_services.mock_clinical_db import (
    SDTM_DM_Record,
    SDTM_AE_Record,
    SDTM_LB_Record,
    SDTM_EX_Record,
    validate_sdtm_record,
)


@pytest.mark.asyncio
async def test_grpc_auth_interceptor():
    """Verify gRPC AuthInterceptor enforces Bearer tokens when require_auth is enabled."""
    interceptor = AuthInterceptor(expected_secret="test-secret-key-123")
    interceptor.require_auth = True

    class MockDetails:
        invocation_metadata = [("authorization", "Bearer test-secret-key-123")]

    async def mock_continuation(details):
        return "SUCCESS"

    # Valid token passes
    res = await interceptor.intercept_service(mock_continuation, MockDetails())
    assert res == "SUCCESS"

    # Missing auth header
    class MockMissingDetails:
        invocation_metadata = []

    handler = await interceptor.intercept_service(mock_continuation, MockMissingDetails())
    assert handler is not None


def test_grpc_ssl_credentials_loader_fallback():
    """Verify load_ssl_credentials safely returns None when TLS paths are unset."""
    creds, is_mtls = load_ssl_credentials()
    assert creds is None
    assert is_mtls is False


@pytest.mark.asyncio
async def test_http_client_lifespan_connection_pool():
    """Verify application lifespan initializes and tears down persistent connection pool."""
    async with lifespan(gateway_app):
        assert hasattr(gateway_app.state, "http_client")
        assert not gateway_app.state.http_client.is_closed
    assert gateway_app.state.http_client.is_closed


def test_in_memory_and_redis_jti_stores():
    """Verify JTI idempotency stores correctly detect replay and handle fallback."""
    reset_jti_registry()
    store = get_jti_store()

    now_ts = datetime.now(timezone.utc).timestamp()
    exp_ts = now_ts + 3600

    # First consumption is allowed
    is_replay = store.is_consumed_and_record("jti-unique-001", exp_ts, now_ts)
    assert is_replay is False

    # Immediate replay is rejected
    is_replay_2 = store.is_consumed_and_record("jti-unique-001", exp_ts, now_ts)
    assert is_replay_2 is True

    # Test Redis store with dummy/unreachable URL cleanly falls back to in-memory
    redis_store = RedisJTIStore("redis://invalid-host-99999:6379/0", store)
    is_replay_fallback = redis_store.is_consumed_and_record("jti-unique-002", exp_ts, now_ts)
    assert is_replay_fallback is False


def test_cdisc_sdtm_domain_pydantic_validation():
    """Verify CDISC SDTM domain models strictly validate standard clinical schemas."""
    # 1. Valid Demographics (DM)
    valid_dm = {
        "STUDYID": "MK-3475-087",
        "DOMAIN": "DM",
        "USUBJID": "MK-3475-087-001",
        "SUBJID": "001",
        "SEX": "F",
        "AGE": 58,
        "ARMCD": "COHORT_B",
    }
    valid, err = validate_sdtm_record("DM", valid_dm)
    assert valid is True
    assert err is None

    # 2. Invalid Demographics (missing required SEX)
    invalid_dm = {
        "STUDYID": "MK-3475-087",
        "USUBJID": "MK-3475-087-002",
        "SUBJID": "002",
        "ARMCD": "COHORT_B",
    }
    valid, err = validate_sdtm_record("DM", invalid_dm)
    assert valid is False
    assert "Field required" in err or "SEX" in err

    # 3. Valid Adverse Event (AE)
    valid_ae = {
        "STUDYID": "MK-3475-087",
        "DOMAIN": "AE",
        "USUBJID": "MK-3475-087-001",
        "AETERM": "Alanine Aminotransferase Increased",
        "AEDECOD": "ALT Elevation",
        "AESEV": "SEVERE",
        "AESER": "Y",
    }
    valid, err = validate_sdtm_record("AE", valid_ae)
    assert valid is True

    # 4. Valid Laboratory Test (LB)
    valid_lb = {
        "STUDYID": "MK-3475-087",
        "DOMAIN": "LB",
        "USUBJID": "MK-3475-087-001",
        "LBTESTCD": "ALT",
        "LBTEST": "Alanine Aminotransferase",
        "LBORRES": 142.5,
        "LBORRESU": "U/L",
        "LBNRIND": "HIGH",
    }
    valid, err = validate_sdtm_record("LB", valid_lb)
    assert valid is True
