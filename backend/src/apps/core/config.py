from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any, Iterable, Mapping, Union
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE_PATH = BACKEND_ROOT / ".env"
GENERAL_SETTINGS_TABLE_NAME = "generalsetting"
NON_RUNTIME_EDITABLE_SETTING_KEYS = frozenset(
    {
        "DATABASE_URL",
        "SYNC_DATABASE_URL",
        "SECRET_KEY",
        "PASSWORD_PEPPER",
        "POSTGRES_SERVER",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_DB",
        "REDIS_PASSWORD",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "GOOGLE_MAPS_API_KEY",
        "EMAIL_HOST_PASSWORD",
        "RESEND_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "VAPID_PRIVATE_KEY",
        "FCM_SERVER_KEY",
        "FCM_API_KEY",
        "FCM_SERVICE_ACCOUNT_JSON",
        "FCM_SERVICE_ACCOUNT_FILE",
        "ONESIGNAL_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "VONAGE_API_KEY",
        "VONAGE_API_SECRET",
        "KHALTI_SECRET_KEY",
        "ESEWA_SECRET_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "PAYPAL_CLIENT_SECRET",
        "GOOGLE_CLIENT_SECRET",
        "GITHUB_CLIENT_SECRET",
        "FACEBOOK_CLIENT_SECRET",
    }
)
PUBLIC_GENERAL_SETTING_KEYS = frozenset(
    {
        "PROJECT_NAME",
        "APP_ENV",
        "FEATURE_AUTH",
        "FEATURE_MULTITENANCY",
        "FEATURE_NOTIFICATIONS",
        "FEATURE_WEBSOCKETS",
        "FEATURE_FINANCE",
        "FEATURE_ANALYTICS",
        "FEATURE_SOCIAL_AUTH",
        "FEATURE_MAPS",
        "EMAIL_ENABLED",
        "EMAIL_PROVIDER",
        "PUSH_ENABLED",
        "PUSH_PROVIDER",
        "SMS_ENABLED",
        "SMS_PROVIDER",
        "ANALYTICS_ENABLED",
        "ANALYTICS_PROVIDER",
        "MAP_PROVIDER",
        "KHALTI_ENABLED",
        "ESEWA_ENABLED",
        "STRIPE_ENABLED",
        "PAYPAL_ENABLED",
    }
)


