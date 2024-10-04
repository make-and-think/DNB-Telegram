from telegram import Update
from telegram.ext import ContextTypes
from .utils import convert_to_square_webp, send_to_api
import logging
from config.config import settings

logger = logging.getLogger(__name__)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "Я работаю только в групповых чатах.")  ## TODO USE https://github.com/solaluset/i18nice
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    webp_buffer = convert_to_square_webp(image_bytes)

    api_response = send_to_api(webp_buffer)

    if api_response is None:
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке изображения. Попробуйте позже.")  ## TODO USE https://github.com/solaluset/i18nice
        return

    # Обработка ответа API
    ratings = api_response.get('ratings', {})
    general_tags = api_response.get('general_tags', {})

    if not ratings or not general_tags:
        await update.message.reply_text(
            "Извините, не удалось получить информацию об изображении.")  ## TODO USE https://github.com/solaluset/i18nice
        return

    # Проверка qe_value
    qe_value = ratings.get('questionable', 0) + ratings.get('explicit', 0)
    qe_threshold = settings.qe_threshold

    if qe_value > qe_threshold:
        reply_message = f"Ваше сообщение будет удалено из-за превышения NSFW {qe_value} > {qe_threshold}"  ## TODO USE https://github.com/solaluset/i18nice
        await update.message.reply_text(reply_message)
        await update.message.delete()
        return

    # Проверка tag_value
    tag_threshold = settings.tag_threshold
    banned_tags = settings.banned_tags
    for tag, score in general_tags.items():
        if tag in banned_tags and score > tag_threshold:
            reply_message = f"Ваше сообщение будет удалено из-за запрещенного тега: {tag} ({score:.2f} > {tag_threshold})"  ## TODO USE https://github.com/solaluset/i18nice
            await update.message.reply_text(reply_message)
            await update.message.delete()
            return

    # Если изображение прошло все проверки, отправляем информацию о нем
    ratings_str = "\n".join([f"{rating}: {score:.2f}" for rating, score in ratings.items()])
    tags_str = ", ".join(
        [f"{tag} ({score:.2f})" for tag, score in sorted(general_tags.items(), key=lambda x: x[1], reverse=True)])

    reply_message = (
        f"Рейтинги изображения:\n{ratings_str}\n\n"
        f"Теги: {tags_str}"
    )  ## TODO USE https://github.com/solaluset/i18nice

    if len(reply_message) > 4096:
        parts = [reply_message[i:i + 4096] for i in range(0, len(reply_message), 4096)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(reply_message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Я работаю только в групповых чатах.")
        return
    ## TODO USE https://github.com/solaluset/i18nice
    await update.message.reply_text(
        "Привет! Я бот для обработки и анализа изображений. Я работаю только в групповых чатах.")


async def set_qe_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        ## TODO USE https://github.com/solaluset/i18nice
        new_threshold = float(context.args[0])
        if 0 <= new_threshold <= 1:
            settings.set('qe_threshold', new_threshold)
            await update.message.reply_text(f"Новый порог qe_threshold установлен: {new_threshold}")
        else:
            await update.message.reply_text("Пожалуйста, укажите значение от 0 до 1.")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите корректное числовое значение.")


async def set_tag_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        new_threshold = float(context.args[0])
        if 0 <= new_threshold <= 1:
            settings.set('tag_threshold', new_threshold)
            ## TODO USE https://github.com/solaluset/i18nice
            await update.message.reply_text(f"Новый порог tag_threshold установлен: {new_threshold}")
        else:
            await update.message.reply_text("Пожалуйста, укажите значение от 0 до 1.")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите корректное числовое значение.")


async def add_banned_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        new_tag = context.args[0].lower()
        banned_tags = settings.get('banned_tags', [])
        if new_tag not in banned_tags:
            banned_tags.append(new_tag)
            settings.set('banned_tags', banned_tags)
            ## TODO USE https://github.com/solaluset/i18nice
            await update.message.reply_text(f"Тег '{new_tag}' добавлен в список запрещенных.")
        else:
            await update.message.reply_text(f"Тег '{new_tag}' уже в списке запрещенных.")
    except IndexError:
        await update.message.reply_text("Пожалуйста, укажите тег для добавления.")


async def remove_banned_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        tag_to_remove = context.args[0].lower()
        banned_tags = settings.get('banned_tags', [])
        if tag_to_remove in banned_tags:
            banned_tags.remove(tag_to_remove)
            settings.set('banned_tags', banned_tags)
            ## TODO USE https://github.com/solaluset/i18nice
            await update.message.reply_text(f"Тег '{tag_to_remove}' удален из списка запрещенных.")
        else:
            await update.message.reply_text(f"Тег '{tag_to_remove}' не найден в списке запрещенных.")
    except IndexError:
        await update.message.reply_text("Пожалуйста, укажите тег для удаления.")


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if user.status in ['creator', 'administrator']:
        return True
    ## TODO USE https://github.com/solaluset/i18nice
    await update.message.reply_text("Эта команда доступна только администраторам.")
    return False
