import uuid
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

# Базовая ссылка на ваше мини-приложение
BASE_WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"
OWNER_ID = 7126242568  

# Временное хранилище для активных бонусов: { bonus_id: {"user_id": int, "amount": int, "used": bool} }
active_bonuses = {}

# Словарь для привязки username -> user_id (чтобы бот знал id пользователей, которые писали /start)
# В реальном проекте лучше заменить на базу данных (SQLite/PostgreSQL), чтобы данные не стирались при перезапуске бота.
known_users = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Сохраняем ID пользователя по его username на случай использования /give
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
    
    # Проверяем, знаком ли бот с этим пользователем
    if target_username not in known_users:
        bot.reply_to(
            message, 
            f"❌ Пользователь @{target_username} не найден в базе данных бота.\n"
            "Он должен хотя бы один раз запустить бота (`/start`), чтобы вы могли выдавать ему бонусы."
        )
        return

    target_user_id = known_users[target_username]

    # Генерируем уникальный одноразовый ID для бонуса
    bonus_id = str(uuid.uuid4())

    # Сохраняем информацию о бонусе в память
    active_bonuses[bonus_id] = {
        "user_id": target_user_id,
        "amount": amount,
        "used": False
    }
    
    # Формируем персональную ссылку с передачей bonus_id
    bonus_url = f"{BASE_WEB_APP_URL}?bonus_id={bonus_id}"
    
    markup = InlineKeyboardMarkup()
    claim_button = InlineKeyboardButton(
        text=f"🎁 Забрать {amount} фишек!", 
        web_app=WebAppInfo(url=bonus_url)
    )
    markup.add(claim_button)
    
    # Отправляем сообщение в чат
    bot.send_message(
        message.chat.id,
        f"🎁 **Внимание, `@{target_username}`!**\n"
        f"👑 Владелец выделил вам персональный бонус: **{amount} фишек**!\n"
        f"Нажмите кнопку ниже, чтобы зайти в казино и забрать их (ссылка одноразовая):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# Дополнительный вспомогательный метод (опционально), если ваш WebApp будет стучаться 
# к боту (или бэкенду) для проверки и активации бонуса по API. 
# Если ваш JS в браузере просто читает параметры из URL, этот блок нужен для бэкенд-логики.
@bot.message_handler(commands=['check_bonus'])
def check_bonus_endpoint(message):
    # Этот обработчик может служить примером того, как ваш WebApp может проверить бонус, 
    # если у вас написан полноценный сервер (например, на Flask/FastAPI).
    pass

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
