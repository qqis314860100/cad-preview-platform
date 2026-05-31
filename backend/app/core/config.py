from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    storage_dir: Path = Path("backend/storage")
    database_path: Path = Path("backend/storage/cad_preview.sqlite3")
    allowed_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    max_upload_bytes: int = 5 * 1024 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_prefix="CAD_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
