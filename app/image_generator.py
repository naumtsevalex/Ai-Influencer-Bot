import os
import base64
import asyncio
import shutil
from pathlib import Path
from datetime import datetime

import aiohttp

from app.utils import setup_logger, get_env_vars, ensure_dir

# Настройка логирования
logger = setup_logger(__file__)

# Загрузка переменных окружения
_, OAUTH_TOKEN, FOLDER_ID = get_env_vars()

# URL API
API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
OPERATION_URL = "https://llm.api.cloud.yandex.net/operations/"
IAM_URL = "https://iam.api.cloud.yandex.net/iam/v1/tokens"

class ImageGenerator:
    def __init__(self):
        self.headers = None
        # Создаем структуру временных директорий
        self.temp_dir = ensure_dir("temp")
        self.temp_images = ensure_dir(self.temp_dir / "generated_images")
        logger.info(f"Инициализация генератора. Директория для изображений: {self.temp_images}")

    async def _get_iam_token(self) -> str:
        """Получение IAM токена через OAuth токен"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                IAM_URL,
                json={"yandexPassportOauthToken": OAUTH_TOKEN}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result['iamToken']

    async def _ensure_valid_token(self):
        """Проверка и обновление IAM токена"""
        try:
            if self.headers is None:
                iam_token = await self._get_iam_token()
                self.headers = {
                    "Authorization": f"Bearer {iam_token}",
                    "Content-Type": "application/json"
                }
                logger.info("Получен новый IAM токен")
        except Exception as e:
            logger.error(f"Ошибка получения IAM токена: {str(e)}")
            raise

    async def generate_image(self, prompt: str) -> str:
        """Генерация изображения по промпту"""
        await self._ensure_valid_token()
        
        # Создаем путь для временного файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = os.urandom(4).hex()
        temp_path = self.temp_images / f"temp_{timestamp}_{file_id}.png"
        logger.info(f"Создаем изображение по пути: {temp_path}")
        
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    # Запрос на генерацию
                    operation_id = await self._request_generation(session, prompt)
                except aiohttp.ClientResponseError as e:
                    if e.status == 401:  # Unauthorized - токен протух
                        logger.info("IAM токен устарел, получаем новый")
                        iam_token = await self._get_iam_token()
                        self.headers["Authorization"] = f"Bearer {iam_token}"
                        operation_id = await self._request_generation(session, prompt)
                    else:
                        raise

                logger.info(f"Получен ID операции: {operation_id}")
                
                # Ожидание и получение результата
                image_data = await self._wait_for_result(session, operation_id)
                logger.info("Получены данные изображения")
                
                # Сохранение изображения во временный файл
                await self._save_image(image_data, temp_path)
                logger.info(f"Изображение сохранено во временный файл: {temp_path}")
                
                return str(temp_path)

        except Exception as e:
            logger.error(f"Ошибка генерации: {str(e)}")
            raise

    async def _request_generation(self, session: aiohttp.ClientSession, prompt: str) -> str:
        """Отправка запроса на генерацию"""
        payload = {
            "modelUri": f"art://{FOLDER_ID}/yandex-art/latest",
            "generationOptions": {
                "seed": "1863",
                "aspectRatio": {
                    "widthRatio": "1",
                    "heightRatio": "1"
                }
            },
            "messages": [
                {
                    "weight": "1",
                    "text": prompt
                }
            ]
        }
        
        logger.info(f"Отправляем запрос с промптом: {prompt}")
        async with session.post(API_URL, headers=self.headers, json=payload) as response:
            response.raise_for_status()
            result = await response.json()
            return result['id']

    async def _wait_for_result(self, session: aiohttp.ClientSession, operation_id: str) -> bytes:
        """Ожидание результата генерации"""
        start_time = datetime.now()
        timeout = 60  # таймаут в секундах
        
        while True:
            if (datetime.now() - start_time).seconds > timeout:
                raise TimeoutError(f"Превышено время ожидания ({timeout} сек)")
                
            async with session.get(f"{OPERATION_URL}{operation_id}", headers=self.headers) as response:
                response.raise_for_status()
                status = await response.json()
                
                if status.get('done', False):
                    if 'error' in status:
                        raise Exception(f"Ошибка генерации: {status['error']}")
                    
                    # Получаем размер изображения до декодирования
                    image_base64 = status['response']['image']
                    size_mb = len(image_base64) * 3/4 / (1024 * 1024)  # примерный размер после декодирования
                    logger.info(f"Получено изображение (ожидаемый размер: {size_mb:.2f} МБ)")
                    
                    return base64.b64decode(image_base64)
                
                logger.info(f"Ожидание генерации... прошло {(datetime.now() - start_time).seconds} сек")
                await asyncio.sleep(1)

    async def _save_image(self, image_data: bytes, path: Path) -> None:
        """Сохранение изображения"""
        try:
            # Убеждаемся, что директория существует перед сохранением
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Проверена директория: {path.parent}")
            
            # Сохраняем изображение
            with open(path, 'wb') as f:
                f.write(image_data)
            
            # Проверяем, что файл существует и его размер
            if path.exists():
                size_mb = len(image_data) / (1024 * 1024)  # Конвертируем в МБ
                logger.info(f"Изображение успешно сохранено: {path} (размер: {size_mb:.2f} МБ)")
            else:
                raise FileNotFoundError(f"Файл не найден после сохранения: {path}")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения изображения {path}: {str(e)}")
            raise

async def main():
    """Тестовый запуск генератора"""
    generator = ImageGenerator()
    prompt = input("Введите описание изображения: ")
    
    try:
        output_path = await generator.generate_image(prompt)
        print(f"Готово! Изображение сохранено в: {output_path}")
    except Exception as e:
        print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 