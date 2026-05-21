"""
Application configuration via pydantic-settings.
All secrets and config are loaded from environment variables / .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Kiosk-GPT."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────
    app_env: str = "development"
    app_base_url: str = "http://localhost:8000"
    log_level: str = "INFO"

    # ── WhatsApp Cloud API ───────────────────────────────
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""

    # ── Groq AI ──────────────────────────────────────────
    groq_api_key: str = ""

    # ── Supabase ─────────────────────────────────────────
    supabase_url: str = ""
    supabase_key: str = ""

    # ── LDK Node ─────────────────────────────────────────
    ldk_storage_dir: str = "./ldk_data"
    ldk_network: str = "testnet"
    ldk_esplora_url: str = "https://mempool.space/testnet/api"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def whatsapp_api_url(self) -> str:
        return f"https://graph.facebook.com/v21.0/{self.whatsapp_phone_number_id}/messages"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
