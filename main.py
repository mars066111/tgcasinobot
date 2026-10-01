import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (чтобы приложение не падало по таймауту) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

    def log_message(self, format, *args):
        pass  # Отключаем лишний спам в логах сервера

def run_server():
    server_address = ("0.0.0.0", 10000)
    httpd = HTTPServer(server_address, SimpleHandler)
    httpd.serve_forever()

# Запускаем сервер в фоновом потоке
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
# --------------------------------------------------------------------

TOKEN = "8980639396:AAFCDoDBWSHUR4gQU4PAym-RHAvx6ujt6PM"
bot = telebot.TeleBot(TOKEN)

# Базовая ссылка на ваше мини-приложение
BASE_WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"
OWNER_ID = 7126242568


@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = InlineKeyboardMarkup()
  web_app_button = InlineKeyboardButton(
      text="🎰 Играть в Казино", web_app=WebAppInfo(url=BASE_WEB_APP_URL)
  )
  markup.add(web_app_button)

  bot.send_message(
      message.chat.id,
      (
          "Привет! Добро пожаловать в официальное Telegram Casino 🎲\nНажми на"
          " кнопку ниже, чтобы открыть мини-приложение:"
      ),
      reply_markup=markup,
  )


@bot.message_handler(commands=["give"])
def give_money(message):
  # Проверяем, что команду пишете именно вы
  if message.from_user.id != OWNER_ID:
    bot.reply_to(message, "⛔ У вас нет прав на использование этой команды.")
    return

  args = message.text.split()
  if len(args) < 3:
    bot.reply_to(
        message,
        "⚠️ Использование: `/give ID_пользователя сумма`",
        parse_mode="Markdown",
    )
    return

  try:
    target_user_id = int(args[1])  # Принимаем чистый цифровой ID
    amount = int(args[2])
  except ValueError:
    bot.reply_to(message, "❌ Ошибка! ID и сумма должны быть числами.")
    return

  if amount <= 0:
    bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
    return

  # Создаем защищенную ссылку с бонусом и привязкой к ID игрока
  bonus_url = f"{BASE_WEB_APP_URL}?bonus={amount}&for_user={target_user_id}"

  markup = InlineKeyboardMarkup()
  claim_button = InlineKeyboardButton(
      text=f"🎁 Забрать {amount} фишек!", web_app=WebAppInfo(url=bonus_url)
  )
  markup.add(claim_button)

  try:
    # Отправляем персональное сообщение НАПРЯМУЮ игроку по его ID
    bot.send_message(
        target_user_id,
        (
            "🎁 **Внимание!**\n👑 Владелец выделил вам персональный бонус:"
            f" **{amount} фишек**!\nНажмите кнопку ниже, чтобы зайти в казино и"
            " забрать их:"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )
    # Отправляем вам подтверждение в чат
    bot.reply_to(
        message,
        (
            "✅ Бонус в размере "
            f"{amount} фишек успешно отправлен игроку с ID `{target_user_id}` в"
            " личные сообщения!"
        ),
    )

  except Exception as e:
    bot.reply_to(
        message,
        (
            "❌ Не удалось отправить сообщение игроку. Возможно, он еще не"
            f" запустил бота или заблокировал его.\nОшибка: {e}"
        ),
    )


if __name__ == "__main__":
  print("Бот и веб-сервер запущены...")
  bot.infinity_polling()