def _parse_csv(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_same_site(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in {"lax", "strict", "none"}:
        raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
    return normalized


def _normalize_storage_backend(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in {"local", "s3"}:
        raise ValueError("STORAGE_BACKEND must be one of: local, s3")
    return normalized


def serialize_setting_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        case_sensitive=True,
        extra="ignore",
        enable_decoding=False,
    )

    PROJECT_NAME: str = "FastAPI Template"
    APP_ENV: str = "development"
    APP_INSTANCE_NAME: str = "fastapi-template"
    APP_REGION: str = "local"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkey"
    PASSWORD_PEPPER: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_COOKIE: str = "access_token"
    REFRESH_TOKEN_COOKIE: str = "refresh_token"
    SECURE_COOKIES: bool = False
    COOKIE_DOMAIN: str | None = None
    COOKIE_SAMESITE: str = "lax"

    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    REQUIRE_EMAIL_VERIFICATION: bool = False
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False

    DEBUG: bool = True
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_PERSIST_MIN_LEVEL: str = "INFO"
    LOG_OUTPUTS: list[str] = ["console", "database", "web"]
    LOG_FILE_PATH: str = "logs/application.log"
    LOG_RETENTION_DAYS: int = 7
    LOG_SQL_QUERIES: bool = False
    FAILED_LOGIN_BURST_THRESHOLD: int = 5
    FAILED_LOGIN_BURST_WINDOW_MINUTES: int = 30
    TOKEN_CHURN_THRESHOLD: int = 3
    TOKEN_CHURN_WINDOW_MINUTES: int = 10
    RATE_LIMIT_SPIKE_THRESHOLD: int = 10
    RATE_LIMIT_SPIKE_WINDOW_MINUTES: int = 10
    ERROR_SPIKE_THRESHOLD: int = 5
    ERROR_SPIKE_WINDOW_MINUTES: int = 10

    FEATURE_AUTH: bool = True
    FEATURE_MULTITENANCY: bool = True
    FEATURE_NOTIFICATIONS: bool = True
    FEATURE_WEBSOCKETS: bool = True
    FEATURE_FINANCE: bool = True
    FEATURE_ANALYTICS: bool = True
    FEATURE_SOCIAL_AUTH: bool = True
    FEATURE_MAPS: bool = False

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_URL: str | None = None
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_TASK_TIME_LIMIT: int = 30 * 60
    CELERY_RESULT_EXPIRES: int = 3600
    CELERY_TASK_ALWAYS_EAGER: bool | None = None
    CELERY_QUEUE_DEFAULT: str = "default"

    BACKEND_CORS_ORIGINS: list[Union[str, AnyHttpUrl]] = [
        "http://localhost",
        "http://localhost:3000",
    ]
    TRUSTED_HOSTS: list[str] = ["localhost", "127.0.0.1", "test", "testserver"]
    PROXY_TRUSTED_HOSTS: list[str] = ["*"]
    FORWARDED_ALLOW_IPS: list[str] = ["*"]
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_SIGNUP: str = "3/hour"
    RATE_LIMIT_PASSWORD_RESET: str = "3/hour"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "app"
    DATABASE_URL: str | None = None
    SYNC_DATABASE_URL: str | None = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    FRONTEND_URL: str = "http://localhost:3000"
    SERVER_HOST: str = "http://localhost:8000"
    HTTP_TIMEOUT_SECONDS: float = 15.0
    HTTP_RETRY_COUNT: int = 1
    HTTP_BACKOFF_SECONDS: float = 0.5
    WS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    WS_HEARTBEAT_INTERVAL_SECONDS: int = 30
    WS_MAX_IDLE_SECONDS: int = 90

    MEDIA_DIR: str = "media"
    MEDIA_URL: str = "/media"
    STORAGE_BACKEND: str = "local"
    MEDIA_BASE_URL: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = ""
    S3_USE_PATH_STYLE: bool = False
    MAX_AVATAR_SIZE_MB: int = 5

    MAP_PROVIDER: str = "osm"
    OSM_MAPS_ENABLED: bool = True
    GOOGLE_MAPS_ENABLED: bool = False
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_MAPS_MAP_ID: str = ""
    MAP_DEFAULT_LATITUDE: float = 27.7172
    MAP_DEFAULT_LONGITUDE: float = 85.3240
    MAP_DEFAULT_ZOOM: int = 13

    EMAIL_ENABLED: bool = False
    EMAIL_PROVIDER: str = "smtp"
    EMAIL_FALLBACK_PROVIDERS: list[str] = []
    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: str = "user@example.com"
    EMAIL_HOST_PASSWORD: SecretStr = SecretStr("password")
    EMAIL_FROM_ADDRESS: str = "noreply@example.com"
    RESEND_API_KEY: str = ""
    RESEND_FROM_ADDRESS: str = "noreply@example.com"
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: SecretStr = SecretStr("")
    SES_FROM_ADDRESS: str = "noreply@example.com"

    PUSH_ENABLED: bool = False
    PUSH_PROVIDER: str = "webpush"
    PUSH_FALLBACK_PROVIDERS: list[str] = []
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = "mailto:admin@example.com"
    FCM_SERVER_KEY: str = ""
    FCM_PROJECT_ID: str = ""
    FCM_WEB_VAPID_KEY: str = ""
    FCM_API_KEY: str = ""
    FCM_APP_ID: str = ""
    FCM_MESSAGING_SENDER_ID: str = ""
    FCM_AUTH_DOMAIN: str = ""
    FCM_STORAGE_BUCKET: str = ""
    FCM_MEASUREMENT_ID: str = ""
    FCM_SERVICE_ACCOUNT_JSON: str = ""
    FCM_SERVICE_ACCOUNT_FILE: str = ""
    ONESIGNAL_APP_ID: str = ""
    ONESIGNAL_API_KEY: str = ""
    ONESIGNAL_WEB_APP_ID: str = ""

    SMS_ENABLED: bool = False
    SMS_PROVIDER: str = "twilio"
    SMS_FALLBACK_PROVIDERS: list[str] = []
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    VONAGE_API_KEY: str = ""
    VONAGE_API_SECRET: str = ""
    VONAGE_FROM_NUMBER: str = ""

    KHALTI_ENABLED: bool = True
    KHALTI_SECRET_KEY: str = "05bf95cc57244045b8df5fad06748dab"
    KHALTI_BASE_URL: str = "https://dev.khalti.com/api/v2/"
    ESEWA_ENABLED: bool = True
    ESEWA_SECRET_KEY: str = "8gBm/:&EnhH.1/q"
    ESEWA_MERCHANT_CODE: str = "EPAYTEST"
    ESEWA_BASE_URL: str = "https://rc-epay.esewa.com.np/api/epay/"
    STRIPE_ENABLED: bool = False
    STRIPE_SECRET_KEY: str = "sk_test_your_stripe_secret_key"
    STRIPE_WEBHOOK_SECRET: str = "whsec_your_stripe_webhook_secret"
    PAYPAL_ENABLED: bool = False
    PAYPAL_CLIENT_ID: str = "your_paypal_sandbox_client_id"
    PAYPAL_CLIENT_SECRET: str = "your_paypal_sandbox_client_secret"
    PAYPAL_MODE: str = "sandbox"

    GOOGLE_ENABLED: bool = False
    GOOGLE_CLIENT_ID: str = "your-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "your-google-client-secret"
    GITHUB_ENABLED: bool = False
    GITHUB_CLIENT_ID: str = "your-github-client-id"
    GITHUB_CLIENT_SECRET: str = "your-github-client-secret"
    FACEBOOK_ENABLED: bool = False
    FACEBOOK_CLIENT_ID: str = "your-facebook-client-id"
    FACEBOOK_CLIENT_SECRET: str = "your-facebook-client-secret"
    SOCIAL_AUTH_REDIRECT_URL: str = "http://localhost:3000/auth/callback"

    ANALYTICS_ENABLED: bool = False
    ANALYTICS_PROVIDER: str = "posthog"
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"
    MIXPANEL_PROJECT_TOKEN: str = ""
    MIXPANEL_API_SECRET: str = ""
    MIXPANEL_API_HOST: str = "https://api.mixpanel.com"

    @field_validator(
        "DEBUG",
        "TESTING",
        "SECURE_COOKIES",
        "FEATURE_AUTH",
        "FEATURE_MULTITENANCY",
        "FEATURE_NOTIFICATIONS",
        "FEATURE_WEBSOCKETS",
        "FEATURE_FINANCE",
        "FEATURE_ANALYTICS",
        "FEATURE_SOCIAL_AUTH",
        "FEATURE_MAPS",
        "EMAIL_ENABLED",
        "PUSH_ENABLED",
        "SMS_ENABLED",
        "ANALYTICS_ENABLED",
        "KHALTI_ENABLED",
        "ESEWA_ENABLED",
        "STRIPE_ENABLED",
        "PAYPAL_ENABLED",
        "GOOGLE_ENABLED",
        "GITHUB_ENABLED",
        "FACEBOOK_ENABLED",
        "OSM_MAPS_ENABLED",
        "GOOGLE_MAPS_ENABLED",
        "LOG_SQL_QUERIES",
        "S3_USE_PATH_STYLE",
        mode="before",
    )
    @classmethod
    def parse_bool_flags(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False
        return value

    @field_validator("PASSWORD_PEPPER", mode="before")
    @classmethod
    def assemble_password_pepper(cls, value: str | None, info: ValidationInfo) -> str:
        if isinstance(value, str) and value:
            return value
        return info.data.get("SECRET_KEY") or "supersecretkey"

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, value: str | None, info: ValidationInfo) -> str:
        if isinstance(value, str) and value:
            return value
        data = info.data
        password = data.get("REDIS_PASSWORD")
        if password:
            return (
                f"redis://:{password}@{data.get('REDIS_HOST')}:"
                f"{data.get('REDIS_PORT')}/{data.get('REDIS_DB')}"
            )
        return (
            f"redis://{data.get('REDIS_HOST')}:"
            f"{data.get('REDIS_PORT')}/{data.get('REDIS_DB')}"
        )

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, value: str | None, info: ValidationInfo) -> str:
        if isinstance(value, str) and value:
            return value
        data = info.data
        return "memory://" if data.get("DEBUG", True) else str(data.get("REDIS_URL"))

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, value: str | None, info: ValidationInfo) -> str:
        if isinstance(value, str) and value:
            return value
        data = info.data
        return "cache+memory://" if data.get("DEBUG", True) else str(data.get("REDIS_URL"))

    @field_validator("CELERY_TASK_ALWAYS_EAGER", mode="before")
    @classmethod
    def assemble_celery_task_always_eager(
        cls,
        value: bool | str | None,
        info: ValidationInfo,
    ) -> bool:
        if isinstance(value, str):
            parsed = cls.parse_bool_flags(value)
            if isinstance(parsed, bool):
                return parsed
        if isinstance(value, bool):
            return value
        return bool(info.data.get("DEBUG", True))

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, value: str | list[str]
    ) -> list[str] | list[Union[str, AnyHttpUrl]]:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return value
        raise ValueError("Invalid CORS origins format")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, value: str | None, info: ValidationInfo) -> str:
        if isinstance(value, str) and value:
            return value
        data = info.data
        if data.get("DEBUG", True):
            return f"sqlite+aiosqlite:///./{data.get('POSTGRES_DB')}.db"
        return (
            f"postgresql+asyncpg://{data.get('POSTGRES_USER')}:"
            f"{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_SERVER')}/"
            f"{data.get('POSTGRES_DB')}"
        )

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_sync_db_connection(cls, value: str | None, info: ValidationInfo) -> str:
        if isinstance(value, str) and value:
            return value
        data = info.data
        if data.get("DEBUG", True):
            return f"sqlite:///./{data.get('POSTGRES_DB')}.db"
        return (
            f"postgresql://{data.get('POSTGRES_USER')}:"
            f"{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_SERVER')}/"
            f"{data.get('POSTGRES_DB')}"
        )

    @field_validator(
        "EMAIL_FALLBACK_PROVIDERS",
        "PUSH_FALLBACK_PROVIDERS",
        "SMS_FALLBACK_PROVIDERS",
        "LOG_OUTPUTS",
        "TRUSTED_HOSTS",
        "PROXY_TRUSTED_HOSTS",
        "FORWARDED_ALLOW_IPS",
        "WS_ALLOWED_ORIGINS",
        mode="before",
    )
    @classmethod
    def parse_provider_lists(cls, value: str | list[str] | None) -> list[str]:
        return _parse_csv(value)

    @field_validator("COOKIE_SAMESITE", mode="before")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        return _normalize_same_site(value)

    @field_validator("STORAGE_BACKEND", mode="before")
    @classmethod
    def validate_storage_backend(cls, value: str) -> str:
        return _normalize_storage_backend(value)

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        return value.strip().lower()

    @property
    def media_base_url(self) -> str:
        if self.MEDIA_BASE_URL:
            return self.MEDIA_BASE_URL.rstrip("/")
        if self.STORAGE_BACKEND == "s3" and self.S3_BUCKET:
            if self.S3_ENDPOINT_URL:
                endpoint = self.S3_ENDPOINT_URL.rstrip("/")
                if self.S3_USE_PATH_STYLE:
                    return f"{endpoint}/{self.S3_BUCKET}"
                parsed = urlparse(endpoint)
                if parsed.scheme and parsed.netloc:
                    return (
                        f"{parsed.scheme}://{self.S3_BUCKET}.{parsed.netloc}"
                        f"{parsed.path.rstrip('/')}"
                    )
                return endpoint
            return f"https://{self.S3_BUCKET}.s3.{self.S3_REGION}.amazonaws.com"
        return f"{self.SERVER_HOST.rstrip('/')}{self.MEDIA_URL.rstrip('/')}"


