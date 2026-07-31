import asyncio
import tempfile

from datetime import datetime
from datetime import timedelta
from pathlib import Path

import pytest

from sqlalchemy import text

from apps.api.v1.models.log_entry_model import LogEntryModel
from apps.api.v1.models.server_model import ServerModel
from apps.services.nginx_log_parser import NginxLogParser
from tests.consts import BASE_API_URL

NEW_LINES = (
    '192.168.1.200 - - [25/Dec/2024:11:00:01 +0300] "GET /health HTTP/1.1" '
    '200 12 "-" "curl/8.4.0"\n'
    '192.168.1.201 - - [25/Dec/2024:11:00:02 +0300] "GET /metrics HTTP/1.1" '
    '200 34 "-" "curl/8.4.0"\n'
)


@pytest.mark.integration
class TestFullWorkflow:
    """Интеграционные тесты полного рабочего процесса."""

    @pytest.fixture
    def sample_log_file(self):
        """Создает временный файл с логами для тестирования."""
        log_content = """192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"
192.168.1.101 - - [25/Dec/2024:10:30:16 +0300] "POST /api/login HTTP/1.1" 401 567 "https://example.com/login" "Mozilla/5.0"
192.168.1.102 - - [25/Dec/2024:10:30:17 +0300] "GET /static/css/style.css HTTP/1.1" 200 2345 "https://example.com" "Mozilla/5.0"
192.168.1.103 - - [25/Dec/2024:10:30:18 +0300] "GET /api/products HTTP/1.1" 404 123 "https://example.com/products" "Mozilla/5.0"
192.168.1.104 - - [25/Dec/2024:10:30:19 +0300] "POST /api/orders HTTP/1.1" 500 789 "https://example.com/checkout" "Mozilla/5.0"
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_file = Path(f.name)

        yield temp_file

        temp_file.unlink(missing_ok=True)

    @pytest.fixture(autouse=True)
    async def clean_tables(self, session):
        """Каждый тест класса начинает с пустых таблиц: фикстура схемы живёт на класс."""
        await session.execute(
            text('TRUNCATE nginx_parser_schema.log_entry_model, nginx_parser_schema.server_model')
        )
        await session.commit()

    @pytest.mark.asyncio
    async def test_full_log_parsing_workflow(self, sample_log_file, session):
        """Тест полного процесса парсинга логов."""
        server = ServerModel(
            id=101,
            name='test-server',
            description='Test server for integration tests',
            ip_address='192.168.1.1',
        )
        session.add(server)
        await session.commit()

        parser = NginxLogParser(str(sample_log_file), server_id=101)

        parsed_entries = []
        with open(sample_log_file) as f:
            for line in f:
                parsed = await parser.parse_log_line(line.strip())
                if parsed:
                    parsed_entries.append(parsed)

        assert len(parsed_entries) == 5

        for entry_data in parsed_entries:
            log_entry = LogEntryModel(**entry_data)
            session.add(log_entry)
        await session.commit()

        stmt = text('SELECT COUNT(*) FROM nginx_parser_schema.log_entry_model')
        result = await session.execute(stmt)
        count = result.scalar()
        assert count == 5

        stmt = text(
            'SELECT status, remote_addr, uri '
            'FROM nginx_parser_schema.log_entry_model ORDER BY timestamp'
        )
        result = await session.execute(stmt)
        entries = result.fetchall()

        assert entries[0][0] == 200  # status
        assert entries[0][1] == '192.168.1.100'  # remote_addr
        assert entries[0][2] == '/api/users'  # uri

        assert entries[1][0] == 401
        assert entries[1][1] == '192.168.1.101'
        assert entries[1][2] == '/api/login'

    @pytest.mark.asyncio
    async def test_analytics_workflow(self, auth_client, session):
        """Тест полного процесса аналитики."""
        now = datetime.now()

        server = ServerModel(
            id=101,
            name='analytics-test-server',
            description='Server for analytics tests',
            ip_address='192.168.1.1',
        )
        session.add(server)
        await session.commit()

        log_entries = [
            LogEntryModel(
                server_id=101,
                timestamp=now - timedelta(minutes=10),
                remote_addr='192.168.1.100',
                method='GET',
                uri='/api/users',
                http_version='HTTP/1.1',
                status=200,
                size=1234,
                referrer='https://example.com',
                user_agent='Mozilla/5.0',
            ),
            LogEntryModel(
                server_id=101,
                timestamp=now - timedelta(minutes=9),
                remote_addr='192.168.1.100',  # Тот же IP
                method='GET',
                uri='/api/users',
                http_version='HTTP/1.1',
                status=200,
                size=1234,
                referrer='https://example.com',
                user_agent='Mozilla/5.0',
            ),
            LogEntryModel(
                server_id=101,
                timestamp=now - timedelta(minutes=8),
                remote_addr='192.168.1.101',
                method='POST',
                uri='/api/login',
                http_version='HTTP/1.1',
                status=401,
                size=567,
                referrer='https://example.com/login',
                user_agent='Mozilla/5.0',
            ),
            LogEntryModel(
                server_id=101,
                timestamp=now - timedelta(minutes=7),
                remote_addr='192.168.1.102',
                method='GET',
                uri='/api/products',
                http_version='HTTP/1.1',
                status=404,
                size=123,
                referrer='https://example.com/products',
                user_agent='Mozilla/5.0',
            ),
            LogEntryModel(
                server_id=101,
                timestamp=now - timedelta(minutes=6),
                remote_addr='192.168.1.103',
                method='POST',
                uri='/api/orders',
                http_version='HTTP/1.1',
                status=500,
                size=789,
                referrer='https://example.com/checkout',
                user_agent='Mozilla/5.0',
            ),
        ]

        for entry in log_entries:
            session.add(entry)
        await session.commit()

        response = await auth_client.get(f'{BASE_API_URL}/analytics/traffic?hours=1')
        assert response.status_code == 200
        traffic_data = response.json()
        assert traffic_data['total_requests'] == 5
        assert traffic_data['unique_ips'] == 4  # 4 уникальных IP
        assert traffic_data['period_hours'] == 1

        response = await auth_client.get(f'{BASE_API_URL}/analytics/status-codes?hours=1')
        assert response.status_code == 200
        status_data = response.json()
        status_counts = {item['status']: item['count'] for item in status_data}
        assert status_counts[200] == 2  # 2 успешных запроса
        assert status_counts[401] == 1
        assert status_counts[404] == 1
        assert status_counts[500] == 1

        response = await auth_client.get(f'{BASE_API_URL}/analytics/top-ips?limit=10&hours=1')
        assert response.status_code == 200
        ips_data = response.json()
        assert ips_data[0]['ip'] == '192.168.1.100'
        assert ips_data[0]['requests'] == 2

        response = await auth_client.get(f'{BASE_API_URL}/analytics/errors?hours=1')
        assert response.status_code == 200
        errors_data = response.json()
        assert len(errors_data) == 3  # 401, 404, 500
        error_statuses = {item['status'] for item in errors_data}
        assert 401 in error_statuses
        assert 404 in error_statuses
        assert 500 in error_statuses

    @pytest.mark.asyncio
    async def test_real_time_monitoring_simulation(self, sample_log_file, session):
        """Симуляция мониторинга в реальном времени."""
        server = ServerModel(
            id=101,
            name='realtime-test-server',
            description='Server for real-time monitoring tests',
            ip_address='192.168.1.1',
        )
        session.add(server)
        await session.commit()

        parser = NginxLogParser(str(sample_log_file), server_id=101)

        async def consume() -> int:
            saved = 0
            async for log_data in parser.monitor_log_file():
                await parser.save_log_entry(log_data)
                saved += 1
                if saved >= 2:
                    return saved
            return saved

        consumer = asyncio.create_task(consume())
        await asyncio.sleep(0.2)

        with open(sample_log_file, 'a') as f:
            f.write(NEW_LINES)
            f.flush()

        saved = await asyncio.wait_for(consumer, timeout=10)
        assert saved == 2

        stmt = text('SELECT COUNT(*) FROM nginx_parser_schema.log_entry_model')
        result = await session.execute(stmt)
        count = result.scalar()
        assert count == 2  # Минимум 5 записей

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, sample_log_file, session):
        """Тест обработки ошибок в полном процессе."""
        server = ServerModel(
            id=101,
            name='error-test-server',
            description='Server for error handling tests',
            ip_address='192.168.1.1',
        )
        session.add(server)
        await session.commit()

        parser = NginxLogParser(str(sample_log_file), server_id=101)

        invalid_lines = [
            'invalid log line',
            '192.168.1.100 - - invalid format',
            '',
            '   ',
            '192.168.1.100 - - [invalid timestamp] "GET / HTTP/1.1" 200 1234 "-" "-"',
        ]

        for line in invalid_lines:
            result = await parser.parse_log_line(line)
            assert result is None  # Невалидные строки должны возвращать None

        valid_error_lines = [
            '192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 404 1234 "https://example.com" "Mozilla/5.0"',
            '192.168.1.101 - - [25/Dec/2024:10:30:16 +0300] "POST /api/login HTTP/1.1" 500 567 "https://example.com/login" "Mozilla/5.0"',
        ]

        for line in valid_error_lines:
            result = await parser.parse_log_line(line)
            assert result is not None
            assert result['status'] >= 400  # Это должны быть ошибки

    @pytest.mark.asyncio
    async def test_performance_workflow(self, session):
        """Тест производительности с большим количеством данных."""
        server = ServerModel(
            id=101,
            name='performance-test-server',
            description='Server for performance tests',
            ip_address='192.168.1.1',
        )
        session.add(server)
        await session.commit()

        now = datetime.now()
        log_entries = []

        for i in range(100):  # 100 записей
            log_entries.append(
                LogEntryModel(
                    server_id=101,
                    timestamp=now - timedelta(minutes=i),
                    remote_addr=f'192.168.1.{i % 10}',  # 10 уникальных IP
                    method='GET' if i % 2 == 0 else 'POST',
                    uri=f'/api/endpoint/{i}',
                    http_version='HTTP/1.1',
                    status=200 if i % 10 != 0 else 404,  # 10% ошибок
                    size=1000 + i,
                    referrer='https://example.com',
                    user_agent='Mozilla/5.0',
                )
            )

        for entry in log_entries:
            session.add(entry)
        await session.commit()

        stmt = text(
            'SELECT COUNT(*) FROM nginx_parser_schema.log_entry_model WHERE server_id = 101'
        )
        result = await session.execute(stmt)
        count = result.scalar()
        assert count >= 100

        stmt = text(
            'SELECT status, COUNT(*) AS count '
            'FROM nginx_parser_schema.log_entry_model '
            'WHERE server_id = 101 '
            'GROUP BY status ORDER BY count DESC'
        )
        result = await session.execute(stmt)
        status_stats = result.fetchall()

        statuses = {row[0] for row in status_stats}
        assert 200 in statuses
        assert 404 in statuses
