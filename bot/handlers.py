from telegram import Update
from telegram.ext import ContextTypes
from .utils import convert_to_square_webp, send_to_api
import logging
from config.config import settings

logger = logging.getLogger(__name__)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Я работаю только в групповых чатах.") ## TODO USE https://github.com/solaluset/i18nice
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    
    webp_buffer = convert_to_square_webp(image_bytes)
    
    api_response = send_to_api(webp_buffer)
    
    if api_response is None:
        await update.message.reply_text("Извините, произошла ошибка при обработке изображения. Попробуйте позже.") ## TODO USE https://github.com/solaluset/i18nice
        return

    # Обработка ответа API
    ratings = api_response.get('ratings', {})
    general_tags = api_response.get('general_tags', {})

    if not ratings or not general_tags:
        await update.message.reply_text("Извините, не удалось получить информацию об изображении.") ## TODO USE https://github.com/solaluset/i18nice
        return

    # Проверка qe_value
    qe_value = ratings.get('questionable', 0) + ratings.get('explicit', 0)
    qe_threshold = settings.qe_threshold
    
    if qe_value > qe_threshold:
        reply_message = f"Ваше сообщение будет удалено из-за превышения NSFW" ## TODO USE https://github.com/solaluset/i18nice
        await update.message.reply_text(reply_message)
        await update.message.delete()
        return

    # Проверка tag_value
    tag_threshold = settings.tag_threshold
    banned_tags = settings.banned_tags
    for tag, score in general_tags.items():
        if tag in banned_tags and score > tag_threshold:
            reply_message = f"Ваше сообщение будет удалено из-за запрещенного тега: {tag} ({score:.2f} > {tag_threshold})" ## TODO USE https://github.com/solaluset/i18nice
            await update.message.reply_text(reply_message)
            await update.message.delete()
            return

    # Если изображение прошло все проверки, отправляем информацию о нем
    ratings_str = "\n".join([f"{rating}: {score:.2f}" for rating, score in ratings.items()])
    tags_str = ", ".join([f"{tag} ({score:.2f})" for tag, score in sorted(general_tags.items(), key=lambda x: x[1], reverse=True)])

    reply_message = (
        f"Рейтинги изображения:\n{ratings_str}\n\n"
        f"Теги: {tags_str}"
    ) ## TODO USE https://github.com/solaluset/i18nice

    if len(reply_message) > 4096:
        parts = [reply_message[i:i+4096] for i in range(0, len(reply_message), 4096)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(reply_message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Я работаю только в групповых чатах.")
        return
    ## TODO USE https://github.com/solaluset/i18nice
    await update.message.reply_text("Привет! Я бот для обработки и анализа изображений. Я работаю только в групповых чатах.")