"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "ZeroELD AI Agent"
    debug: bool = True
    log_level: str = "INFO"

    # ZeroELD API (kept for reference, replaced by Fortex)
    zeroeld_api_url: str = "https://cloud.zeroeld.us"
    zeroeld_username: str = ""
    zeroeld_password: str = ""
    zeroeld_device_model: str = "AI Agent"
    zeroeld_os_version: str = "1.0"

    # Fortex API
    fortex_api_url: str
    fortex_auth_token: str = "y3He9C57ecfmMAsR19"
    fortex_system_name: str = "zero"

    # Fortex UI (Playwright)
    fortex_ui_url: str = "https://fortex-zero.us/"
    fortex_ui_username: str
    fortex_ui_password: str

    # Playwright Configuration
    playwright_headless: bool = False  # Show browser during automation (user can watch)
    playwright_screenshots_dir: str = "./screenshots"
    playwright_session_dir: str = "./playwright_data"

    # Database
    database_url: str

    # Supabase (optional)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # Security
    secret_key: str
    access_token_expire_minutes: int = 60

    # Agent Configuration
    agent_polling_interval_seconds: int = 300
    agent_max_concurrent_fixes: int = 1
    agent_require_approval: bool = True
    agent_dry_run_mode: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars like tg_bot


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings
