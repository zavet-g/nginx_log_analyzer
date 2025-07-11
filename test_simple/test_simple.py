"""Очень простой тест для проверки работы pytest."""

import sys
import os


def test_python_version():
    """Тест версии Python."""
    assert sys.version_info >= (3, 8), "Требуется Python 3.8+"


def test_current_directory():
    """Тест текущей директории."""
    assert os.path.exists("."), "Текущая директория должна существовать"


def test_basic_math():
    """Тест базовой математики."""
    assert 2 + 2 == 4, "2 + 2 должно равняться 4"
    assert 3 * 3 == 9, "3 * 3 должно равняться 9"


def test_string_operations():
    """Тест операций со строками."""
    text = "Hello, World!"
    assert len(text) == 13, "Длина строки должна быть 13"
    assert "Hello" in text, "Строка должна содержать 'Hello'"


if __name__ == "__main__":
    print("Запуск простых тестов...")
    test_python_version()
    test_current_directory()
    test_basic_math()
    test_string_operations()
    print("Все тесты прошли успешно!") 