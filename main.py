import os
import asyncio
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from aiohttp import ClientSession

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # ID каналу, наприклад: -1001234567890
WEBAPP_URL = os.getenv("WEBAPP_URL")
CHECK_INTERVAL = 10  # Перевірка підписки кожні 10 секунд

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
user_messages = {}  # Збереження ID повідомлення з кнопкою для кожного користувача

async def check_subscription(user_id):
    """Перевіряє, чи підписаний користувач на канал."""
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    async with ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            status = data.get("result", {}).get("status", "left")
            return status in ["member", "administrator", "creator"]

async def send_webapp_button(update, context):
    """Надсилає або оновлює кнопку доступу до WebApp."""
    user_id = update.effective_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        keyboard = [[InlineKeyboardButton("Відкрити WebApp", web_app=WEBAPP_URL)]]
        text = "✅ Ви маєте доступ до WebApp."
    else:
        keyboard = [[InlineKeyboardButton("Підписатися", url=f"https://t.me/{CHANNEL_ID[4:]}")]]
        text = "❌ Ви не підписані на канал. Будь ласка, підпишіться для доступу."
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if user_id in user_messages:
        await context.bot.edit_message_text(chat_id=user_id, message_id=user_messages[user_id], text=text, reply_markup=reply_markup)
    else:
        message = await update.message.reply_text(text, reply_markup=reply_markup)
        user_messages[user_id] = message.message_id

async def start(update, context):
    """Обробник команди /start."""
    await send_webapp_button(update, context)

async def periodic_check(context):
    """Перевіряє статус підписки всіх користувачів і оновлює кнопку."""
    for user_id in list(user_messages.keys()):
        is_subscribed = await check_subscription(user_id)
        if not is_subscribed:
            keyboard = [[InlineKeyboardButton("Підписатися", url=f"https://t.me/{CHANNEL_ID[4:]}")]]
            text = "❌ Ви втратили доступ до WebApp. Підпишіться знову."
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await bot.edit_message_text(chat_id=user_id, message_id=user_messages[user_id], text=text, reply_markup=reply_markup)
            except Exception as e:
                logger.warning(f"Не вдалося оновити повідомлення для {user_id}: {e}")

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.job_queue.run_repeating(periodic_check, interval=CHECK_INTERVAL)
    
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
