from telegram import Update
from telegram.ext import ContextTypes
from .utils import convert_to_square_webp, send_to_api
import logging

logger = logging.getLogger(__name__)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Я работаю только в групповых чатах.")
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    
    webp_buffer = convert_to_square_webp(image_bytes)
    
    api_response = send_to_api(webp_buffer)
    
    if api_response is None:
        await update.message.reply_text("Извините, произошла ошибка при обработке изображения. Попробуйте позже.")
        return

    # Обработка ответа API
    ratings = api_response.get('ratings', {})
    general_tags = api_response.get('general_tags', {})

    if not ratings or not general_tags:
        await update.message.reply_text("Извините, не удалось получить информацию об изображении.")
        return

    # Определение основного рейтинга
    main_rating = max(ratings, key=ratings.get)
    main_rating_score = ratings[main_rating]

    # Формирование списка основных тегов
    top_tags = sorted(general_tags.items(), key=lambda x: x[1], reverse=True)[:3]
    tags_str = ", ".join([f"{tag} ({score:.2f})" for tag, score in top_tags])

    reply_message = (
        f"Рейтинг изображения: {main_rating} ({main_rating_score:.2f})\n"
        f"Основные теги: {tags_str}"
    )

    await update.message.reply_text(reply_message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Я работаю только в групповых чатах.")
        return

    await update.message.reply_text("Привет! Я бот для обработки и анализа изображений. Я работаю только в групповых чатах.")