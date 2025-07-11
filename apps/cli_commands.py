import asyncio
import argparse
import sys
from pathlib import Path

from loguru import logger

from apps.services.nginx_log_parser import start_log_monitoring
from apps.settings import SETTINGS


async def start_monitoring(log_file_path: str, server_id: int = 1) -> None:
    """Запускает мониторинг логов nginx."""
    logger.info(f"Запуск мониторинга логов: {log_file_path}")
    logger.info(f"Server ID: {server_id}")
    
    try:
        await start_log_monitoring(log_file_path, server_id)
    except KeyboardInterrupt:
        logger.info("Мониторинг остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка мониторинга: {e}")
        sys.exit(1)


def main():
    """Основная функция CLI."""
    parser = argparse.ArgumentParser(description="Nginx Log Analyzer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
    
    # Команда мониторинга
    monitor_parser = subparsers.add_parser("monitor", help="Запустить мониторинг логов")
    monitor_parser.add_argument(
        "log_file", 
        help="Путь к файлу логов nginx"
    )
    monitor_parser.add_argument(
        "--server-id", 
        type=int, 
        default=1, 
        help="ID сервера (по умолчанию: 1)"
    )
    
    # Команда проверки файла
    check_parser = subparsers.add_parser("check", help="Проверить файл логов")
    check_parser.add_argument(
        "log_file", 
        help="Путь к файлу логов nginx"
    )
    
    args = parser.parse_args()
    
    if args.command == "monitor":
        log_path = Path(args.log_file)
        if not log_path.exists():
            logger.error(f"Файл логов не найден: {log_path}")
            sys.exit(1)
        
        asyncio.run(start_monitoring(str(log_path), args.server_id))
    
    elif args.command == "check":
        log_path = Path(args.log_file)
        if not log_path.exists():
            logger.error(f"Файл логов не найден: {log_path}")
            sys.exit(1)
        
        logger.info(f"Проверка файла: {log_path}")
        logger.info(f"Размер файла: {log_path.stat().st_size} байт")
        
        # Читаем несколько строк для проверки формата
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 5:  # Показываем первые 5 строк
                        break
                    logger.info(f"Строка {i+1}: {line.strip()}")
        except Exception as e:
            logger.error(f"Ошибка чтения файла: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 