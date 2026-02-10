import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from testbook_scraper import TestBookScraper
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

if not TOKEN or not ADMIN_CHAT_ID:
    raise ValueError("Missing required environment variables")

class TestBookBot:
    def __init__(self):
        self.scraper = TestBookScraper()
        self.application = Application.builder().token(TOKEN).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r'https://testbook\.com/.*/test-series'),
            self.handle_url
        ))
        self.application.add_handler(CallbackQueryHandler(self.handle_timer))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if str(update.effective_chat.id) != ADMIN_CHAT_ID:
                await update.message.reply_text("❌ Unauthorized access")
                return

            await update.message.reply_text(
                "📚 TestBook Scraper Bot\n\n"
                "Send me a TestBook test series URL (e.g. https://testbook.com/ssc-cgl/test-series)"
            )
        except Exception as e:
            logger.error(f"Start error: {e}")

    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            url = update.message.text
            logger.info(f"Received URL: {url}")

            keyboard = [
                [
                    InlineKeyboardButton("30 mins", callback_data=f"30|{url}"),
                    InlineKeyboardButton("60 mins", callback_data=f"60|{url}"),
                ],
                [
                    InlineKeyboardButton("90 mins", callback_data=f"90|{url}"),
                    InlineKeyboardButton("120 mins", callback_data=f"120|{url}"),
                ]
            ]

            await update.message.reply_text(
                "⏱ Select test duration:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"URL handling error: {e}")
            await update.message.reply_text("❌ Error processing URL")

    async def handle_timer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            minutes, url = query.data.split('|')
            minutes = int(minutes)
            
            await query.edit_message_text(f"⌛ Scraping {url} with {minutes} minute timer...")
            
            # Scrape and send tests
            mocks = self.scraper.scrape_test_series(url, minutes)
            if not mocks:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="❌ No mock tests found"
                )
                return

            for mock in mocks:
                try:
                    with open(mock['html_file'], 'rb') as f:
                        await context.bot.send_document(
                            chat_id=query.message.chat_id,
                            document=f,
                            filename=f"mock_test_{mock['id']}.html",
                            caption=f"📝 {mock['title']}\n⏱ {minutes} minutes"
                        )
                except Exception as e:
                    logger.error(f"Error sending test: {e}")

        except Exception as e:
            logger.error(f"Timer error: {e}")
            await query.edit_message_text("❌ Error processing request")

    def run(self):
        logger.info("Starting bot...")
        self.application.run_polling()

if __name__ == '__main__':
    try:
        bot = TestBookBot()
        bot.run()
    except Exception as e:
        logger.error(f"Bot failed: {e}")
