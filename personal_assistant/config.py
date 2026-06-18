from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_timezone: str = os.getenv("APP_TIMEZONE", "Asia/Seoul")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/personal_assistant.db"))
    google_calendar_id: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    @property
    def google_calendar_enabled(self) -> bool:
        return bool(self.google_service_account_file)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.gemini_api_key or self.openai_api_key)


settings = Settings()

