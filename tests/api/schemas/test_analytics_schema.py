import pytest
from datetime import datetime, timezone

from apps.api.v1.schemas.analytics_schema import (
    StatusCodeStats,
    TopIPsStats,
    TopURLsStats,
    TrafficStats,
    ErrorStats,
    TimeSeriesData
)


class TestAnalyticsSchemas:
    """Тесты для схем аналитики."""

    def test_status_code_stats_schema(self):
        """Тест схемы StatusCodeStats."""
        data = {
            'status': 200,
            'count': 150
        }
        
        stats = StatusCodeStats(**data)
        
        assert stats.status == 200
        assert stats.count == 150
        assert isinstance(stats.status, int)
        assert isinstance(stats.count, int)

    def test_top_ips_stats_schema(self):
        """Тест схемы TopIPsStats."""
        data = {
            'ip': '192.168.1.100',
            'requests': 50,
            'avg_size': 1024
        }
        
        stats = TopIPsStats(**data)
        
        assert stats.ip == '192.168.1.100'
        assert stats.requests == 50
        assert stats.avg_size == 1024
        assert isinstance(stats.ip, str)
        assert isinstance(stats.requests, int)
        assert isinstance(stats.avg_size, int)

    def test_top_urls_stats_schema(self):
        """Тест схемы TopURLsStats."""
        data = {
            'url': '/api/users',
            'requests': 25,
            'avg_size': 2048
        }
        
        stats = TopURLsStats(**data)
        
        assert stats.url == '/api/users'
        assert stats.requests == 25
        assert stats.avg_size == 2048
        assert isinstance(stats.url, str)
        assert isinstance(stats.requests, int)
        assert isinstance(stats.avg_size, int)

    def test_traffic_stats_schema(self):
        """Тест схемы TrafficStats."""
        data = {
            'total_requests': 1000,
            'total_bytes': 1024000,
            'avg_request_size': 1024,
            'unique_ips': 50,
            'period_hours': 24
        }
        
        stats = TrafficStats(**data)
        
        assert stats.total_requests == 1000
        assert stats.total_bytes == 1024000
        assert stats.avg_request_size == 1024
        assert stats.unique_ips == 50
        assert stats.period_hours == 24
        
        assert isinstance(stats.total_requests, int)
        assert isinstance(stats.total_bytes, int)
        assert isinstance(stats.avg_request_size, int)
        assert isinstance(stats.unique_ips, int)
        assert isinstance(stats.period_hours, int)

    def test_error_stats_schema(self):
        """Тест схемы ErrorStats."""
        timestamp = datetime.now(timezone.utc)
        data = {
            'status': 404,
            'url': '/api/products',
            'ip': '192.168.1.100',
            'timestamp': timestamp,
            'user_agent': 'Mozilla/5.0'
        }
        
        stats = ErrorStats(**data)
        
        assert stats.status == 404
        assert stats.url == '/api/products'
        assert stats.ip == '192.168.1.100'
        assert stats.timestamp == timestamp
        assert stats.user_agent == 'Mozilla/5.0'
        
        assert isinstance(stats.status, int)
        assert isinstance(stats.url, str)
        assert isinstance(stats.ip, str)
        assert isinstance(stats.timestamp, datetime)
        assert isinstance(stats.user_agent, str)

    def test_error_stats_schema_without_user_agent(self):
        """Тест схемы ErrorStats без user_agent."""
        timestamp = datetime.now(timezone.utc)
        data = {
            'status': 500,
            'url': '/api/orders',
            'ip': '192.168.1.101',
            'timestamp': timestamp
        }
        
        stats = ErrorStats(**data)
        
        assert stats.status == 500
        assert stats.url == '/api/orders'
        assert stats.ip == '192.168.1.101'
        assert stats.timestamp == timestamp
        assert stats.user_agent is None

    def test_time_series_data_schema(self):
        """Тест схемы TimeSeriesData."""
        timestamp = datetime.now(timezone.utc)
        data = {
            'timestamp': timestamp,
            'requests': 100,
            'bytes': 51200
        }
        
        time_series = TimeSeriesData(**data)
        
        assert time_series.timestamp == timestamp
        assert time_series.requests == 100
        assert time_series.bytes == 51200
        
        assert isinstance(time_series.timestamp, datetime)
        assert isinstance(time_series.requests, int)
        assert isinstance(time_series.bytes, int)

    def test_schemas_validation(self):
        """Тест валидации схем."""
        # Тест с валидными данными
        valid_data = {
            'status': 200,
            'count': 100
        }
        stats = StatusCodeStats(**valid_data)
        assert stats.status == 200
        
        # Тест с невалидными типами данных
        with pytest.raises(ValueError):
            StatusCodeStats(status="invalid", count="invalid")

    def test_schemas_serialization(self):
        """Тест сериализации схем."""
        timestamp = datetime.now(timezone.utc)
        
        # Создаем объекты схем
        status_stats = StatusCodeStats(status=200, count=100)
        top_ips = TopIPsStats(ip='192.168.1.100', requests=50, avg_size=1024)
        traffic = TrafficStats(
            total_requests=1000,
            total_bytes=1024000,
            avg_request_size=1024,
            unique_ips=50,
            period_hours=24
        )
        error = ErrorStats(
            status=404,
            url='/api/products',
            ip='192.168.1.100',
            timestamp=timestamp,
            user_agent='Mozilla/5.0'
        )
        time_series = TimeSeriesData(
            timestamp=timestamp,
            requests=100,
            bytes=51200
        )
        
        # Проверяем, что объекты можно сериализовать в dict
        assert status_stats.model_dump() == {'status': 200, 'count': 100}
        assert top_ips.model_dump() == {
            'ip': '192.168.1.100',
            'requests': 50,
            'avg_size': 1024
        }
        assert traffic.model_dump() == {
            'total_requests': 1000,
            'total_bytes': 1024000,
            'avg_request_size': 1024,
            'unique_ips': 50,
            'period_hours': 24
        }
        assert error.model_dump() == {
            'status': 404,
            'url': '/api/products',
            'ip': '192.168.1.100',
            'timestamp': timestamp,
            'user_agent': 'Mozilla/5.0'
        }
        assert time_series.model_dump() == {
            'timestamp': timestamp,
            'requests': 100,
            'bytes': 51200
        }

    def test_schemas_edge_cases(self):
        """Тест граничных случаев схем."""
        # Тест с нулевыми значениями
        zero_stats = StatusCodeStats(status=0, count=0)
        assert zero_stats.status == 0
        assert zero_stats.count == 0
        
        # Тест с большими значениями
        large_stats = TopIPsStats(ip='192.168.1.100', requests=999999, avg_size=999999)
        assert large_stats.requests == 999999
        assert large_stats.avg_size == 999999
        
        # Тест с пустыми строками
        empty_stats = TopURLsStats(url='', requests=0, avg_size=0)
        assert empty_stats.url == ''
        assert empty_stats.requests == 0
        assert empty_stats.avg_size == 0

    def test_schemas_inheritance(self):
        """Тест наследования от BaseSchema."""
        timestamp = datetime.now(timezone.utc)
        
        # Все схемы должны наследоваться от BaseSchema
        status_stats = StatusCodeStats(status=200, count=100)
        top_ips = TopIPsStats(ip='192.168.1.100', requests=50, avg_size=1024)
        traffic = TrafficStats(
            total_requests=1000,
            total_bytes=1024000,
            avg_request_size=1024,
            unique_ips=50,
            period_hours=24
        )
        
        # Проверяем, что у всех есть метод model_dump
        assert hasattr(status_stats, 'model_dump')
        assert hasattr(top_ips, 'model_dump')
        assert hasattr(traffic, 'model_dump')
        
        # Проверяем, что можно создать из dict
        assert StatusCodeStats.model_validate({'status': 200, 'count': 100})
        assert TopIPsStats.model_validate({
            'ip': '192.168.1.100',
            'requests': 50,
            'avg_size': 1024
        }) 