import pytest
from pathlib import Path


@pytest.mark.asyncio
class TestStaticFiles:
    """Тесты для статических файлов."""

    async def test_static_files_exist(self):
        """Проверяет, что статические файлы существуют."""
        static_dir = Path("apps/static")
        assert static_dir.exists(), "Директория apps/static не существует"
        
        index_file = static_dir / "index.html"
        assert index_file.exists(), "Файл apps/static/index.html не существует"

    async def test_index_html_content(self):
        """Проверяет содержимое index.html."""
        index_file = Path("apps/static/index.html")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем основные элементы
        assert '<title>Nginx Log Analyzer - Дашборд</title>' in content
        assert '📊 Nginx Log Analyzer' in content
        assert 'Chart.js' in content  # Библиотека для графиков
        assert 'loadDashboard()' in content  # Функция загрузки данных
        
        # Проверяем API endpoints
        assert '/api/analytics/traffic' in content
        assert '/api/analytics/status-codes' in content
        assert '/api/analytics/top-ips' in content
        assert '/api/analytics/top-urls' in content
        assert '/api/analytics/errors' in content
        assert '/api/analytics/time-series' in content

    async def test_static_files_structure(self):
        """Проверяет структуру статических файлов."""
        static_dir = Path("apps/static")
        
        # Проверяем, что это директория
        assert static_dir.is_dir()
        
        # Проверяем, что index.html - это файл
        index_file = static_dir / "index.html"
        assert index_file.is_file()
        
        # Проверяем размер файла (должен быть больше 1KB)
        assert index_file.stat().st_size > 1024

    async def test_html_validity(self):
        """Проверяет валидность HTML."""
        index_file = Path("apps/static/index.html")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем основные HTML теги
        assert '<!DOCTYPE html>' in content
        assert '<html' in content
        assert '<head>' in content
        assert '<body>' in content
        assert '</html>' in content
        
        # Проверяем, что все открытые теги закрыты
        assert content.count('<div') == content.count('</div>')
        assert content.count('<script') == content.count('</script>')
        assert content.count('<style') == content.count('</style>')

    async def test_css_styles(self):
        """Проверяет наличие CSS стилей."""
        index_file = Path("apps/static/index.html")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие CSS классов
        css_classes = [
            'container',
            'header',
            'stats-grid',
            'stat-card',
            'chart-container',
            'table-container',
            'refresh-btn'
        ]
        
        for css_class in css_classes:
            assert f'class="{css_class}"' in content or f"class='{css_class}'" in content

    async def test_javascript_functions(self):
        """Проверяет наличие JavaScript функций."""
        index_file = Path("apps/static/index.html")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие основных функций
        js_functions = [
            'initCharts',
            'loadDashboard',
            'formatBytes'
        ]
        
        for function in js_functions:
            assert f'function {function}' in content

    async def test_responsive_design(self):
        """Проверяет наличие адаптивного дизайна."""
        index_file = Path("apps/static/index.html")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие медиа-запросов
        assert '@media' in content
        assert 'max-width' in content
        
        # Проверяем наличие viewport meta тега
        assert 'viewport' in content
        assert 'width=device-width' in content

    async def test_external_dependencies(self):
        """Проверяет внешние зависимости."""
        index_file = Path("apps/static/index.html")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие Chart.js
        assert 'cdn.jsdelivr.net/npm/chart.js' in content
        
        # Проверяем, что используется HTTPS
        assert 'https://' in content 