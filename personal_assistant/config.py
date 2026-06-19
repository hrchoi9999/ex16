from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_SECRET_ENV = PROJECT_ROOT.parent / ".chatgptkey.env"

if SHARED_SECRET_ENV.exists():
    load_dotenv(SHARED_SECRET_ENV)
load_dotenv(PROJECT_ROOT / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    app_timezone: str = os.getenv("APP_TIMEZONE", "Asia/Seoul")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/personal_assistant_pc.db"))

    google_calendar_id: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    google_oauth_client_secret_file: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE", "")
    google_oauth_client_id: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    google_oauth_client_secret: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    google_oauth_redirect_uri: str = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8501")
    google_oauth_token_file: str = os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "data/google_token.json")
    google_registered_email: str = os.getenv("GOOGLE_REGISTERED_EMAIL", "")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    site_collection_interval_hours: int = int(os.getenv("SITE_COLLECTION_INTERVAL_HOURS", "3"))
    seoul50plus_url: str = os.getenv("SEOUL50PLUS_URL", "https://www.50plus.or.kr/")
    seoul50plus_training_url: str = os.getenv(
        "SEOUL50PLUS_TRAINING_URL",
        "https://www.50plus.or.kr/in_appList.do?bizSeUrl=IN49009&rcrtSeUrl=IN47002",
    )
    seoul50plus_job_support_url: str = os.getenv(
        "SEOUL50PLUS_JOB_SUPPORT_URL",
        "https://www.50plus.or.kr/in_appList.do?bizSeUrl=IN49001&rcrtSeUrl=IN47002",
    )
    kstartup_url: str = os.getenv("KSTARTUP_URL", "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do")

    @property
    def google_calendar_enabled(self) -> bool:
        return bool(
            self.google_service_account_file
            or self.google_oauth_client_secret_file
            or (self.google_oauth_client_id and self.google_oauth_client_secret)
        )

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(self.google_oauth_client_secret_file or (self.google_oauth_client_id and self.google_oauth_client_secret))

    @property
    def llm_enabled(self) -> bool:
        return bool(self.gemini_api_key or self.openai_api_key)


settings = Settings()
