"""Pytest configuration and environment initialization for Gateway test suites."""

import os
import pytest

# Ensure local test runners explicitly set non-production environment with dev auth enabled
os.environ["APP_ENV"] = "development"
os.environ["ALLOW_DEV_AUTH"] = "true"
os.environ["JWT_SECRET"] = "Enterprise-gxp-clinical-vault-super-secure-hmac-sha256-key-2026"
