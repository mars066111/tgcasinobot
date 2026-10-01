import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

# Базовая ссылка на ваше мини-приложение
BASE_WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"
OWNER_ID = 7126242568  

# Словарь для хранения связки username -> user_id (чтобы бот знал, кому выдавать бонус)
known_users = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Запоминаем юзернейм и ID пользователя, когда он пишет /start
    if message.from_user.username:
        known_users[message.from_user.username.lower()] = message.from_user.id

    markup = InlineKeyboardMarkup()
    web_app_button = InlineKeyboardButton(
        text="🎰 Играть в Казино", 
        web_app=WebAppInfo(url=BASE_WEB_APP_URL)
    )
    markup.add(web_app_button)
    
    bot.send_message(
        message.chat.id,
        "Привет! Добро пожаловать в официальное Telegram Casino 🎲\nНажми на кнопку ниже, чтобы открыть мини-приложение:",
        reply_markup=markup
    )

@bot.message_handler(commands=['give'])
def give_money(message):
    # Проверяем, что команду пишете именно вы
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ У вас нет прав на использование этой команды.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ Использование: `/give @username сумма`", parse_mode="Markdown")
        return
    
    target_username = args[1].lstrip('@').lower()
    
    try:
        amount = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть целым числом.")
        return
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
        return
    
    # Проверяем, запускал ли пользователь бота раньше
    if target_username not in known_users:
        bot.reply_to(
            message, 
            f"❌ Пользователь @{target_username} не найден в базе данных.\n"
            "Он должен хотя бы один раз нажать `/start` в этом боте, прежде чем вы сможете выдать ему бонус."
        )
        return

    target_user_id = known_users[target_username]

    # Создаем защищенную ссылку с бонусом и привязкой к ID игрока
    bonus_url = f"{BASE_WEB_APP_URL}?bonus={amount}&for_user={target_user_id}"
    
    markup = InlineKeyboardMarkup()
    claim_button = InlineKeyboardButton(
        text=f"🎁 Забрать {amount} фишек!", 
        web_app=WebAppInfo(url=bonus_url)
    )
    markup.add(claim_button)
    
    try:
        # Отправляем персональное сообщение НАПРЯМУЮ игроку в личные сообщения[span_2](start_span)[span_2](end_span)[span_3](start_span)[span_3](end_span)
        bot.send_message(
            target_user_id,
            f"🎁 **Внимание, `@{target_username}`!**\n"
            f"👑 Владелец выделил вам персональный бонус: **{amount} фишек**!\n"
            f"Нажмите кнопку ниже, чтобы зайти в казино и забрать их:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        # Отправляем вам подтверждение в чат
        bot.reply_to(message, f"✅ Бонус в размере {amount} фишек успешно отправлен игроку @{target_username} в личные сообщения!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось отправить сообщение игроку. Возможно, он заблокировал бота.\nОшибка: {e}")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
