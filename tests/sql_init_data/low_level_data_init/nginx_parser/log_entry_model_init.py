from datetime import UTC
from datetime import datetime
from datetime import timedelta

from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import Insert

from apps.api.v1.models.log_entry_model import LogEntryModel

ENTRIES_PER_SERVER = 20
SERVER_COUNT = 5

CLIENT_IPS = ('10.0.0.11', '10.0.0.12', '10.0.0.13', '10.0.0.14')
REQUESTS = (
    ('GET', '/', 200, 1024),
    ('GET', '/api/v1/servers', 200, 2048),
    ('POST', '/api/v1/log-entries', 201, 512),
    ('GET', '/static/app.css', 304, 0),
    ('GET', '/api/v1/missing', 404, 128),
    ('POST', '/api/v1/servers', 401, 96),
    ('GET', '/api/v1/analytics/traffic', 500, 256),
)
USER_AGENTS = (
    'Mozilla/5.0 (X11; Linux x86_64)',
    'curl/8.4.0',
    'python-httpx/0.27.0',
)

OLDEST_ENTRY_AGE = timedelta(hours=20)
ENTRY_INTERVAL = timedelta(minutes=5)


def get_log_entry_model_init() -> list[Insert]:
    """Создаёт SQL-выражение для вставки записей access-лога.

    Данные генерируются детерминированно, без чтения внешнего файла: набор
    покрывает успешные ответы, редирект и три вида ошибок, распределён по
    серверам и укладывается в промежуток от 20 до 2 часов назад. Записи
    заведомо старше часа, поэтому не попадают в выборки тестов, которые
    добавляют собственные данные и фильтруют их по последнему часу.
    """
    start = datetime.now(tz=UTC) - OLDEST_ENTRY_AGE
    log_entries = []

    for index in range(ENTRIES_PER_SERVER * SERVER_COUNT):
        method, uri, status, size = REQUESTS[index % len(REQUESTS)]
        log_entries.append(
            {
                'timestamp': start + ENTRY_INTERVAL * index,
                'remote_addr': CLIENT_IPS[index % len(CLIENT_IPS)],
                'method': method,
                'uri': uri,
                'http_version': 'HTTP/1.1',
                'status': status,
                'size': size,
                'referrer': 'https://example.com/' if index % 3 else None,
                'user_agent': USER_AGENTS[index % len(USER_AGENTS)],
                'server_id': index // ENTRIES_PER_SERVER + 1,
            }
        )

    return [insert(LogEntryModel).values(log_entries)]
