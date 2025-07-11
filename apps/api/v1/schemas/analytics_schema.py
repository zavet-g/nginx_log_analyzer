from datetime import datetime
from typing import Optional

from apps.api.v1.schemas.base_schema import BaseSchema


class StatusCodeStats(BaseSchema):
    """Статистика по HTTP статус кодам."""
    status: int
    count: int


class TopIPsStats(BaseSchema):
    """Статистика по топ IP адресам."""
    ip: str
    requests: int
    avg_size: int


class TopURLsStats(BaseSchema):
    """Статистика по топ URL."""
    url: str
    requests: int
    avg_size: int


class TrafficStats(BaseSchema):
    """Общая статистика трафика."""
    total_requests: int
    total_bytes: int
    avg_request_size: int
    unique_ips: int
    period_hours: int


class ErrorStats(BaseSchema):
    """Статистика ошибок."""
    status: int
    url: str
    ip: str
    timestamp: datetime
    user_agent: Optional[str] = None


class TimeSeriesData(BaseSchema):
    """Данные временных рядов."""
    timestamp: datetime
    requests: int
    bytes: int 