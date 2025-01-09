# YandexART Telegram Bot

Telegram бот для генерации изображений с использованием YandexART API. Бот позволяет генерировать изображения по текстовому описанию.

## Особенности
- 🚀 Асинхронная обработка запросов
- 🎨 Интеграция с YandexART API
- 📁 Автоматическое обновление IAM токенов
- 📁 Автоматическая очистка временных файлов
- 📝 Подробное логирование
- 💬 Простой и понятный интерфейс

## Требования
- Python 3.8+
- Yandex Cloud аккаунт
- Telegram Bot Token

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd img_gen_bot
```

2. Создайте и активируйте виртуальное окружение:
```bash
# Создание
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройка окружения:
   - Создайте файл `.env` в корневой директории
   - Добавьте следующие переменные:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
YANDEX_OAUTH_TOKEN=your_oauth_token
YANDEX_FOLDER_ID=your_folder_id
```

## Получение токенов

### Telegram Bot Token:
1. Откройте @BotFather в Telegram
2. Создайте нового бота командой /newbot
3. Следуйте инструкциям и получите токен

### Yandex Cloud:
1. Создайте аккаунт в [Yandex Cloud](https://cloud.yandex.ru/)
2. Получите OAuth токен:
   - Перейдите на [страницу OAuth-токена](https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855fa7bec2fb)
   - После авторизации скопируйте токен из URL (параметр access_token)
   - Токен начинается с "y0_Ag..."
3. Найдите Folder ID в настройках облака

## Запуск

Запуск бота из корневой директории проекта:
```bash
PYTHONPATH=. python app/bot.py
```

## Использование

1. Найдите бота в Telegram по имени
2. Отправьте команду `/start` для начала работы
3. Отправьте текстовое описание желаемого изображения
4. Дождитесь результата

## Структура проекта
```
img_gen_bot/
├── app/
│   ├── __init__.py
│   ├── bot.py           # Основной файл бота
│   └── image_generator.py  # Модуль генерации изображений
├── requirements.txt     # Зависимости
├── .env                # Конфигурация (не включена в репозиторий)
├── logs/               # Логи (создается автоматически)
└── temp/               # Временные файлы (создается автоматически)
```

## Логирование
- Логи бота сохраняются в `logs/bot.log`
- Логи генератора в `logs/image_generator.log`
- Режим логирования: перезапись при каждом запуске

## Безопасность
- Не храните токены в коде
- Используйте .env файл
- Добавьте .env в .gitignore
- OAuth токен используется для автоматического получения IAM токенов

## Лицензия
MIT