SETTING_FIELD_NAMES = frozenset(Settings.model_fields.keys())
_environment_settings = Settings()


def get_environment_settings_snapshot() -> dict[str, str | None]:
    snapshot = _environment_settings.model_dump()
    return {
        key: serialize_setting_value(snapshot[key])
        for key in sorted(SETTING_FIELD_NAMES)
    }


def _get_explicit_environment_values() -> dict[str, Any]:
    snapshot = _environment_settings.model_dump()
    return {
        key: snapshot[key]
        for key in _environment_settings.model_fields_set
        if key in SETTING_FIELD_NAMES
    }


def build_effective_settings(
    database_rows: Iterable[Mapping[str, Any]] | None = None,
) -> Settings:
    merged_values = _get_explicit_environment_values()
    for row in database_rows or ():
        key = str(row.get("key", "")).strip()
        if key not in SETTING_FIELD_NAMES or key in NON_RUNTIME_EDITABLE_SETTING_KEYS:
            continue
        if not row.get("is_runtime_editable", True):
            continue
        if row.get("use_db_value") and row.get("db_value") is not None:
            merged_values[key] = row["db_value"]
    return Settings(**merged_values)


def _load_general_setting_rows() -> list[dict[str, Any]]:
    from sqlalchemy import create_engine, inspect, text

    try:
        engine = create_engine(_environment_settings.SYNC_DATABASE_URL)
    except Exception:
        return []

    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            if GENERAL_SETTINGS_TABLE_NAME not in inspector.get_table_names():
                return []
            result = connection.execute(
                text(
                    f"""
                    SELECT key, db_value, use_db_value, is_runtime_editable
                    FROM {GENERAL_SETTINGS_TABLE_NAME}
                    """
                )
            )
            return [dict(row._mapping) for row in result]
    except Exception:
        return []
    finally:
        engine.dispose()


