"""Runtime settings, all overridable via CROPSTACK_* environment variables."""

import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CROPSTACK_", env_file=".env", extra="ignore")

    data_dir: Path = Path("./data")
    static_dir: Path = Path("./static")
    secret_key: str = ""
    secure_cookies: bool = False  # set true behind HTTPS

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'cropstack.db'}"

    def resolved_secret(self) -> str:
        """Return the configured secret, or create and persist one in the data dir."""
        if self.secret_key:
            return self.secret_key
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / "secret.key"
        if not path.exists():
            path.write_text(secrets.token_urlsafe(48))
            path.chmod(0o600)
        return path.read_text().strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
