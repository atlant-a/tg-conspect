import os
import asyncio
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import nest_asyncio  # type: ignore

# Отримуємо змінні оточення
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEB_APP_URL = os.getenv("WEB_APP_URL")

# Перевіряємо, чи змінні завантажились
if not TOKEN or not CHANNEL_ID or not WEB_APP_URL:
    raise ValueError("Не встановлені змінні оточення!")

# Зберігання message_id для оновлення або видалення повідомлень
user_messages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Відправка стартового повідомлення з інлайн-кнопкою."""
    user = update.effective_user

    # Надсилаємо повідомлення з кнопкою перевірки підписки
    sent_message = await update.message.reply_text(
        "Натисніть кнопку нижче, щоб отримати доступ до вебзастосунку:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Перевірити статус", callback_data="check_subscription")]]
        ),
    )
    # Зберігаємо message_id для подальшого оновлення
    user_messages[user.id] = sent_message.message_id

async def handle_subscription_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перевіряє статус підписки і обробляє натискання кнопки."""
    query = update.callback_query
    user = query.from_user

    # Перевіряємо статус підписки
    if await is_subscribed(user.id):
        # Якщо підписка активна, оновлюємо кнопку для запуску вебзастосунку
        await query.edit_message_text(
            "Ви підписані! Натисніть кнопку нижче, щоб запустити вебзастосунок:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Запустити вебзастосунок", web_app=WebAppInfo(WEB_APP_URL))]]
            ),
        )
    else:
        # Якщо користувач не підписаний, оновлюємо повідомлення з інструкцією
        await query.edit_message_text(
            "Ви не підписані на канал. Будь ласка, підпишіться за посиланням нижче:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Підписатися на канал", url=f"https://t.me/{CHANNEL_ID}")]]
            ),
        )

async def is_subscribed(user_id: int) -> bool:
    """Перевіряє, чи є користувач підписаним на канал."""
    try:
        member = await application.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False  # Якщо користувач не знайдений або виникла помилка

async def main():
    global application
    application = Application.builder().token(TOKEN).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_subscription_check, pattern="check_subscription"))

    print("Бот запущений.")
    await application.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