class DatabaseBackedSettings:
    def __init__(self, environment_settings: Settings):
        object.__setattr__(self, "_environment_settings", environment_settings)
        object.__setattr__(self, "_current_settings", environment_settings)
        object.__setattr__(self, "_manual_overrides", {})
        object.__setattr__(self, "_loaded_from_database", False)
        object.__setattr__(self, "_lock", Lock())

    def _refresh_from_database(self, force: bool = False) -> None:
        if self._loaded_from_database and not force:
            return
        with self._lock:
            if self._loaded_from_database and not force:
                return
            object.__setattr__(
                self,
                "_current_settings",
                build_effective_settings(_load_general_setting_rows()),
            )
            object.__setattr__(self, "_loaded_from_database", True)

    def refresh_from_database(self, force: bool = False) -> None:
        self._refresh_from_database(force=force)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self._refresh_from_database()
        data = self._current_settings.model_dump(*args, **kwargs)
        data.update(self._manual_overrides)
        return data

    def __getattr__(self, name: str) -> Any:
        self._refresh_from_database()
        if name in self._manual_overrides:
            return self._manual_overrides[name]
        return getattr(self._current_settings, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        self._manual_overrides[name] = value

    def __delattr__(self, name: str) -> None:
        if name in self._manual_overrides:
            del self._manual_overrides[name]
            return
        raise AttributeError(name)

    def __repr__(self) -> str:
        return f"DatabaseBackedSettings({self.model_dump()!r})"


settings = DatabaseBackedSettings(_environment_settings)


OAUTH_PROVIDERS: dict[str, dict[str, Any]] = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
        "extra_params": {"access_type": "online", "response_type": "code"},
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "emails_url": "https://api.github.com/user/emails",
        "scope": "read:user user:email",
        "extra_params": {},
    },
    "facebook": {
        "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email,picture",
        "scope": "email,public_profile",
        "extra_params": {"response_type": "code"},
    },
}
