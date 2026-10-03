import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlparse, parse_qs

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# ====================== НАСТРОЙКИ ======================
# Токен берётся из переменной окружения BOT_TOKEN (Render -> Environment).
# НЕ вписывай его в код: файл лежит на GitHub.
TOKEN = os.environ.get("BOT_TOKEN", "")
BASE_WEB_APP_URL = "https://mars066111.github.io/tgcasinobot/"
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "https://mars066111.github.io")
OWNER_ID = 7126242568
PORT = int(os.environ.get("PORT", 10000))
DB_PATH = os.environ.get("DB_PATH", "leaderboard.db")

MAX_BODY = 64 * 1024          # максимум размера запроса
MAX_INV_ITEMS = 200           # сколько скинов хранить в профиле
MAX_BALANCE = 10 ** 12        # защита от мусорных чисел
AUTH_MAX_AGE = 3 * 24 * 3600  # сколько живёт подпись Telegram
ONLINE_WINDOW = 5 * 60        # «онлайн» = был активен за 5 минут
TOP_N = 50
MAX_SSE = 300                 # максимум одновременных live-подключений
# =======================================================

if not TOKEN:
    raise SystemExit("Не задана переменная окружения BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# ---------------------- БАЗА ДАННЫХ ----------------------
db_lock = threading.Lock()
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.execute(
    """CREATE TABLE IF NOT EXISTS players (
        uid INTEGER PRIMARY KEY,
        name TEXT, username TEXT, photo TEXT,
        balance INTEGER DEFAULT 0,
        cases INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        seen INTEGER DEFAULT 0,
        profile TEXT
    )"""
)
db.commit()

# ---------------------- LIVE (SSE) -----------------------
clients = set()
clients_lock = threading.Lock()
board_version = 0
version_cond = threading.Condition()


def bump_version():
    global board_version
    with version_cond:
        board_version += 1
        version_cond.notify_all()


def get_board():
    """Топ по деньгам и по кейсам + число игроков/онлайн."""
    now = int(time.time())
    with db_lock:
        total = db.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        online = db.execute(
            "SELECT COUNT(*) FROM players WHERE seen > ?", (now - ONLINE_WINDOW,)
        ).fetchone()[0]

        def top(col):
            rows = db.execute(
                f"SELECT uid,name,username,photo,balance,cases,level,seen,profile "
                f"FROM players WHERE {col} > 0 ORDER BY {col} DESC, uid ASC LIMIT ?",
                (TOP_N,),
            ).fetchall()
            out = []
            for r in rows:
                try:
                    p = json.loads(r[8]) if r[8] else {}
                except Exception:
                    p = {}
                out.append(
                    {
                        "id": r[0],
                        "name": r[1],
                        "username": r[2],
                        "photo": r[3],
                        "balance": r[4],
                        "cases": r[5],
                        "level": r[6],
                        "online": r[7] > now - ONLINE_WINDOW,
                        "title": p.get("title", ""),
                        "frame": p.get("frame", ""),
                    }
                )
            return out

        data = {"money": top("balance"), "cases": top("cases")}
    data["total"] = total
    data["online"] = online
    data["ts"] = now
    return data


def get_rank(uid):
    with db_lock:
        row = db.execute(
            "SELECT balance,cases FROM players WHERE uid=?", (uid,)
        ).fetchone()
        if not row:
            return None
        money_rank = (
            db.execute(
                "SELECT COUNT(*) FROM players WHERE balance > ?", (row[0],)
            ).fetchone()[0]
            + 1
        )
        cases_rank = (
            db.execute(
                "SELECT COUNT(*) FROM players WHERE cases > ?", (row[1],)
            ).fetchone()[0]
            + 1
        )
    return {"money": money_rank, "cases": cases_rank}


# --------------- ПРОВЕРКА ПОДПИСИ TELEGRAM ---------------
def verify_init_data(init_data):
    """Возвращает dict пользователя Telegram или None, если подпись неверна."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        got_hash = pairs.pop("hash", None)
        if not got_hash:
            return None
        check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, got_hash):
            return None
        if time.time() - int(pairs.get("auth_date", "0")) > AUTH_MAX_AGE:
            return None
        user = json.loads(pairs.get("user", "{}"))
        return user if user.get("id") else None
    except Exception:
        return None


# --------------- ОЧИСТКА ДАННЫХ ОТ КЛИЕНТА ---------------
def to_int(v, lo=0, hi=MAX_BALANCE):
    try:
        return max(lo, min(hi, int(v)))
    except Exception:
        return lo


def to_str(v, n):
    return str(v or "")[:n]


def clean_profile(p):
    inv = []
    for it in (p.get("inv") or [])[:MAX_INV_ITEMS]:
        try:
            inv.append(
                [to_str(it[0], 40), to_str(it[1], 60), to_str(it[2], 12), to_int(it[3], 0, 10 ** 9)]
            )
        except Exception:
            continue
    return {
        "title": to_str(p.get("title"), 24),
        "frame": to_str(p.get("frame"), 4),
        "elo": to_int(p.get("elo"), 0, 10 ** 9),
        "xp": to_int(p.get("xp"), 0, 10 ** 9),
        "games": to_int(p.get("games"), 0, 10 ** 9),
        "upW": to_int(p.get("upW"), 0, 10 ** 9),
        "upL": to_int(p.get("upL"), 0, 10 ** 9),
        "maxBal": to_int(p.get("maxBal")),
        "maxItem": to_int(p.get("maxItem"), 0, 10 ** 9),
        "ach": [bool(x) for x in (p.get("ach") or [])[:30]],
        "streak": to_int(p.get("streak"), 0, 10 ** 5),
        "invCount": to_int(p.get("invCount"), 0, 10 ** 7),
        "invValue": to_int(p.get("invValue")),
        "inv": inv,
    }


# ---------------------- HTTP-СЕРВЕР ----------------------
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Vary", "Origin")

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/stream":
            return self._stream()
        if url.path == "/api/board":
            return self._json(get_board())
        if url.path == "/api/player":
            q = parse_qs(url.query)
            try:
                uid = int(q.get("id", ["0"])[0])
            except ValueError:
                return self._json({"error": "bad id"}, 400)
            return self._player(uid)
        # health-check для Render / пингера
        body = b"Bot is alive and running!"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _player(self, uid):
        now = int(time.time())
        with db_lock:
            r = db.execute(
                "SELECT uid,name,username,photo,balance,cases,level,seen,profile "
                "FROM players WHERE uid=?",
                (uid,),
            ).fetchone()
        if not r:
            return self._json({"error": "not found"}, 404)
        try:
            p = json.loads(r[8]) if r[8] else {}
        except Exception:
            p = {}
        rank = get_rank(uid) or {}
        self._json(
            {
                "id": r[0],
                "name": r[1],
                "username": r[2],
                "photo": r[3],
                "balance": r[4],
                "cases": r[5],
                "level": r[6],
                "online": r[7] > now - ONLINE_WINDOW,
                "seen": r[7],
                "rank": rank,
                "profile": p,
            }
        )

    def do_POST(self):
        if urlparse(self.path).path != "/api/sync":
            return self._json({"error": "not found"}, 404)
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_BODY:
            return self._json({"error": "bad size"}, 413)
        try:
            data = json.loads(self.rfile.read(n))
        except Exception:
            return self._json({"error": "bad json"}, 400)

        user = verify_init_data(str(data.get("initData", "")))
        if not user:
            return self._json({"error": "auth"}, 401)

        uid = int(user["id"])
        name = to_str(user.get("first_name") or user.get("username") or "Игрок", 40)
        username = to_str(user.get("username"), 40)
        photo = to_str(user.get("photo_url"), 300)
        if not photo.startswith("https://"):
            photo = ""
        balance = to_int(data.get("balance"))
        cases = to_int(data.get("cases"), 0, 10 ** 9)
        level = to_int(data.get("level"), 1, 10 ** 4)
        prof = json.dumps(clean_profile(data.get("profile") or {}), ensure_ascii=False)

        with db_lock:
            db.execute(
                """INSERT INTO players (uid,name,username,photo,balance,cases,level,seen,profile)
                   VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(uid) DO UPDATE SET
                     name=excluded.name, username=excluded.username, photo=excluded.photo,
                     balance=excluded.balance, cases=excluded.cases, level=excluded.level,
                     seen=excluded.seen, profile=excluded.profile""",
                (uid, name, username, photo, balance, cases, level, int(time.time()), prof),
            )
            db.commit()
        bump_version()
        self._json({"ok": True, "rank": get_rank(uid)})

    def _stream(self):
        with clients_lock:
            if len(clients) >= MAX_SSE:
                return self._json({"error": "busy"}, 503)
            token = object()
            clients.add(token)
        try:
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            seen_version = -1
            last_ping = 0
            last_push = 0
            while True:
                with version_cond:
                    version_cond.wait(timeout=5)
                    cur = board_version
                now = time.time()
                if cur != seen_version and now - last_push >= 1.0:
                    seen_version = cur
                    last_push = now
                    payload = json.dumps(get_board(), ensure_ascii=False)
                    self.wfile.write(f"event: board\ndata: {payload}\n\n".encode())
                    self.wfile.flush()
                    last_ping = now
                elif now - last_ping >= 15:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    last_ping = now
        except Exception:
            pass
        finally:
            with clients_lock:
                clients.discard(token)
            self.close_connection = True


def run_server():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.daemon_threads = True
    srv.serve_forever()


threading.Thread(target=run_server, daemon=True).start()
# --------------------------------------------------------------------


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
