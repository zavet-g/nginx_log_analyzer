from pathlib import Path

import pytest


@pytest.mark.asyncio
class TestStaticFiles:
    """Тесты для статических файлов."""

    async def test_static_files_exist(self):
        """Проверяет, что статические файлы существуют."""
        static_dir = Path('apps/static')
        assert static_dir.exists(), 'Директория apps/static не существует'

        index_file = static_dir / 'index.html'
        assert index_file.exists(), 'Файл apps/static/index.html не существует'

    async def test_index_html_content(self):
        """Проверяет содержимое index.html."""
        index_file = Path('apps/static/index.html')

        with open(index_file, encoding='utf-8') as f:
            content = f.read()

        assert '<title>Nginx Log Analyzer - Дашборд</title>' in content
        assert '📊 Nginx Log Analyzer' in content
        assert 'chart.js' in content.lower()  # Библиотека для графиков
        assert 'loadDashboard()' in content  # Функция загрузки данных

        assert '/api/analytics/traffic' in content
        assert '/api/analytics/status-codes' in content
        assert '/api/analytics/top-ips' in content
        assert '/api/analytics/top-urls' in content
        assert '/api/analytics/errors' in content
        assert '/api/analytics/time-series' in content

    async def test_static_files_structure(self):
        """Проверяет структуру статических файлов."""
        static_dir = Path('apps/static')

        assert static_dir.is_dir()

        index_file = static_dir / 'index.html'
        assert index_file.is_file()

        assert index_file.stat().st_size > 1024

    async def test_html_validity(self):
        """Проверяет валидность HTML."""
        index_file = Path('apps/static/index.html')

        with open(index_file, encoding='utf-8') as f:
            content = f.read()

        assert '<!DOCTYPE html>' in content
        assert '<html' in content
        assert '<head>' in content
        assert '<body>' in content
        assert '</html>' in content

        assert content.count('<div') == content.count('</div>')
        assert content.count('<script') == content.count('</script>')
        assert content.count('<style') == content.count('</style>')

    async def test_css_styles(self):
        """Проверяет наличие CSS стилей."""
        index_file = Path('apps/static/index.html')

        with open(index_file, encoding='utf-8') as f:
            content = f.read()

        css_classes = [
            'container',
            'header',
            'stats-grid',
            'stat-card',
            'chart-container',
            'table-container',
            'refresh-btn',
        ]

        for css_class in css_classes:
            assert f'class="{css_class}"' in content or f"class='{css_class}'" in content

    async def test_javascript_functions(self):
        """Проверяет наличие JavaScript функций."""
        index_file = Path('apps/static/index.html')

        with open(index_file, encoding='utf-8') as f:
            content = f.read()

        js_functions = ['initCharts', 'loadDashboard', 'formatBytes']

        for function in js_functions:
            assert f'function {function}' in content

    async def test_responsive_design(self):
        """Проверяет наличие адаптивного дизайна."""
        index_file = Path('apps/static/index.html')

        with open(index_file, encoding='utf-8') as f:
            content = f.read()

        assert '@media' in content
        assert 'max-width' in content

        assert 'viewport' in content
        assert 'width=device-width' in content

    async def test_external_dependencies(self):
        """Проверяет внешние зависимости."""
        index_file = Path('apps/static/index.html')

        with open(index_file, encoding='utf-8') as f:
            content = f.read()

        assert 'cdn.jsdelivr.net/npm/chart.js' in content

        assert 'https://' in content
