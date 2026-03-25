from pathlib import Path

from src.apps.core.config import ENV_FILE_PATH, Settings, settings


class TestSettings:
    """Test application settings."""
    
    def test_project_name(self):
        """Test project name is set."""
        assert settings.PROJECT_NAME == "FastAPI Template"
    
    def test_api_version(self):
        """Test API version prefix."""
        assert settings.API_V1_STR == "/api/v1"
    
    def test_token_expiry_settings(self):
        """Test token expiry settings are configured."""
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_password_policy_settings(self):
        """Test password policy settings."""
        assert settings.PASSWORD_MIN_LENGTH >= 8
        assert isinstance(settings.PASSWORD_REQUIRE_UPPERCASE, bool)
        assert isinstance(settings.PASSWORD_REQUIRE_LOWERCASE, bool)
        assert isinstance(settings.PASSWORD_REQUIRE_DIGIT, bool)
    
    def test_security_settings(self):
        """Test security settings are configured."""
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0
        assert settings.MAX_LOGIN_ATTEMPTS > 0
        assert settings.ACCOUNT_LOCKOUT_DURATION_MINUTES > 0
    
    def test_cors_origins(self):
        """Test CORS origins are configured."""
        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
        assert len(settings.BACKEND_CORS_ORIGINS) > 0
    
    def test_database_url(self):
        """Test database URL is configured."""
        assert settings.DATABASE_URL is not None
        assert len(settings.DATABASE_URL) > 0
    
    def test_debug_mode(self):
        """Test debug mode setting."""
        assert isinstance(settings.DEBUG, bool)

    def test_logging_settings(self):
        """Test logging defaults are configured."""
        assert settings.LOG_LEVEL in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert settings.LOG_PERSIST_MIN_LEVEL in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert isinstance(settings.LOG_OUTPUTS, list)
        assert all(output in {"console", "database", "web", "file"} for output in settings.LOG_OUTPUTS)
        assert len(settings.LOG_FILE_PATH) > 0
        assert settings.LOG_RETENTION_DAYS >= 1

    def test_operational_settings(self):
        """Test new operational defaults are configured."""
        assert settings.APP_ENV in {"development", "staging", "production", "test"}
        assert settings.COOKIE_SAMESITE in {"lax", "strict", "none"}
        assert settings.STORAGE_BACKEND in {"local", "s3"}
        assert settings.DB_POOL_SIZE >= 1
        assert settings.HTTP_TIMEOUT_SECONDS > 0
        assert settings.WS_HEARTBEAT_INTERVAL_SECONDS > 0
        assert settings.WS_MAX_IDLE_SECONDS > settings.WS_HEARTBEAT_INTERVAL_SECONDS

    def test_settings_parses_operational_lists_and_booleans(self):
        parsed = Settings(
            TRUSTED_HOSTS="api.example.com,example.com",
            PROXY_TRUSTED_HOSTS="10.0.0.1,10.0.0.2",
            FORWARDED_ALLOW_IPS="127.0.0.1,::1",
            WS_ALLOWED_ORIGINS="https://app.example.com,https://admin.example.com",
            S3_USE_PATH_STYLE="true",
            COOKIE_SAMESITE="Strict",
            STORAGE_BACKEND="S3",
        )

        assert parsed.TRUSTED_HOSTS == ["api.example.com", "example.com"]
        assert parsed.PROXY_TRUSTED_HOSTS == ["10.0.0.1", "10.0.0.2"]
        assert parsed.FORWARDED_ALLOW_IPS == ["127.0.0.1", "::1"]
        assert parsed.WS_ALLOWED_ORIGINS == [
            "https://app.example.com",
            "https://admin.example.com",
        ]
        assert parsed.S3_USE_PATH_STYLE is True
        assert parsed.COOKIE_SAMESITE == "strict"
        assert parsed.STORAGE_BACKEND == "s3"

    def test_media_base_url_defaults_to_server_media_path(self):
        parsed = Settings(SERVER_HOST="https://api.example.com", MEDIA_URL="/uploads")
        assert parsed.media_base_url == "https://api.example.com/uploads"

    def test_env_file_path_points_to_backend_env(self):
        assert ENV_FILE_PATH == Path(__file__).resolve().parents[3] / ".env"
