import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import json
import os

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"
OWNER_ID = 7126242568  

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    web_app_button = InlineKeyboardButton(
        text="🎰 Играть в Казино", 
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    markup.add(web_app_button)
    
    bot.send_message(
        message.chat.id,
        "Привет! Добро пожаловать в официальное Telegram Casino 🎲\nНажми на кнопку ниже, чтобы открыть мини-приложение:",
        reply_markup=markup
    )

@bot.message_handler(commands=['give'])
def give_money(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ У вас нет прав на использование этой команды.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️️ Использование: `/give @username сумма`", parse_mode="Markdown")
        return
    
    target_username = args[1].lstrip('@')
    
    try:
        amount = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть целым числом.")
        return
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
        return
    
    players_db = load_db()
    
    if target_username not in players_db:
        players_db[target_username] = 0
    
    players_db[target_username] += amount
    save_db(players_db)
    
    # 1. Отправляем отчет вам в чат
    bot.reply_to(
        message, 
        f"👑 **Казначейство казино:**\n"
        f"Успешно выдано `{amount}` фишек игроку `@{target_username}`.\n"
        f"💰 Баланс в базе: `{players_db[target_username]}` фишек.",
        parse_mode="Markdown"
    )
    
    # 2. Пытаемся отправить уведомление самому игроку (если бот знает его chat_id)
    # Примечание: Чтобы бот мог написать по username, пользователь должен был хотя бы раз написать боту или нажать старт.
    # Более надежный способ — передавать не юзернейм, а Telegram ID, но для юзернеймов сделаем попытку оповещения:
    try:
        # Если у вас в базе сохранялся chat_id игрока, можно отправить ему лично. 
        # Пока что бот отправляет подтверждение в текущий чат, где вы ввели команду.
        pass
    except Exception as e:
        print(f"Не удалось отправить сообщение игроку: {e}")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
