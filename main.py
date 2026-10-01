import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

# Базовая ссылка на ваше мини-приложение
BASE_WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"
OWNER_ID = 7126242568  

@bot.message_handler(commands=['start'])
def send_welcome(message):
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
    
    target_username = args[1].lstrip('@')
    
    try:
        amount = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть целым числом.")
        return
    
    if amount <= 0:
        bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
        return
    
    # Создаем специальную ссылку с бонусом для игрока
    bonus_url = f"{BASE_WEB_APP_URL}?bonus={amount}"
    
    markup = InlineKeyboardMarkup()
    claim_button = InlineKeyboardButton(
        text=f"🎁 Забрать {amount} фишек!", 
        web_app=WebAppInfo(url=bonus_url)
    )
    markup.add(claim_button)
    
    # Отправляем сообщение (его можно отправить в чат, или переслать игроку)
    bot.send_message(
        message.chat.id,
        f"🎁 **Внимание, `@{target_username}`!**\n"
        f"👑 Владелец выделил вам персональный бонус: **{amount} фишек**!\n"
        f"Нажмите кнопку ниже, чтобы зайти в казино и забрать их:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
