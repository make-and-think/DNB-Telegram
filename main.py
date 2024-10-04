import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN
from bot.handlers import handle_photo, start, set_qe_threshold, set_tag_threshold, add_banned_tag, remove_banned_tag

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
## TODO change python-telegram-bot tp Telethon
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_photo))
    
    application.add_handler(CommandHandler("set_qe_threshold", set_qe_threshold))
    application.add_handler(CommandHandler("set_tag_threshold", set_tag_threshold))
    application.add_handler(CommandHandler("add_banned_tag", add_banned_tag))
    application.add_handler(CommandHandler("remove_banned_tag", remove_banned_tag))
    
    application.run_polling()

if __name__ == '__main__':
    main()