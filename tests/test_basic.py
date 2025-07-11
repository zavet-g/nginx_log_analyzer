"""Базовые тесты без зависимости от базы данных."""

import pytest
from apps.utils.enums.env_enum import EnvEnum
from apps.utils.enums.log_level_enum import LogLevelEnum


def test_env_enum():
    """Тест перечисления окружений."""
    assert EnvEnum.PYTEST.value == "PYTEST"
    assert EnvEnum.PROD.value == "PROD"
    assert EnvEnum.LOCAL.value == "LOCAL"
    assert EnvEnum.STAGE.value == "STAGE"


def test_log_level_enum():
    """Тест перечисления уровней логирования."""
    assert LogLevelEnum.DEBUG == "DEBUG"
    assert LogLevelEnum.INFO == "INFO"
    assert LogLevelEnum.WARNING == "WARNING"
    assert LogLevelEnum.ERROR == "ERROR"
    assert LogLevelEnum.CRITICAL == "CRITICAL"


def test_basic_imports():
    """Тест базовых импортов."""
    try:
        from apps.utils.health_check import health_check_router, default_health_check
        assert callable(default_health_check)
    except ImportError:
        pytest.skip("health_check не доступен")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 