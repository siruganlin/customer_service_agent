from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL")
    app_host: str = os.getenv("APP_HOST")
    app_port: int = int(os.getenv("APP_PORT"))


settings = Settings()
