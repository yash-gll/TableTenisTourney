from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://tt:tt@localhost:5432/tt"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 14

    verify_token_ttl_hours: int = 48
    reset_token_ttl_hours: int = 2

    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    # Hardening / ops
    rate_limit_enabled: bool = True
    # Log verification/reset links to the console (dev convenience; these links
    # contain raw tokens — disable in production once real email is wired up).
    log_verification_links: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def jwt_secret_is_default(self) -> bool:
        return self.jwt_secret == "change-me-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
