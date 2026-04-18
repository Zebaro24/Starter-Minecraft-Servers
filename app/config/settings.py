from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    telegram_bot_token: str
    telegram_admin_id: int

    # Default RCON password used for all servers unless overridden per-server
    rcon_password: str = "minecraft"

    # Base domain used to build full addresses from server subdomains — e.g. "zebaro.dev"
    # Result: subdomain="mc1" + base_domain="zebaro.dev" → "mc1.zebaro.dev"
    base_domain: str = "zebaro.dev"


settings = Settings()  # type: ignore
