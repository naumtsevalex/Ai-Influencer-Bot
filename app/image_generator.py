import os
import base64
import logging
import asyncio
from pathlib import Path
from datetime import datetime

import aiohttp
from dotenv import load_dotenv

# Создаем директорию для логов перед настройкой логирования
Path("logs").mkdir(exist_ok=True)

# Базовая настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/image_generator.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
OAUTH_TOKEN = os.getenv('YANDEX_OAUTH_TOKEN')
FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')

# URL API
API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
OPERATION_URL = "https://llm.api.cloud.yandex.net/operations/"
IAM_URL = "https://iam.api.cloud.yandex.net/iam/v1/tokens"

class ImageGenerator:
    def __init__(self):
        self.headers = None
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)

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
        temp_path = self.temp_dir / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}.png"
        
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
                
                # Сохранение изображения
                await self._save_image(image_data, temp_path)
                logger.info(f"Изображение сохранено: {temp_path}")
                
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
        while True:
            async with session.get(f"{OPERATION_URL}{operation_id}", headers=self.headers) as response:
                response.raise_for_status()
                status = await response.json()
                
                if status.get('done', False):
                    if 'error' in status:
                        raise Exception(f"Ошибка генерации: {status['error']}")
                    return base64.b64decode(status['response']['image'])
                
                await asyncio.sleep(1)

    async def _save_image(self, image_data: bytes, path: Path) -> None:
        """Сохранение изображения"""
        try:
            with open(path, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            logger.error(f"Ошибка сохранения изображения: {str(e)}")
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