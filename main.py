import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import json
import os

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"
OWNER_ID = 7126242568  

DB_FILE = "database.json"

# Функции для работы с файлом базы данных
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
        bot.reply_to(message, "⚠️ Использование: `/give @username сумма`", parse_mode="Markdown")
        return
    
    target_username = args[1].lstrip('@').lower() # Приводим к нижнему регистру для надежности
    
    try:
        amount = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть целым числом.")
        return
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
        return
    
    # Загружаем базу из файла
    players_db = load_db()
    
    if target_username not in players_db:
        players_db[target_username] = 0
    
    players_db[target_username] += amount
    
    # Сохраняем обратно в файл
    save_db(players_db)
    
    bot.reply_to(
        message, 
        f"👑 **Казначейство казино:**\n"
        f"Успешно выдано `{amount}` фишек игроку `@{target_username}`.\n"
        f"💰 Баланс в базе: `{players_db[target_username]}` фишек.",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
