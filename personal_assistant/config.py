from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_timezone: str = os.getenv("APP_TIMEZONE", "Asia/Seoul")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/personal_assistant_pc.db"))

    google_calendar_id: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    google_oauth_client_secret_file: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE", "")
    google_oauth_token_file: str = os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "data/google_token.json")
    google_registered_email: str = os.getenv("GOOGLE_REGISTERED_EMAIL", "")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    site_collection_interval_hours: int = int(os.getenv("SITE_COLLECTION_INTERVAL_HOURS", "3"))
    seoul50plus_url: str = os.getenv("SEOUL50PLUS_URL", "https://www.50plus.or.kr/job.do")
    kstartup_url: str = os.getenv("KSTARTUP_URL", "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do")

    @property
    def google_calendar_enabled(self) -> bool:
        return bool(self.google_service_account_file or self.google_oauth_client_secret_file)

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(self.google_oauth_client_secret_file)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.gemini_api_key or self.openai_api_key)


settings = Settings()
