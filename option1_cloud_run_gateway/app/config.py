"""Configuration module for Cloud Run Interceptor Gateway."""

import secrets
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

    # Application settings
    APP_ENV: str = Field(default="demo", description="Environment: demo, development, staging, production")
    ALLOW_DEV_AUTH: bool = Field(
        default=False,
        description="Explicit local-only switch for mock development authentication. Never enable in demo/staging/production."
    )
    ENABLE_LAB_ENDPOINTS: bool = Field(
        default=False,
        description="Expose experimental/demo mutation endpoints. Disabled by default."
    )
    TRUST_PROXY_HEADERS: bool = Field(
        default=False,
        description="Trust X-Forwarded-For only when an upstream trusted proxy strips caller-supplied forwarding headers."
    )
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8080, description="Server port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    SERVICE_NAME: str = Field(default="Enterprise-a2a-interceptor-gateway", description="Service identifier")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service release version")

    # Security & Tokens
    JWT_SECRET: str = Field(
        default_factory=lambda: "ephemeral-" + secrets.token_urlsafe(48),
        description="HMAC secret key for sealing state tokens. Production must inject a managed secret."
    )
    JWT_PREVIOUS_SECRET: Optional[str] = Field(
        default=None,
        description="Optional previous HMAC secret accepted only for verification during key rotation."
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
        description="Downstream A2A agent URL. Production requires a durable downstream service."
    )
    DOWNSTREAM_ID_TOKEN_AUDIENCE: Optional[str] = Field(
        default=None,
        description="Optional Google OIDC audience used to mint a destination-specific ADC ID token for the downstream agent."
    )
    DOWNSTREAM_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        description="HTTP timeout when proxying to downstream agent"
    )
    WEBHOOK_ALLOWED_HOSTS: str = Field(
        default="",
        description="Comma-separated exact webhook hostnames allowed in staging/production. Empty means deny all external push callbacks."
    )
    CORS_ALLOWED_ORIGINS: str = Field(
        default="",
        description="Comma-separated exact HTTPS origins permitted for cross-origin browser access. Same-origin access needs no entry."
    )

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Enforce strict secret entropy in production to prevent hardcoded key exploits."""
        env = self.APP_ENV.lower()
        if env not in {"demo", "development", "staging", "production"}:
            raise ValueError("APP_ENV must be one of: demo, development, staging, production")

        if self.ALLOW_DEV_AUTH and env != "development":
            raise ValueError("ALLOW_DEV_AUTH may only be enabled when APP_ENV=development")

        if env in {"staging", "production"}:
            insecure_defaults = {
                "secret",
                "changeme",
                "default",
                "test",
                # Historical repository default is permanently compromised once published.
                "enterprise-gxp-clinical-vault-super-secure-hmac-sha256-key-2026",
            }
            if (
                not self.JWT_SECRET
                or self.JWT_SECRET.startswith("ephemeral-")
                or self.JWT_SECRET.lower() in insecure_defaults
                or len(self.JWT_SECRET) < 32
            ):
                raise ValueError(
                    "Managed JWT_SECRET (>=32 characters) is required in staging/production. "
                    "Do not rely on an application default."
                )

        if self.JWT_PREVIOUS_SECRET is not None and len(self.JWT_PREVIOUS_SECRET) < 32:
            raise ValueError("JWT_PREVIOUS_SECRET must be >=32 characters when configured")
        return self


settings = Settings()
