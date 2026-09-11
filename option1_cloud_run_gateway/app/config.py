"""Configuration module for Cloud Run Interceptor Gateway."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """Gateway settings and environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application settings: Default to production fail-closed security
    APP_ENV: str = Field(default="production", description="Environment: development, staging, production")
    ALLOW_DEV_AUTH: bool = Field(default=False, description="Explicit flag required to enable dev/mock auth in non-production")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8080, description="Server port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    SERVICE_NAME: str = Field(default="enterprise-a2a-interceptor-gateway", description="Service identifier")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service release version")

    # Security & Tokens (Dual-key rotation support)
    JWT_SECRET: str = Field(
        default="Enterprise-gxp-clinical-vault-super-secure-hmac-sha256-key-2026",
        description="HMAC secret key for sealing state tokens"
    )
    GATEWAY_HMAC_SECRET: Optional[str] = Field(
        default=None,
        description="Primary HMAC secret key (canonical alias for JWT_SECRET)"
    )
    GATEWAY_HMAC_SECRET_SECONDARY: Optional[str] = Field(
        default=None,
        description="Secondary HMAC secret key for zero-downtime key rotation"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    STATE_TOKEN_TTL_HOURS: int = Field(default=48, description="State token time-to-live in hours (HITL 48hr window)")
    EXPECTED_AUDIENCE: str = Field(
        default="https://a2a-gateway-Enterprise.run.app",
        description="Expected Google OIDC audience"
    )

    # Downstream Agent Routing
    DOWNSTREAM_AGENT_URL: Optional[str] = Field(
        default=None,
        description="Downstream agent URL (if empty, gateway runs in standalone mock mode)"
    )
    DOWNSTREAM_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        description="HTTP timeout when proxying to downstream agent"
    )

    @property
    def active_hmac_secret(self) -> str:
        """Return the active primary HMAC secret key."""
        return self.GATEWAY_HMAC_SECRET or self.JWT_SECRET

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Enforce strict secret entropy in production to prevent hardcoded key exploits."""
        active_secret = self.GATEWAY_HMAC_SECRET or self.JWT_SECRET
        if self.APP_ENV.lower() == "production":
            insecure_defaults = [
                "Enterprise-gxp-clinical-vault-super-secure-hmac-sha256-key-2026",
                "secret",
                "changeme",
                "default",
                "test",
            ]
            if not active_secret or active_secret in insecure_defaults or len(active_secret) < 32:
                raise ValueError(
                    "CRITICAL GxP SECURITY VIOLATION: Default or weak JWT_SECRET / GATEWAY_HMAC_SECRET cannot be used in production! "
                    "Configure a strong cryptographic secret (>= 32 characters) via GATEWAY_HMAC_SECRET environment variable."
                )
            if self.ALLOW_DEV_AUTH:
                raise ValueError(
                    "CRITICAL GxP SECURITY VIOLATION: ALLOW_DEV_AUTH cannot be enabled when APP_ENV=production!"
                )
        return self


settings = Settings()
