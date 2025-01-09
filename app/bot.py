import os
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from app.image_generator import ImageGenerator
from app.utils import setup_logger, get_env_vars

# Настройка логирования
logger = setup_logger(__file__)

# Загрузка переменных окружения
TELEGRAM_TOKEN, _, _ = get_env_vars()

# Создание генератора изображений
generator = ImageGenerator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот для генерации изображений с помощью YandexART.\n"
        "Просто отправь мне описание желаемого изображения, и я его сгенерирую!\n"
        "Например: 'Космический корабль в стиле киберпанк'"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🎨 Как использовать бота:\n"
        "1. Просто отправьте текстовое описание желаемого изображения\n"
        "2. Подождите немного, пока изображение генерируется\n"
        "3. Получите готовое изображение\n\n"
        "💡 Советы:\n"
        "- Описывайте изображение подробно\n"
        "- Используйте художественные термины\n"
        "- Указывайте желаемый стиль"
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    # Отправляем сообщение о начале генерации
    message = await update.message.reply_text("🎨 Начинаю генерацию изображения...")
    
    try:
        # Генерируем изображение
        prompt = update.message.text
        image_path = await generator.generate_image(prompt)
        
        # Отправляем изображение
        await message.edit_text("✨ Загружаю изображение...")
        with open(image_path, 'rb') as image:
            await update.message.reply_photo(
                photo=image,
                caption=f"🎨 Промпт: {prompt}"
            )
        await message.delete()
        
        # Удаляем временный файл
        os.remove(image_path)
        
    except Exception as e:
        logger.error(f"Ошибка при генерации: {str(e)}")
        await message.edit_text(f"❌ Произошла ошибка: {str(e)}")

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    # Запускаем бота
    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 