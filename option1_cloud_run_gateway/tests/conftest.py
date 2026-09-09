"""Explicit test-only security configuration.

Production defaults intentionally fail closed. The test suite opts into mock
authentication and lab APIs here so tests never depend on insecure defaults.
"""

from option1_cloud_run_gateway.app.config import settings


settings.APP_ENV = "development"
settings.ALLOW_DEV_AUTH = True
settings.ENABLE_LAB_ENDPOINTS = True
settings.TRUST_PROXY_HEADERS = False
settings.JWT_SECRET = "pytest-only-secret-with-more-than-thirty-two-characters"
settings.JWT_PREVIOUS_SECRET = None
settings.WEBHOOK_ALLOWED_HOSTS = ""
