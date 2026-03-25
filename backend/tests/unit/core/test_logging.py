from src.apps.core.config import settings
from src.apps.core.logging import get_enabled_log_outputs


class TestLoggingOutputs:
    def test_web_output_implies_database_persistence(self):
        settings.LOG_OUTPUTS = ["web", "file"]
        try:
            outputs = get_enabled_log_outputs()
            assert outputs == {"web", "database", "file"}
        finally:
            del settings.LOG_OUTPUTS

