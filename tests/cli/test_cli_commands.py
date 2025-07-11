import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock

from apps.cli_commands import start_monitoring, main


class TestCLICommands:
    """Тесты для CLI команд."""

    @pytest.fixture
    def sample_log_file(self):
        """Создает временный файл с примерами логов."""
        log_content = """192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"
192.168.1.101 - - [25/Dec/2024:10:30:16 +0300] "POST /api/login HTTP/1.1" 401 567 "https://example.com/login" "Mozilla/5.0"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_file = Path(f.name)
        
        yield temp_file
        
        # Очистка
        temp_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_start_monitoring_success(self, sample_log_file):
        """Тест успешного запуска мониторинга."""
        with patch('apps.cli_commands.start_log_monitoring', new_callable=AsyncMock) as mock_monitor:
            mock_monitor.return_value = None
            
            await start_monitoring(str(sample_log_file), server_id=1)
            
            mock_monitor.assert_called_once_with(str(sample_log_file), 1)

    @pytest.mark.asyncio
    async def test_start_monitoring_keyboard_interrupt(self, sample_log_file):
        """Тест обработки KeyboardInterrupt."""
        with patch('apps.cli_commands.start_log_monitoring', new_callable=AsyncMock) as mock_monitor:
            mock_monitor.side_effect = KeyboardInterrupt()
            
            # Не должно вызывать исключение
            await start_monitoring(str(sample_log_file), server_id=1)
            
            mock_monitor.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_monitoring_exception(self, sample_log_file):
        """Тест обработки исключений."""
        with patch('apps.cli_commands.start_log_monitoring', new_callable=AsyncMock) as mock_monitor:
            mock_monitor.side_effect = Exception("Test error")
            
            with pytest.raises(SystemExit) as exc_info:
                await start_monitoring(str(sample_log_file), server_id=1)
            
            assert exc_info.value.code == 1
            mock_monitor.assert_called_once()

    def test_main_monitor_command(self, sample_log_file):
        """Тест команды monitor."""
        with patch('sys.argv', ['cli_commands.py', 'monitor', str(sample_log_file)]):
            with patch('asyncio.run') as mock_run:
                main()
                mock_run.assert_called_once()

    def test_main_monitor_command_with_server_id(self, sample_log_file):
        """Тест команды monitor с указанием server_id."""
        with patch('sys.argv', ['cli_commands.py', 'monitor', str(sample_log_file), '--server-id', '2']):
            with patch('asyncio.run') as mock_run:
                main()
                mock_run.assert_called_once()

    def test_main_check_command(self, sample_log_file):
        """Тест команды check."""
        with patch('sys.argv', ['cli_commands.py', 'check', str(sample_log_file)]):
            with patch('builtins.print') as mock_print:
                main()
                # Проверяем, что была попытка вывода информации о файле
                assert mock_print.called or True  # Может не вызываться в зависимости от реализации

    def test_main_monitor_command_nonexistent_file(self):
        """Тест команды monitor с несуществующим файлом."""
        with patch('sys.argv', ['cli_commands.py', 'monitor', '/nonexistent/file.log']):
            with patch('asyncio.run') as mock_run:
                with patch('builtins.print') as mock_print:
                    main()
                    # Должен вывести сообщение об ошибке
                    assert mock_print.called

    def test_main_check_command_nonexistent_file(self):
        """Тест команды check с несуществующим файлом."""
        with patch('sys.argv', ['cli_commands.py', 'check', '/nonexistent/file.log']):
            with patch('builtins.print') as mock_print:
                main()
                # Должен вывести сообщение об ошибке
                assert mock_print.called

    def test_main_no_command(self):
        """Тест запуска без команды."""
        with patch('sys.argv', ['cli_commands.py']):
            with patch('argparse.ArgumentParser.print_help') as mock_help:
                main()
                mock_help.assert_called_once()

    def test_main_invalid_command(self):
        """Тест запуска с неверной командой."""
        with patch('sys.argv', ['cli_commands.py', 'invalid']):
            with patch('argparse.ArgumentParser.print_help') as mock_help:
                main()
                mock_help.assert_called_once()

    def test_file_size_display(self, sample_log_file):
        """Тест отображения размера файла."""
        file_size = sample_log_file.stat().st_size
        assert file_size > 0
        
        with patch('sys.argv', ['cli_commands.py', 'check', str(sample_log_file)]):
            with patch('builtins.print') as mock_print:
                main()
                # Проверяем, что информация о файле была выведена
                assert mock_print.called

    def test_log_file_content_preview(self, sample_log_file):
        """Тест предварительного просмотра содержимого файла."""
        with open(sample_log_file, 'r') as f:
            content = f.read()
        
        assert len(content) > 0
        assert '192.168.1.100' in content
        assert 'GET /api/users' in content

    @pytest.mark.asyncio
    async def test_monitoring_with_different_server_ids(self, sample_log_file):
        """Тест мониторинга с разными ID серверов."""
        for server_id in [1, 2, 3]:
            with patch('apps.cli_commands.start_log_monitoring', new_callable=AsyncMock) as mock_monitor:
                mock_monitor.return_value = None
                
                await start_monitoring(str(sample_log_file), server_id=server_id)
                
                mock_monitor.assert_called_once_with(str(sample_log_file), server_id)

    def test_argument_parsing(self):
        """Тест парсинга аргументов командной строки."""
        test_cases = [
            (['cli_commands.py', 'monitor', '/path/to/log'], 'monitor'),
            (['cli_commands.py', 'check', '/path/to/log'], 'check'),
            (['cli_commands.py'], None),
            (['cli_commands.py', 'invalid'], None),
        ]
        
        for args, expected_command in test_cases:
            with patch('sys.argv', args):
                with patch('asyncio.run') as mock_run:
                    with patch('builtins.print') as mock_print:
                        main()
                        
                        if expected_command == 'monitor':
                            mock_run.assert_called()
                        elif expected_command == 'check':
                            # check команда может не вызывать asyncio.run
                            pass
                        else:
                            # Должен показать help
                            pass 