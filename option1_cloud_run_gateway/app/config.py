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

    # Application settings
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8080, description="Server port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    SERVICE_NAME: str = Field(default="Enterprise-a2a-interceptor-gateway", description="Service identifier")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service release version")

    # Security & Tokens
    JWT_SECRET: str = Field(
        default="Enterprise-gxp-clinical-vault-super-secure-hmac-sha256-key-2026",
        description="HMAC secret key for sealing state tokens"
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

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Enforce strict secret entropy in production to prevent hardcoded key exploits."""
        if self.APP_ENV.lower() == "production":
            insecure_defaults = [
                "Enterprise-gxp-clinical-vault-super-secure-hmac-sha256-key-2026",
                "secret",
                "changeme",
                "default",
                "test",
            ]
            if not self.JWT_SECRET or self.JWT_SECRET in insecure_defaults or len(self.JWT_SECRET) < 32:
                raise ValueError(
                    "CRITICAL GxP SECURITY VIOLATION: Default or weak JWT_SECRET cannot be used in production! "
                    "Configure a strong cryptographic secret (>= 32 characters) via JWT_SECRET environment variable."
                )
        return self


settings = Settings()
