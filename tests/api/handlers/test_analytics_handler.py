import pytest
from datetime import datetime, timedelta
from sqlalchemy import insert

from apps.api.v1.models.log_entry_model import LogEntryModel
from apps.api.v1.models.server_model import ServerModel
from tests.consts import BASE_API_URL
from tests.sql_init_data.base_data_tree import base_parser_tree


@pytest.mark.handlers
@pytest.mark.parametrize(
    'db_init_pre_build',
    [base_parser_tree],
    indirect=True,
)
class TestAnalyticsHandler:
    """Тесты для аналитических эндпоинтов."""

    async def test_get_status_code_stats(self, auth_client, db_init_pre_build):
        """Тест получения статистики по статус кодам."""
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/status-codes?hours=24'
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:  # Если есть данные
            for item in data:
                assert 'status' in item
                assert 'count' in item
                assert isinstance(item['status'], int)
                assert isinstance(item['count'], int)

    async def test_get_top_ips(self, auth_client, db_init_pre_build):
        """Тест получения топ IP адресов."""
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/top-ips?limit=5&hours=24'
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:  # Если есть данные
            for item in data:
                assert 'ip' in item
                assert 'requests' in item
                assert 'avg_size' in item
                assert isinstance(item['ip'], str)
                assert isinstance(item['requests'], int)
                assert isinstance(item['avg_size'], int)

    async def test_get_top_urls(self, auth_client, db_init_pre_build):
        """Тест получения топ URL."""
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/top-urls?limit=5&hours=24'
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:  # Если есть данные
            for item in data:
                assert 'url' in item
                assert 'requests' in item
                assert 'avg_size' in item
                assert isinstance(item['url'], str)
                assert isinstance(item['requests'], int)
                assert isinstance(item['avg_size'], int)

    async def test_get_traffic_stats(self, auth_client, db_init_pre_build):
        """Тест получения статистики трафика."""
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/traffic?hours=24'
        )

        assert response.status_code == 200
        data = response.json()
        
        assert 'total_requests' in data
        assert 'total_bytes' in data
        assert 'avg_request_size' in data
        assert 'unique_ips' in data
        assert 'period_hours' in data
        
        assert isinstance(data['total_requests'], int)
        assert isinstance(data['total_bytes'], int)
        assert isinstance(data['avg_request_size'], int)
        assert isinstance(data['unique_ips'], int)
        assert isinstance(data['period_hours'], int)

    async def test_get_error_stats(self, auth_client, db_init_pre_build):
        """Тест получения статистики ошибок."""
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/errors?hours=24'
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:  # Если есть данные
            for item in data:
                assert 'status' in item
                assert 'url' in item
                assert 'ip' in item
                assert 'timestamp' in item
                assert isinstance(item['status'], int)
                assert isinstance(item['url'], str)
                assert isinstance(item['ip'], str)
                # Проверяем, что это ошибки (4xx, 5xx)
                assert item['status'] >= 400

    async def test_get_time_series_data(self, auth_client, db_init_pre_build):
        """Тест получения временных рядов."""
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/time-series?hours=24'
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:  # Если есть данные
            for item in data:
                assert 'timestamp' in item
                assert 'requests' in item
                assert 'bytes' in item
                assert isinstance(item['requests'], int)
                assert isinstance(item['bytes'], int)

    async def test_analytics_with_different_hours(self, auth_client, db_init_pre_build):
        """Тест аналитики с разными периодами времени."""
        for hours in [1, 6, 12, 24]:
            response = await auth_client.get(
                f'{BASE_API_URL}/analytics/traffic?hours={hours}'
            )
            assert response.status_code == 200
            data = response.json()
            assert data['period_hours'] == hours

    async def test_analytics_with_different_limits(self, auth_client, db_init_pre_build):
        """Тест аналитики с разными лимитами."""
        for limit in [1, 5, 10, 20]:
            response = await auth_client.get(
                f'{BASE_API_URL}/analytics/top-ips?limit={limit}&hours=24'
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= limit

    async def test_analytics_unauthorized(self, client, db_init_pre_build):
        """Тест доступа к аналитике без авторизации."""
        endpoints = [
            '/analytics/status-codes',
            '/analytics/top-ips',
            '/analytics/top-urls',
            '/analytics/traffic',
            '/analytics/errors',
            '/analytics/time-series'
        ]
        
        for endpoint in endpoints:
            response = await client.get(f'{BASE_API_URL}{endpoint}')
            assert response.status_code == 401  # Unauthorized


@pytest.mark.handlers
class TestAnalyticsWithCustomData:
    """Тесты аналитики с кастомными данными."""

    async def test_analytics_with_recent_data(self, auth_client, session):
        """Тест аналитики с недавними данными."""
        # Создаем тестовые данные
        now = datetime.now()
        
        # Добавляем сервер
        server = ServerModel(
            id=1,
            name='test-server',
            description='Test server',
            ip_address='192.168.1.1'
        )
        session.add(server)
        await session.commit()
        
        # Добавляем логи с разными статус кодами
        log_entries = [
            LogEntryModel(
                server_id=1,
                timestamp=now - timedelta(minutes=5),
                remote_addr='192.168.1.100',
                method='GET',
                uri='/api/users',
                http_version='HTTP/1.1',
                status=200,
                size=1234,
                referrer='https://example.com',
                user_agent='Mozilla/5.0'
            ),
            LogEntryModel(
                server_id=1,
                timestamp=now - timedelta(minutes=4),
                remote_addr='192.168.1.101',
                method='POST',
                uri='/api/login',
                http_version='HTTP/1.1',
                status=401,
                size=567,
                referrer='https://example.com/login',
                user_agent='Mozilla/5.0'
            ),
            LogEntryModel(
                server_id=1,
                timestamp=now - timedelta(minutes=3),
                remote_addr='192.168.1.102',
                method='GET',
                uri='/api/products',
                http_version='HTTP/1.1',
                status=404,
                size=123,
                referrer='https://example.com/products',
                user_agent='Mozilla/5.0'
            ),
            LogEntryModel(
                server_id=1,
                timestamp=now - timedelta(minutes=2),
                remote_addr='192.168.1.103',
                method='POST',
                uri='/api/orders',
                http_version='HTTP/1.1',
                status=500,
                size=789,
                referrer='https://example.com/checkout',
                user_agent='Mozilla/5.0'
            )
        ]
        
        for entry in log_entries:
            session.add(entry)
        await session.commit()
        
        # Тестируем статистику трафика
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/traffic?hours=1'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['total_requests'] == 4
        assert data['unique_ips'] == 4
        
        # Тестируем статус коды
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/status-codes?hours=1'
        )
        assert response.status_code == 200
        data = response.json()
        status_codes = {item['status'] for item in data}
        assert 200 in status_codes
        assert 401 in status_codes
        assert 404 in status_codes
        assert 500 in status_codes
        
        # Тестируем ошибки
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/errors?hours=1'
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # 401, 404, 500
        
        # Тестируем топ IP
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/top-ips?limit=10&hours=1'
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # 4 уникальных IP
        
        # Тестируем топ URL
        response = await auth_client.get(
            f'{BASE_API_URL}/analytics/top-urls?limit=10&hours=1'
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # 4 уникальных URL 