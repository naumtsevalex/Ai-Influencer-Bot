import os
import logging
from pathlib import Path
from typing import Union
from dotenv import load_dotenv

def setup_logger(file: str) -> logging.Logger:
    """Настройка логгера для файла
    
    Args:
        file: путь к файлу (__file__)
    """
    # Создаем временную директорию и поддиректорию для логов
    temp_dir = ensure_dir("temp")
    logs_dir = ensure_dir(temp_dir / "logs")
    
    # Получаем имя файла без расширения для логгера
    name = Path(file).stem
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Форматтер для всех хендлеров
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    
    # Файловый хендлер
    file_handler = logging.FileHandler(logs_dir / f'{name}.log', mode='w')
    file_handler.setFormatter(formatter)
    
    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_env_vars() -> tuple[str, str, str]:
    """Загрузка переменных окружения"""
    load_dotenv()
    
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    oauth_token = os.getenv('YANDEX_OAUTH_TOKEN')
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    
    if not all([telegram_token, oauth_token, folder_id]):
        raise ValueError("Не все необходимые переменные окружения установлены")
    
    return telegram_token, oauth_token, folder_id

def ensure_dir(path: Union[str, Path]) -> Path:
    """Создание директории, если она не существует"""
    dir_path = Path(path)
    dir_path.mkdir(exist_ok=True)
    return dir_path 