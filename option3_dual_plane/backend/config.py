"""Configuration for Option 3 Dual-Plane Architecture."""

import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class PlaneConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    APP_ENV: str = Field(default="demo", description="Option 3 is a demo/development architecture experiment")

    # GCP Vertex AI Configuration (Plane 1)
    GCP_PROJECT_ID: str = Field(default="Enterprise-clinical-gxp-prod", description="GCP Project ID")
    GCP_LOCATION: str = Field(default="us-central1", description="Vertex AI Region")
    MODEL_NAME: str = Field(default="gemini-1.5-pro", description="Foundation model")
    MOCK_VERTEX_AI: bool = Field(default=True, description="Use local high-fidelity mock if no GCP credentials")

    # UI Bridge Service (Plane 2 Gateway)
    BRIDGE_SERVICE_URL: str = Field(default="http://127.0.0.1:8092", description="Bridge service URL")
    BRIDGE_PORT: int = Field(default=8092, description="Port for Bridge service")

    # Simulated GE Inbound Service
    GE_INBOUND_URL: str = Field(default="http://127.0.0.1:8093", description="GE Inbound push receiver URL")
    GE_INBOUND_PORT: int = Field(default=8093, description="Port for mock GE inbound")

    # Security
    HMAC_SECRET: str = Field(
        default_factory=lambda: "option3-ephemeral-" + secrets.token_urlsafe(48),
        description="Demo HMAC secret. This experimental plane is not production-hardened."
    )

    @model_validator(mode="after")
    def validate_environment(self) -> "PlaneConfig":
        """Prevent accidental deployment of the experimental plane as production."""
        env = (self.APP_ENV or os.getenv("APP_ENV", "demo")).lower()
        if env in {"staging", "production"}:
            raise ValueError(
                "Option 3 dual-plane service is an architecture experiment and is not "
                "production-hardened. Use the Option 1 policy gateway or complete "
                "identity, durable audit, replay, key-management, and operational controls first."
            )
        historical_secret = "enterprise-plane2-hitl-signing-key-gxp-2026"
        if self.HMAC_SECRET.lower() == historical_secret:
            raise ValueError("Historical published Option 3 HMAC secret is permanently rejected")
        return self


config = PlaneConfig()
