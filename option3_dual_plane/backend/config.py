"""Configuration for Option 3 Dual-Plane Architecture."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class PlaneConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

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
        default="Enterprise-plane2-hitl-signing-key-gxp-2026",
        description="HMAC secret for state token signatures"
    )


config = PlaneConfig()
