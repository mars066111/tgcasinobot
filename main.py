import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"

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

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
