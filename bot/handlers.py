from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from .utils import convert_to_square_webp, send_to_api
import logging
from config.config import settings
from dynaconf import Dynaconf

logger = logging.getLogger(__name__)

default_language = settings.get('default_language', 'en') # TODO move to settings.py
localization_file = settings.localization_files[default_language] # TODO move to settings.py
localization = Dynaconf(settings_files=[localization_file])  # TODO move to settings.py


def get_localization(): # TODO move to settings.py
    return localization


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(localization.group_only_message)
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    # TODO Проверка файлов.

    webp_buffer = convert_to_square_webp(image_bytes)

    api_response = send_to_api(webp_buffer)

    if api_response is None:
        await update.message.reply_text(
            localization.error_processing_image)
        return

    # Обработка ответа API
    ratings = api_response.get('ratings', {})
    general_tags = api_response.get('general_tags', {})

    if not ratings or not general_tags:
        await update.message.reply_text(
            localization.failed_to_get_image_info)
        return

    # Проверка qe_value
    qe_value = ratings.get('questionable', 0) + ratings.get('explicit', 0)
    qe_threshold = settings.qe_threshold

    if qe_value > qe_threshold:
        reply_message = localization.message_deleted_nsfw.format(qe_value=qe_value, qe_threshold=qe_threshold)
        await update.message.reply_text(reply_message)
        await update.message.delete()
        return

    # Проверка tag_value
    tag_threshold = settings.tag_threshold  # TODO У каждого тега свой показатель tag_threshold
    banned_tags = settings.banned_tags
    for tag, score in general_tags.items():
        if tag in banned_tags and score > tag_threshold:
            reply_message = localization.message_deleted_banned_tag.format(tag=tag, score=score,
                                                                           tag_threshold=tag_threshold)
            await update.message.reply_text(reply_message)
            await update.message.delete()
            return

    # Если изображение прошло все проверки, отправляем информацию о нем
    # TODO Если изображение прошло все проверки то зачем написать почему мы его удалили?
    ratings_str = "\n".join([f"{rating}: {score:.2f}" for rating, score in ratings.items()])
    tags_str = ", ".join(
        [f"{tag} ({score:.2f})" for tag, score in sorted(general_tags.items(), key=lambda x: x[1], reverse=True)])

    reply_message = (
        f"{localization.image_ratings}\n{ratings_str}\n\n"
        f"{localization.image_tags} {tags_str}"
    )

    if len(reply_message) > 4096:
        parts = [reply_message[i:i + 4096] for i in range(0, len(reply_message), 4096)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(reply_message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(localization.group_only_message)
        return

    await update.message.reply_text(
        localization.start_message
    )


async def set_qe_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        new_threshold = float(context.args[0])
        if 0 <= new_threshold <= 1:
            old_threshold = settings.get('qe_threshold')
            settings.set('qe_threshold', new_threshold)
            logger.info(
                f"QE threshold changed from {old_threshold} to {new_threshold} by user {update.effective_user.id}")
            await update.message.reply_text(localization.new_qe_threshold_set.format(new_threshold=new_threshold))
        else:
            await update.message.reply_text(localization.please_specify_value_between)
    except (IndexError, ValueError):
        await update.message.reply_text(localization.please_specify_correct_value)


async def set_tag_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        new_threshold = float(context.args[0])
        if 0 <= new_threshold <= 1:
            old_threshold = settings.get('tag_threshold')
            settings.set('tag_threshold', new_threshold)
            logger.info(
                f"Tag threshold changed from {old_threshold} to {new_threshold} by user {update.effective_user.id}")
            await update.message.reply_text(localization.new_tag_threshold_set.format(new_threshold=new_threshold))
        else:
            await update.message.reply_text(localization.please_specify_value_between)
    except (IndexError, ValueError):
        await update.message.reply_text(localization.please_specify_correct_value)


async def add_banned_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        new_tag = context.args[0].lower()
        banned_tags = settings.get('banned_tags', [])
        if new_tag not in banned_tags:
            banned_tags.append(new_tag)
            settings.set('banned_tags', banned_tags)
            logger.info(f"Banned tag '{new_tag}' added by user {update.effective_user.id}")
            await update.message.reply_text(localization.tag_added_to_banned.format(new_tag=new_tag))
        else:
            await update.message.reply_text(localization.tag_already_in_banned.format(new_tag=new_tag))
    except IndexError:
        await update.message.reply_text(localization.please_specify_tag_to_add)


async def remove_banned_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    try:
        tag_to_remove = context.args[0].lower()
        banned_tags = settings.get('banned_tags', [])
        if tag_to_remove in banned_tags:
            banned_tags.remove(tag_to_remove)
            settings.set('banned_tags', banned_tags)
            logger.info(f"Banned tag '{tag_to_remove}' removed by user {update.effective_user.id}")
            await update.message.reply_text(localization.tag_removed_from_banned.format(tag_to_remove=tag_to_remove))
        else:
            await update.message.reply_text(localization.tag_not_found_in_banned.format(tag_to_remove=tag_to_remove))
    except IndexError:
        await update.message.reply_text(localization.please_specify_tag_to_remove)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if user.status in ['creator', 'administrator']:
        return True
    await update.message.reply_text(localization.admin_only_command)
    return False


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    context.user_data['language'] = lang

    await query.edit_message_text(localization.language_changed)
