import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import BotCommand
from config import BOT_TOKEN
from bot.handlers import handle_photo, start, set_qe_threshold, set_tag_threshold, add_banned_tag, remove_banned_tag, get_localization

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
## TODO add slash commands description
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_photo))
    
    application.add_handler(CommandHandler("set_qe_threshold", set_qe_threshold))
    application.add_handler(CommandHandler("set_tag_threshold", set_tag_threshold))
    application.add_handler(CommandHandler("add_banned_tag", add_banned_tag))
    application.add_handler(CommandHandler("remove_banned_tag", remove_banned_tag))
    
    # Добавление описаний команд
    async def set_commands(app):
        localization = get_localization()
        commands = [
            BotCommand("start", localization.start_command_description),
            BotCommand("set_qe_threshold", localization.set_qe_threshold_description),
            BotCommand("set_tag_threshold", localization.set_tag_threshold_description),
            BotCommand("add_banned_tag", localization.add_banned_tag_description),
            BotCommand("remove_banned_tag", localization.remove_banned_tag_description)
        ]
        await app.bot.set_my_commands(commands)
    
    application.post_init = set_commands
    
    application.run_polling()

if __name__ == '__main__':
    main()