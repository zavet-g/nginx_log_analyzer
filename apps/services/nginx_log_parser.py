import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

import aiofiles
from loguru import logger

from apps.api.v1.models.log_entry_model import LogEntryModel
from apps.api.v1.models.server_model import ServerModel
from apps.db.session import connector


class NginxLogParser:
    """Парсер логов nginx в реальном времени."""
    
    def __init__(self, log_file_path: str, server_id: int = 1):
        self.log_file_path = Path(log_file_path)
        self.server_id = server_id
        self.position = 0
        self.log_pattern = re.compile(
            r'(?P<remote_addr>\S+) - - \[(?P<timestamp>[^\]]+)\] '
            r'"(?P<method>\S+) (?P<uri>\S+) (?P<http_version>[^"]+)" '
            r'(?P<status>\d{3}) (?P<size>\d+) "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"'
        )
    
    async def parse_log_line(self, line: str) -> dict | None:
        """Парсит одну строку лога nginx."""
        match = self.log_pattern.match(line.strip())
        if not match:
            return None
            
        data = match.groupdict()
        
        try:
            # Парсим timestamp
            timestamp_str = data['timestamp']
            if ' +' in timestamp_str:
                timestamp_str = timestamp_str.replace(' +', ' +')
            elif ' -' in timestamp_str:
                timestamp_str = timestamp_str.replace(' -', ' -')
                
            parsed_time = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            
            return {
                'server_id': self.server_id,
                'timestamp': parsed_time,
                'remote_addr': data['remote_addr'],
                'method': data['method'],
                'uri': data['uri'],
                'http_version': data['http_version'],
                'status': int(data['status']),
                'size': int(data['size']),
                'referrer': data['referrer'] if data['referrer'] != '-' else None,
                'user_agent': data['user_agent'] if data['user_agent'] != '-' else None,
            }
        except (ValueError, KeyError) as e:
            logger.warning(f"Ошибка парсинга строки: {line.strip()}, ошибка: {e}")
            return None
    
    async def monitor_log_file(self) -> AsyncGenerator[dict, None]:
        """Мониторит файл логов в реальном времени."""
        if not self.log_file_path.exists():
            logger.error(f"Файл логов не найден: {self.log_file_path}")
            return
            
        # Начинаем с конца файла для мониторинга новых записей
        self.position = self.log_file_path.stat().st_size
        
        while True:
            try:
                current_size = self.log_file_path.stat().st_size
                
                if current_size < self.position:
                    # Файл был перезаписан (log rotation)
                    self.position = 0
                
                if current_size > self.position:
                    async with aiofiles.open(self.log_file_path, 'r', encoding='utf-8') as f:
                        await f.seek(self.position)
                        new_lines = await f.read()
                        
                        for line in new_lines.splitlines():
                            if line.strip():
                                parsed_data = await self.parse_log_line(line)
                                if parsed_data:
                                    yield parsed_data
                    
                    self.position = current_size
                
                await asyncio.sleep(1)  # Проверяем каждую секунду
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга логов: {e}")
                await asyncio.sleep(5)  # Пауза при ошибке
    
    async def save_log_entry(self, log_data: dict) -> None:
        """Сохраняет запись лога в базу данных."""
        try:
            async with connector.get_pg_session_cm() as db_session:
                log_entry = LogEntryModel(**log_data)
                db_session.add(log_entry)
                await db_session.commit()
                logger.debug(f"Сохранена запись лога: {log_data['remote_addr']} - {log_data['method']} {log_data['uri']}")
        except Exception as e:
            logger.error(f"Ошибка сохранения лога: {e}")


async def start_log_monitoring(log_file_path: str, server_id: int = 1) -> None:
    """Запускает мониторинг логов nginx."""
    parser = NginxLogParser(log_file_path, server_id)
    logger.info(f"Запуск мониторинга логов: {log_file_path}")
    
    async for log_data in parser.monitor_log_file():
        await parser.save_log_entry(log_data) 