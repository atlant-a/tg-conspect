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
import nest_asyncio # type: ignore

# Токен бота і ID вашого каналу
TOKEN = "7799406026:AAEMNhLQllapHWd7nHk7RSl4SfR9wQ9C5Ug"
CHANNEL_ID = -1002419705763
WEB_APP_URL = "https://www.deep-d.pp.ua/"  # URL вашого вебзастосунку

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

async def check_and_update_messages():
    """Періодично перевіряє статус підписки і оновлює повідомлення."""
    while True:
        for user_id, message_id in user_messages.items():
            if not await is_subscribed(user_id):
                try:
                    # Видалення кнопок у старих повідомленнях
                    await application.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=message_id,
                        text="Доступ заблоковано! Будь ласка, підпишіться на канал, щоб отримати доступ.",
                        reply_markup=None,
                    )
                except Exception:
                    pass
        await asyncio.sleep(10)  # Регулярно перевіряємо статус (в секундах)

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

    # Запускаємо окрему задачу для перевірки підписок
    asyncio.create_task(check_and_update_messages())

    print("Бот запущений.")
    await application.run_polling()

if __name__ == "__main__":
    # Дозволяємо повторне використання існуючого event loop
    nest_asyncio.apply()
    asyncio.run(main())
