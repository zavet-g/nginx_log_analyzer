import tempfile

from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from apps.cli_commands import main
from apps.cli_commands import start_monitoring

LOG_SAMPLE = (
    '192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" '
    '200 1234 "https://example.com" "Mozilla/5.0"\n'
    '192.168.1.101 - - [25/Dec/2024:10:30:16 +0300] "POST /api/login HTTP/1.1" '
    '401 567 "https://example.com/login" "Mozilla/5.0"\n'
)


@pytest.fixture
def sample_log_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(LOG_SAMPLE)
        temp_file = Path(f.name)
    yield temp_file
    temp_file.unlink(missing_ok=True)


@pytest.mark.cli
class TestStartMonitoring:
    """Тесты корутины запуска мониторинга."""

    async def test_delegates_to_monitoring_service(self, sample_log_file):
        with patch(
            'apps.cli_commands.start_log_monitoring', new_callable=AsyncMock
        ) as mock_monitor:
            await start_monitoring(str(sample_log_file), server_id=1)

        mock_monitor.assert_awaited_once_with(str(sample_log_file), 1)

    async def test_keyboard_interrupt_is_not_an_error(self, sample_log_file):
        with patch(
            'apps.cli_commands.start_log_monitoring',
            new_callable=AsyncMock,
            side_effect=KeyboardInterrupt,
        ):
            await start_monitoring(str(sample_log_file), server_id=1)

    async def test_unexpected_failure_exits_with_code_1(self, sample_log_file):
        with (
            patch(
                'apps.cli_commands.start_log_monitoring',
                new_callable=AsyncMock,
                side_effect=OSError('broken pipe'),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            await start_monitoring(str(sample_log_file), server_id=1)

        assert exc_info.value.code == 1


@pytest.mark.cli
class TestMainCommand:
    """Тесты разбора аргументов и веток main()."""

    def test_monitor_runs_event_loop(self, sample_log_file):
        with (
            patch('sys.argv', ['cli_commands.py', 'monitor', str(sample_log_file)]),
            patch('apps.cli_commands.start_monitoring') as mock_start,
            patch('apps.cli_commands.asyncio.run') as mock_run,
        ):
            main()

        mock_run.assert_called_once()
        mock_start.assert_called_once_with(str(sample_log_file), 1)

    def test_monitor_exits_when_file_is_missing(self):
        with (
            patch('sys.argv', ['cli_commands.py', 'monitor', '/nonexistent/file.log']),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1

    def test_check_reads_existing_file(self, sample_log_file):
        with patch('sys.argv', ['cli_commands.py', 'check', str(sample_log_file)]):
            main()

    def test_check_exits_when_file_is_missing(self):
        with (
            patch('sys.argv', ['cli_commands.py', 'check', '/nonexistent/file.log']),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1

    def test_unknown_command_is_rejected_by_argparse(self):
        with (
            patch('sys.argv', ['cli_commands.py', 'invalid']),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 2

    def test_no_command_prints_help(self):
        with (
            patch('sys.argv', ['cli_commands.py']),
            patch('argparse.ArgumentParser.print_help') as mock_help,
        ):
            main()

        mock_help.assert_called_once()
