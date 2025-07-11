import pytest
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime, timezone

from apps.services.nginx_log_parser import NginxLogParser


class TestNginxLogParser:
    """Тесты для парсера логов nginx."""
    
    @pytest.fixture
    def sample_log_file(self):
        """Создает временный файл с примерами логов nginx."""
        log_content = """192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
192.168.1.101 - - [25/Dec/2024:10:30:16 +0300] "POST /api/login HTTP/1.1" 401 567 "https://example.com/login" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
192.168.1.102 - - [25/Dec/2024:10:30:17 +0300] "GET /static/css/style.css HTTP/1.1" 200 2345 "https://example.com" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
invalid log line
192.168.1.103 - - [25/Dec/2024:10:30:18 +0300] "GET /api/products HTTP/1.1" 404 123 "https://example.com/products" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_file = Path(f.name)
        
        yield temp_file
        
        # Очистка
        temp_file.unlink(missing_ok=True)
    
    @pytest.fixture
    def parser(self, sample_log_file):
        """Создает экземпляр парсера."""
        return NginxLogParser(str(sample_log_file), server_id=1)
    
    def test_parser_initialization(self, parser):
        """Тест инициализации парсера."""
        assert parser.log_file_path.exists()
        assert parser.server_id == 1
        assert parser.position == 0
        assert parser.log_pattern is not None
    
    @pytest.mark.asyncio
    async def test_parse_valid_log_line(self, parser):
        """Тест парсинга валидной строки лога."""
        valid_line = '192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"'
        
        result = await parser.parse_log_line(valid_line)
        
        assert result is not None
        assert result['remote_addr'] == '192.168.1.100'
        assert result['method'] == 'GET'
        assert result['uri'] == '/api/users'
        assert result['http_version'] == 'HTTP/1.1'
        assert result['status'] == 200
        assert result['size'] == 1234
        assert result['referrer'] == 'https://example.com'
        assert result['user_agent'] == 'Mozilla/5.0'
        assert result['server_id'] == 1
        assert isinstance(result['timestamp'], datetime)
    
    @pytest.mark.asyncio
    async def test_parse_invalid_log_line(self, parser):
        """Тест парсинга невалидной строки лога."""
        invalid_line = 'invalid log line'
        
        result = await parser.parse_log_line(invalid_line)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_log_line_with_dash_values(self, parser):
        """Тест парсинга строки с дефисами в referrer и user_agent."""
        line_with_dashes = '192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 200 1234 "-" "-"'
        
        result = await parser.parse_log_line(line_with_dashes)
        
        assert result is not None
        assert result['referrer'] is None
        assert result['user_agent'] is None
    
    @pytest.mark.asyncio
    async def test_parse_log_line_with_different_timezone(self, parser):
        """Тест парсинга строки с разными часовыми поясами."""
        line_utc = '192.168.1.100 - - [25/Dec/2024:10:30:15 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "-"'
        line_minus = '192.168.1.100 - - [25/Dec/2024:10:30:15 -0500] "GET /api/users HTTP/1.1" 200 1234 "-" "-"'
        
        result_utc = await parser.parse_log_line(line_utc)
        result_minus = await parser.parse_log_line(line_minus)
        
        assert result_utc is not None
        assert result_minus is not None
        assert result_utc['timestamp'].tzinfo is not None
        assert result_minus['timestamp'].tzinfo is not None
    
    @pytest.mark.asyncio
    async def test_monitor_log_file_empty_file(self, tmp_path):
        """Тест мониторинга пустого файла."""
        empty_file = tmp_path / "empty.log"
        empty_file.touch()
        
        parser = NginxLogParser(str(empty_file))
        async for _ in parser.monitor_log_file():
            # Не должно быть записей в пустом файле
            assert False, "Не должно быть записей в пустом файле"
    
    @pytest.mark.asyncio
    async def test_monitor_log_file_nonexistent(self):
        """Тест мониторинга несуществующего файла."""
        parser = NginxLogParser("/nonexistent/file.log")
        
        # Должен корректно обработать несуществующий файл
        async for _ in parser.monitor_log_file():
            assert False, "Не должно быть записей для несуществующего файла"
    
    def test_log_pattern_matching(self, parser):
        """Тест регулярного выражения для парсинга логов."""
        test_cases = [
            {
                'line': '192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"',
                'should_match': True
            },
            {
                'line': 'invalid log line',
                'should_match': False
            },
            {
                'line': '192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "POST /api/login HTTP/1.1" 401 567 "-" "-"',
                'should_match': True
            },
            {
                'line': '127.0.0.1 - - [25/Dec/2024:10:30:15 +0300] "GET / HTTP/1.1" 200 1234 "https://example.com" "curl/7.68.0"',
                'should_match': True
            }
        ]
        
        for case in test_cases:
            match = parser.log_pattern.match(case['line'])
            if case['should_match']:
                assert match is not None, f"Должен совпадать: {case['line']}"
            else:
                assert match is None, f"Не должен совпадать: {case['line']}"
    
    @pytest.mark.asyncio
    async def test_parse_multiple_lines(self, parser):
        """Тест парсинга нескольких строк логов."""
        lines = [
            '192.168.1.100 - - [25/Dec/2024:10:30:15 +0300] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"',
            '192.168.1.101 - - [25/Dec/2024:10:30:16 +0300] "POST /api/login HTTP/1.1" 401 567 "https://example.com/login" "Mozilla/5.0"',
            'invalid line',
            '192.168.1.102 - - [25/Dec/2024:10:30:17 +0300] "GET /static/css/style.css HTTP/1.1" 200 2345 "https://example.com" "Mozilla/5.0"'
        ]
        
        results = []
        for line in lines:
            result = await parser.parse_log_line(line)
            if result:
                results.append(result)
        
        assert len(results) == 3  # 3 валидные строки
        assert results[0]['remote_addr'] == '192.168.1.100'
        assert results[1]['remote_addr'] == '192.168.1.101'
        assert results[2]['remote_addr'] == '192.168.1.102'
        assert results[0]['status'] == 200
        assert results[1]['status'] == 401
        assert results[2]['status'] == 200 