import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"

# Ваш реальный Telegram ID Владельца
OWNER_ID = 7126242568  

# База данных балансов игроков
players_db = {}

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

# Команда для выдачи денег: /give @username сумма
@bot.message_handler(commands=['give'])
def give_money(message):
    # Проверяем, что команду отправляете именно вы (по вашему ID)
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ У вас нет прав на использование этой команды. Вы не Владелец!")
        return
    
    # Разбираем команду (/give @username сумма)
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ Ошибка в формате!\nИспользуйте: `/give @username сумма`", parse_mode="Markdown")
        return
    
    target_username = args[1].lstrip('@') # Убираем символ @, если ввели с ним
    
    try:
        amount = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть целым числом.")
        return
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
        return
    
    # Начисляем деньги из безлимитного фонда
    if target_username not in players_db:
        players_db[target_username] = 0
    
    players_db[target_username] += amount
    
    # Отправляем отчет вам
    bot.reply_to(
        message, 
        f"👑 **Казначейство казино:**\n"
        f"Успешно выдано `{amount}` фишек игроку `@{target_username}`.\n"
        f"💰 Текущий баланс игрока: `{players_db[target_username]}` фишек.",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
