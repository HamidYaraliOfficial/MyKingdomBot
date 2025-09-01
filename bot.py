import logging
import sqlite3
import uuid
import asyncio
import time
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7130642738:AAF3B75yP6iJUMAs7UVKGts9b_t6YSIpruk"
OWNER_IDS = [123456789,123456789]
INVINCIBLE_USER = 123456789

COUNTRIES = {
    "امپراتوری آستاریا": "✅",
    "جمهوری نیکان": "✅",
    "سلطنت آورا": "✅",
    "فدراسیون زامورا": "✅",
    "پادشاهی دراکورا": "✅",
    "کنفدراسیون میراژ": "✅",
    "مملکت آلفاریوس": "✅",
    "اتحاد شمالی کوردان": "✅",
    "دولت مقدس سولاریا": "✅",
    "جمهوری متحد زاتاک": "✅",
    "امارت صحراوی باریس": "✅",
    "پادشاهی ماروِن": "✅",
    "فدراسیون صنعتی تاراکس": "✅",
    "جمهوری آزاد رُمانیا": "✅",
    "سرزمین آتشین نِرونا": "✅",
    "قلمروی سلطنتی ویسان": "✅",
    "جمهوری کوهستانی باریوس": "✅",
    "مملکت دریایی لورکا": "✅",
    "کنفدراسیون جنگلی آریسا": "✅",
    "سلطنت شبانه ایریس": "✅",
    "دولت کویری ساندورا": "✅",
    "پادشاهی زمردین زیگورا": "✅",
    "امپراتوری آهنین نُوا": "✅",
    "اتحاد ابرشهرها": "✅",
    "قلمرو ساکنین شب": "✅",
    "جمهوری هوشمند نئوس": "✅",
    "مملکت یخ‌زده اِلدارا": "✅",
    "پادشاهی سحرآمیز مِراونا": "✅",
    "جمهوری نظامی آرتیس": "✅",
    "فدراسیون خورشیدی نُتالیا": "✅"
}

EQUIPMENTS = {
    "army": {"name": "🪖 ارتش", "price": 100},
    "spy": {"name": "🕵️ جاسوس", "price": 200},
    "hacker": {"name": "💻 هکر", "price": 150},
    "firewall": {"name": "🔥 فایروال", "price": 120},
    "propaganda": {"name": "📢 تبلیغات سیاه", "price": 90},
    "factory": {"name": "🏭 کارخانه", "price": 150},
    "school": {"name": "🏫 مدرسه", "price": 130},
    "shield": {"name": "🛡️ سپر دفاعی", "price": 200},
}

ATTACK_EQUIPMENTS = ["army", "spy", "hacker", "propaganda"]
DEFENSE_EQUIPMENTS = ["firewall", "shield"]

ADMIN_PERMISSIONS = {
    "start_game": "شروع بازی",
    "end_game": "پایان بازی",
    "broadcast": "همگانی",
    "set_country_price": "تعیین قیمت مملکت‌ها",
    "ban_user": "بن کاربر",
    "unban_user": "آنبن کاربر",
    "set_prize": "تعیین جایزه",
    "reset_bot": "ریست ربات",
    "destroy_country": "سقوط مملکت",
    "give_equipment": "دادن امکانات",
    "give_country": "دادن مملکت به کاربر",
    "set_equipment_price": "تغییر قیمت امکانات",
    "change_channel": "تغییر کانال",
    "bot_stats": "آمار ربات",
    "set_min_players": "حداقل شرکت‌کنندگان",
    "confirm_payments": "تایید پرداخت‌ها",
    "manage_channels": "مدیریت کانال‌ها"
}

DAMAGE_VALUES = {
    "army": {"defense": 20, "shield": 10},
    "hacker": {"defense": 25, "shield": 15},
    "propaganda": {"defense": 15, "shield": 10},
}

payment_requests = {}
user_channel_timers = {}
alliance_requests = {}
spy_operations = {}

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('war_game.db', check_same_thread=False)
        self.create_tables()
        self.initialize_settings()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_banned INTEGER DEFAULT 0,
            is_verified INTEGER DEFAULT 0
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            name TEXT PRIMARY KEY,
            status TEXT,
            price INTEGER,
            owner_id INTEGER,
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipments (
            user_id INTEGER,
            country_name TEXT,
            equipment_id TEXT,
            quantity INTEGER,
            PRIMARY KEY (user_id, country_name, equipment_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (country_name) REFERENCES countries(name)
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            permissions TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS required_channels (
            channel_username TEXT PRIMARY KEY
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alliances (
            country1 TEXT,
            country2 TEXT,
            PRIMARY KEY (country1, country2),
            FOREIGN KEY (country1) REFERENCES countries(name),
            FOREIGN KEY (country2) REFERENCES countries(name)
        )''')
        self.conn.commit()

    def initialize_settings(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO game_settings (key, value)
        VALUES ('channel', ?)
        ''', ('cyber43',))
        self.conn.commit()

    def add_user(self, user_id, username):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, is_verified) 
            VALUES (?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
        ''', (user_id, username))
        self.conn.commit()
        
    def mark_user_verified(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_verified = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def is_verified(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_verified FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else False

    def ban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def unban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def is_banned(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else False

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username FROM users WHERE is_banned = 0')
        return cursor.fetchall()

    def get_banned_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username FROM users WHERE is_banned = 1')
        return cursor.fetchall()

    def set_country_owner(self, country_name, user_id, username):
        cursor = self.conn.cursor()
        self.add_user(user_id, username)
        cursor.execute('UPDATE countries SET status = "❌", owner_id = ? WHERE name = ?', (user_id, country_name))
        self.conn.commit()

    def get_country_owner(self, country_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT owner_id FROM countries WHERE name = ?', (country_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_user_countries(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM countries WHERE owner_id = ?', (user_id,))
        return [row[0] for row in cursor.fetchall()]

    def add_equipment(self, user_id, country_name, equipment_id, quantity):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO equipments (user_id, country_name, equipment_id, quantity)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, country_name, equipment_id) 
        DO UPDATE SET quantity = quantity + excluded.quantity
        ''', (user_id, country_name, equipment_id, quantity))
        self.conn.commit()

    def get_user_equipments(self, user_id, country_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT equipment_id, quantity 
        FROM equipments 
        WHERE user_id = ? AND country_name = ?
        ''', (user_id, country_name))
        return {row[0]: row[1] for row in cursor.fetchall()}
        
    def get_country_equipments(self, country_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT equipment_id, SUM(quantity) 
        FROM equipments 
        WHERE country_name = ?
        GROUP BY equipment_id
        ''', (country_name,))
        return {row[0]: row[1] for row in cursor.fetchall()}

    def remove_equipment(self, user_id, country_name, equipment_id, quantity):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE equipments 
        SET quantity = quantity - ?
        WHERE user_id = ? AND country_name = ? AND equipment_id = ? AND quantity >= ?
        ''', (quantity, user_id, country_name, equipment_id, quantity))
        affected = cursor.rowcount
        self.conn.commit()
        return affected > 0

    def initialize_countries(self):
        cursor = self.conn.cursor()
        for country, status in COUNTRIES.items():
            cursor.execute('''
            INSERT OR IGNORE INTO countries (name, status, price)
            VALUES (?, ?, ?)
            ''', (country, status, 100))
        self.conn.commit()

    def set_country_price(self, country_name, price):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE countries SET price = ? WHERE name = ?', (price, country_name))
        self.conn.commit()

    def get_country_price(self, country_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT price FROM countries WHERE name = ?', (country_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_available_countries(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM countries WHERE status = "✅"')
        return [row[0] for row in cursor.fetchall()]

    def destroy_country(self, country_name):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE countries SET status = "💀", owner_id = NULL WHERE name = ?', (country_name,))
        cursor.execute('DELETE FROM equipments WHERE country_name = ?', (country_name,))
        cursor.execute('DELETE FROM alliances WHERE country1 = ? OR country2 = ?', (country_name, country_name))
        self.conn.commit()

    def set_game_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO game_settings (key, value)
        VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()

    def get_game_setting(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM game_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else default

    def add_admin(self, user_id, permissions):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO admins (user_id, permissions)
        VALUES (?, ?)
        ''', (user_id, ",".join(permissions)))
        self.conn.commit()

    def remove_admin(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def is_admin(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

    def get_admin_permissions(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT permissions FROM admins WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0].split(",") if result else []

    def get_all_admins(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT u.user_id, u.username, a.permissions 
        FROM users u
        JOIN admins a ON u.user_id = a.user_id
        ''')
        return cursor.fetchall()
    
    def add_required_channel(self, channel_username):
        channel_username = channel_username.lstrip('@')
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO required_channels (channel_username) VALUES (?)', (channel_username,))
        self.conn.commit()
    
    def remove_required_channel(self, channel_username):
        channel_username = channel_username.lstrip('@')
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM required_channels WHERE channel_username = ?', (channel_username,))
        self.conn.commit()
    
    def get_required_channels(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT channel_username FROM required_channels')
        return [row[0] for row in cursor.fetchall()]
    
    def count_players_with_countries(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT owner_id) FROM countries WHERE status = "❌"')
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def end_game(self):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE countries SET status = "✅", owner_id = NULL WHERE status != "💀"')
        cursor.execute('DELETE FROM equipments')
        cursor.execute('DELETE FROM alliances')
        self.set_game_setting("game_started", "0")
        self.conn.commit()
        
    def create_alliance(self, country1, country2):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO alliances (country1, country2)
        VALUES (?, ?)
        ''', (country1, country2))
        cursor.execute('''
        INSERT OR IGNORE INTO alliances (country1, country2)
        VALUES (?, ?)
        ''', (country2, country1))
        self.conn.commit()
        
    def are_allies(self, country1, country2):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 1 FROM alliances 
        WHERE country1 = ? AND country2 = ?
        ''', (country1, country2))
        return cursor.fetchone() is not None
        
    def get_allies(self, country_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT country2 FROM alliances 
        WHERE country1 = ?
        ''', (country_name,))
        return [row[0] for row in cursor.fetchall()]

db = Database()
db.initialize_countries()

async def show_main_menu(update, context, user_id):
    user_countries = db.get_user_countries(user_id)
    has_country = bool(user_countries)
    
    keyboard = [
        [InlineKeyboardButton("📚 راهنمای بازی", callback_data="guide")],
        [
            InlineKeyboardButton("📢 چنل بازی", url="https://t.me/cyber43"),
            InlineKeyboardButton("🏛️ تأسیس مملکت", callback_data="buy_country"),
        ],
        [
            InlineKeyboardButton("🏗️ توسعه امکانات", callback_data="buy_equipment"),
            InlineKeyboardButton("💥 عملیات", callback_data="attack"),
        ],
        [
            InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
            InlineKeyboardButton("🌍 بازدید مملکت‌ها", callback_data="visit_countries"),
        ],
    ]
    
    if has_country:
        keyboard.insert(3, [
            InlineKeyboardButton("📢 ارسال پیام به کانال", callback_data="send_to_channel"),
            InlineKeyboardButton("🤝 درخواست اتحاد", callback_data="alliance_request"),
        ])
        
        allies = db.get_allies(user_countries[0])
        if allies:
            keyboard.insert(4, [
                InlineKeyboardButton("🎁 ارسال امکانات به متحد", callback_data="send_to_ally")
            ])
    
    if user_id in OWNER_IDS or db.is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🛠️ پنل مدیریت", callback_data="panel")])

    keyboard.append([InlineKeyboardButton("🔄 رفرش", callback_data="refresh")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'message'):
        await update.message.reply_text(
            "🎮 به ربات «مملکت من» خوش آمدید!\n\n"
            "🏆 آخرین بازمانده برنده بازی خواهد شد!\n"
            "⚔️ مملکت خود را تقویت کنید و به دیگران عملیات انجام دهید!",
            reply_markup=reply_markup,
        )
    else:
        await update.edit_message_text(
            "🎮 به ربات «مملکت من» خوش آمدید!\n\n"
            "🏆 آخرین بازمانده برنده بازی خواهد شد!\n"
            "⚔️ مملکت خود را تقویت کنید و به دیگران عملیات انجام دهید!",
            reply_markup=reply_markup,
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "کاربر ناشناس"

    if db.is_banned(user_id):
        await update.message.reply_text("⛔ شما از ربات بن شده‌اید!")
        return

    db.add_user(user_id, username)
    
    if db.is_verified(user_id):
        await show_main_menu(update, context, user_id)
        return
    
    if user_id in OWNER_IDS or db.is_admin(user_id):
        await show_main_menu(update, context, user_id)
        return
        
    required_channels = db.get_required_channels()
    if required_channels:
        user_channel_timers[user_id] = time.time()
        
        message = "⚠️ برای استفاده از ربات، لطفاً در کانال‌های زیر عضو شوید:\n"
        buttons = []
        for channel in required_channels:
            message += f"\n🔹 @{channel}"
            buttons.append([InlineKeyboardButton(
                f"عضویت در @{channel}", 
                url=f"https://t.me/{channel}")
            ])
        message += "\n\n⏱️ لطفاً ۵ ثانیه صبر کنید و سپس دکمه «بررسی عضویت» را فشار دهید."
        
        buttons.append([InlineKeyboardButton("🔄 بررسی عضویت", callback_data="verify_join")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(message, reply_markup=reply_markup)
        return

    db.mark_user_verified(user_id)
    await show_main_menu(update, context, user_id)

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in OWNER_IDS and not db.is_admin(user_id):
        await update.message.reply_text("⛔ شما دسترسی به این بخش را ندارید!")
        return

    is_owner = user_id in OWNER_IDS
    admin_permissions = db.get_admin_permissions(user_id) if not is_owner else list(ADMIN_PERMISSIONS.keys())

    keyboard = []
    temp_row = []
    
    if is_owner or "start_game" in admin_permissions:
        temp_row.append(InlineKeyboardButton("🚀 شروع بازی", callback_data="start_game"))
    
    if is_owner or "end_game" in admin_permissions:
        temp_row.append(InlineKeyboardButton("🛑 پایان بازی", callback_data="end_game"))
    
    if temp_row:
        keyboard.append(temp_row)
        temp_row = []
    
    if is_owner or "broadcast" in admin_permissions:
        temp_row.append(InlineKeyboardButton("📢 همگانی", callback_data="broadcast"))
    
    if is_owner or "set_country_price" in admin_permissions:
        temp_row.append(InlineKeyboardButton("💰 قیمت مملکت‌ها", callback_data="set_country_price"))
    
    if is_owner or "ban_user" in admin_permissions:
        temp_row.append(InlineKeyboardButton("🚫 بن کاربر", callback_data="ban_user"))
    
    if temp_row:
        keyboard.append(temp_row)
        temp_row = []
    
    if is_owner or "unban_user" in admin_permissions:
        temp_row.append(InlineKeyboardButton("✅ آنبن کاربر", callback_data="unban_user"))
    
    if is_owner or "set_prize" in admin_permissions:
        temp_row.append(InlineKeyboardButton("🏆 تعیین جایزه", callback_data="set_prize"))
    
    if temp_row:
        keyboard.append(temp_row)
        temp_row = []
    
    if is_owner or "reset_bot" in admin_permissions:
        temp_row.append(InlineKeyboardButton("🔄 ریست ربات", callback_data="reset_bot"))
    
    if is_owner or "destroy_country" in admin_permissions:
        temp_row.append(InlineKeyboardButton("💀 سقوط مملکت", callback_data="destroy_country"))
    
    if temp_row:
        keyboard.append(temp_row)
        temp_row = []
    
    if is_owner or "give_equipment" in admin_permissions:
        temp_row.append(InlineKeyboardButton("🎁 دادن امکانات", callback_data="give_equipment"))
    
    if is_owner or "give_country" in admin_permissions:
        temp_row.append(InlineKeyboardButton("🏰 دادن مملکت", callback_data="give_country"))
    
    if temp_row:
        keyboard.append(temp_row)
        temp_row = []
    
    if is_owner or "set_equipment_price" in admin_permissions:
        temp_row.append(InlineKeyboardButton("⚔️ قیمت امکانات", callback_data="set_equipment_price"))
    
    if is_owner or "change_channel" in admin_permissions:
        temp_row.append(InlineKeyboardButton("📢 تغییر کانال", callback_data="change_channel"))
    
    if is_owner or "bot_stats" in admin_permissions:
        temp_row.append(InlineKeyboardButton("📊 آمار ربات", callback_data="bot_stats"))
    
    if is_owner or "set_min_players" in admin_permissions:
        temp_row.append(InlineKeyboardButton("👥 حداقل بازیکنان", callback_data="set_min_players"))
    
    if is_owner or "manage_channels" in admin_permissions:
        temp_row.append(InlineKeyboardButton("➕ افزودن کانال اجباری", callback_data="add_required_channel"))
        temp_row.append(InlineKeyboardButton("➖ حذف کانال اجباری", callback_data="remove_required_channel"))
    
    if temp_row:
        keyboard.append(temp_row)
        temp_row = []
    
    if is_owner:
        keyboard.append([InlineKeyboardButton("👤 افزودن ادمین", callback_data="add_admin")])
        keyboard.append([InlineKeyboardButton("🔧 مدیریت دسترسی", callback_data="manage_admin_permissions")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠️ پنل مدیریت:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username or "کاربر ناشناس"

    if db.is_banned(user_id):
        await query.answer("⛔ شما از ربات بن شده‌اید!")
        return

    await query.answer()
    data = query.data

    if data == "verify_join":
        required_channels = db.get_required_channels()
        if not required_channels:
            await query.edit_message_text("✅ عضویت شما با موفقیت تأیید شد! لطفاً کمی صبر کنید...")
            db.mark_user_verified(user_id)
            await asyncio.sleep(1)
            await show_main_menu(query, context, user_id)
            return
        
        start_time = user_channel_timers.get(user_id, 0)
        elapsed = time.time() - start_time
        
        if elapsed < 5:
            message = "⛔ هنوز ۵ ثانیه نشده است! لطفاً صبر کنید.\n\n"
            buttons = []
            for channel in required_channels:
                message += f"\n🔹 @{channel}"
                buttons.append([InlineKeyboardButton(
                    f"عضویت در @{channel}", 
                    url=f"https://t.me/{channel}")
                ])
            message += f"\n\n⏱️ زمان باقی‌مانده: {5 - int(elapsed)} ثانیه"
            buttons.append([InlineKeyboardButton("🔄 بررسی عضویت", callback_data="verify_join")])
            
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.edit_message_text("✅ عضویت شما با موفقیت تأیید شد! لطفاً کمی صبر کنید...")
            db.mark_user_verified(user_id)
            await asyncio.sleep(1)
            await show_main_menu(query, context, user_id)
        return

    elif data == "guide":
        guide_text = """
📚 راهنمای کامل بازی مملکت من:

🔹 بخش‌های اصلی:
1. 🏛️ تأسیس مملکت
2. 🏗️ توسعه امکانات
3. 💥 عملیات علیه دیگران
4. 🛡️ دفاع از مملکت
5. 🤝 اتحاد با مملکت‌های دیگر

🔹 قوانین بازی:
- هر بازیکن فقط می‌تواند یک مملکت داشته باشد
- برای عملیات نیاز به امکانات دارید
- مملکت‌های بدون دفاع به راحتی سقوط می‌کنند
- آخرین مملکت باقی‌مانده برنده است
- مملکت‌های متحد نمی‌توانند به هم عملیات انجام دهند
- مملکت‌های متحد می‌توانند به هم امکانات بفرستند
- در صورت پیروزی، جایزه بین متحدان تقسیم می‌شود

⚔️ قدرت امکانات:
🪖 ارتش: 3 پدافند یا 1 سپر
🕵️ جاسوس: دزدی تجهیزات از حریف
💻 هکر: 10 سپر یا 30 پدافند
🔥 فایروال: دفاع در برابر هکرها
📢 تبلیغات سیاه: 10 تا = 5 سپر
🏭 کارخانه: تولید امکانات دفاعی
🏫 مدرسه: افزایش قدرت امکانات
🛡️ سپر دفاعی: قوی‌ترین دفاع

💰 قیمت‌ها:
مملکت‌ها: قیمت‌های متفاوت
امکانات: از 80 تا 200 داگز
"""
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(guide_text, reply_markup=reply_markup)

    elif data == "buy_country":
        if not db.get_game_setting("game_started") and user_id not in OWNER_IDS and not db.is_admin(user_id):
            await query.edit_message_text("⛔ بازی هنوز شروع نشده است!")
            return

        if db.get_user_countries(user_id):
            await query.edit_message_text("⛔ شما قبلاً یک مملکت دارید! هر کاربر فقط می‌تواند یک مملکت داشته باشد.")
            return

        available_countries = db.get_available_countries()
        if not available_countries:
            await query.edit_message_text("⛔ هیچ مملکتی برای تأسیس موجود نیست!")
            return

        keyboard = [
            [InlineKeyboardButton(country, callback_data=f"select_country_{country}")]
            for country in available_countries
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🏛️ مملکت مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("select_country_"):
        country = data.replace("select_country_", "")
        price = db.get_country_price(country)
        if not price:
            await query.edit_message_text("⛔ قیمت این مملکت تعیین نشده است!")
            return

        context.user_data["selected_country"] = country
        await query.edit_message_text(
            f"🏛️ مملکت انتخابی: {country}\n💰 قیمت: {price} داگز\n\n"
            f"لطفاً پیام پرداخت خود را ارسال کنید (متن دلخواه). درخواست شما به ادمین ارسال خواهد شد."
        )

    elif data == "buy_equipment":
        if not db.get_game_setting("game_started") and user_id not in OWNER_IDS and not db.is_admin(user_id):
            await query.edit_message_text("⛔ بازی هنوز شروع نشده است!")
            return

        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما باید ابتدا یک مملکت تأسیس کنید!")
            return

        keyboard = [
            [InlineKeyboardButton(eq["name"], callback_data=f"select_eq_{eq_id}")]
            for eq_id, eq in EQUIPMENTS.items()
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🏗️ امکانات مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("select_eq_"):
        equipment_id = data.replace("select_eq_", "")
        equipment = EQUIPMENTS.get(equipment_id)
        if not equipment:
            await query.edit_message_text("⛔ امکانات مورد نظر یافت نشد!")
            return

        context.user_data["selected_equipment"] = equipment_id
        await query.edit_message_text(f"🏗️ تعداد {equipment['name']} مورد نیاز را وارد کنید:")

    elif data == "attack":
        if not db.get_game_setting("game_started"):
            await query.edit_message_text("⛔ بازی هنوز شروع نشده است!")
            return

        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما باید ابتدا یک مملکت تأسیس کنید!")
            return

        min_players = int(db.get_game_setting("min_players", 0))
        if db.count_players_with_countries() < min_players:
            await query.edit_message_text(f"⛔ حداقل {min_players} بازیکن برای عملیات نیاز است!")
            return

        all_users = db.get_all_users()
        target_countries = []
        user_country = db.get_user_countries(user_id)[0]
        allies = db.get_allies(user_country)
        
        for user_id_db, _ in all_users:
            if user_id_db != user_id:
                countries = db.get_user_countries(user_id_db)
                for country in countries:
                    if country not in allies:
                        target_countries.append(country)
        
        if not target_countries:
            await query.edit_message_text("⛔ هیچ مملکتی برای عملیات موجود نیست!")
            return

        context.user_data["attack_targets"] = []
        
        keyboard = [
            [InlineKeyboardButton(country, callback_data=f"select_attack_target_{country}")]
            for country in target_countries
        ]
        keyboard.append([InlineKeyboardButton("✅ اتمام انتخاب مملکت‌ها", callback_data="confirm_attack_targets")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💥 مملکت(ها) هدف را انتخاب کنید (می‌توانید چند مملکت انتخاب کنید):", reply_markup=reply_markup)

    elif data.startswith("select_attack_target_"):
        target_country = data.replace("select_attack_target_", "")
        if "attack_targets" not in context.user_data:
            context.user_data["attack_targets"] = []
            
        if target_country not in context.user_data["attack_targets"]:
            context.user_data["attack_targets"].append(target_country)
        
        selected_text = "\n".join([f"• {c}" for c in context.user_data["attack_targets"]])
        message = f"مملکت‌های انتخاب شده:\n{selected_text}\n\nلطفاً مملکت‌های دیگر را انتخاب کنید یا اتمام را بزنید."
        
        all_users = db.get_all_users()
        target_countries = []
        user_country = db.get_user_countries(user_id)[0]
        allies = db.get_allies(user_country)
        
        for user_id_db, _ in all_users:
            if user_id_db != user_id:
                countries = db.get_user_countries(user_id_db)
                for country in countries:
                    if country not in allies and country not in context.user_data["attack_targets"]:
                        target_countries.append(country)
        
        keyboard = [
            [InlineKeyboardButton(country, callback_data=f"select_attack_target_{country}")]
            for country in target_countries
        ]
        keyboard.append([InlineKeyboardButton("✅ اتمام انتخاب مملکت‌ها", callback_data="confirm_attack_targets")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif data == "confirm_attack_targets":
        if "attack_targets" not in context.user_data or not context.user_data["attack_targets"]:
            await query.edit_message_text("⛔ حداقل یک مملکت را انتخاب کنید!")
            return
            
        selected_countries = context.user_data["attack_targets"]
        selected_text = "\n".join([f"• {c}" for c in selected_countries])
        await query.edit_message_text(f"✅ مملکت‌های انتخاب شده:\n{selected_text}\n\nاکنون امکانات عملیات را انتخاب کنید:")

        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ خطا در پیدا کردن مملکت شما!")
            return
            
        user_country = user_countries[0]
        equipments = db.get_user_equipments(user_id, user_country)
        
        available_equipments = [
            eq_id for eq_id in ATTACK_EQUIPMENTS 
            if eq_id in equipments and equipments[eq_id] > 0
        ]
        
        if not available_equipments:
            await query.edit_message_text("⛔ شما امکانات عملیاتی ندارید!")
            return

        keyboard = [
            [InlineKeyboardButton(EQUIPMENTS[eq_id]["name"], callback_data=f"use_eq_{eq_id}")]
            for eq_id in available_equipments
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="attack")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💥 امکانات عملیات را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("use_eq_"):
        equipment_id = data.replace("use_eq_", "")
        equipment = EQUIPMENTS.get(equipment_id)
        if not equipment:
            await query.edit_message_text("⛔ امکانات مورد نظر یافت نشد!")
            return
            
        context.user_data["attack_equipment"] = equipment_id
        
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ خطا در پیدا کردن مملکت شما!")
            return
            
        user_country = user_countries[0]
        equipments = db.get_user_equipments(user_id, user_country)
        max_quantity = equipments.get(equipment_id, 0)
        
        if max_quantity <= 0:
            await query.edit_message_text("⛔ شما این امکانات را ندارید!")
            return
                    
        context.user_data["max_quantity"] = max_quantity
        
        if equipment_id == "spy":
            if len(context.user_data["attack_targets"]) != 1:
                await query.edit_message_text("⛔ برای عملیات جاسوسی فقط یک مملکت را انتخاب کنید!")
                return
                
            await query.edit_message_text(f"🕵️‍♂️ تعداد جاسوس‌ها را وارد کنید (هر جاسوس یک عملیات دزدی انجام می‌دهد):")
        else:
            await query.edit_message_text(
                f"💥 تعداد {equipment['name']} برای هر مملکت را وارد کنید "
                f"(تعداد کل: {len(context.user_data['attack_targets'])} مملکت × تعداد انتخابی شما)"
            )

    elif data == "support":
        context.user_data["waiting_for_support_msg"] = True
        await query.edit_message_text("📞 پیام خود را برای پشتیبانی ارسال کنید:")

    elif data == "visit_countries":
        cursor = db.conn.cursor()
        cursor.execute('SELECT name, owner_id FROM countries WHERE status = "❌"')
        owned_countries = []
        for country, owner_id in cursor.fetchall():
            cursor.execute('SELECT username FROM users WHERE user_id = ?', (owner_id,))
            result = cursor.fetchone()
            owner_username = result[0] if result else "ناشناس"
            owned_countries.append((country, owner_username))

        if not owned_countries:
            await query.edit_message_text("⛔ هنوز هیچ مملکتی تأسیس نشده است!")
            return

        keyboard = [
            [InlineKeyboardButton(country, callback_data=f"view_country_{country}")]
            for country, _ in owned_countries
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🌍 مملکت مورد نظر برای مشاهده را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("view_country_"):
        country_name = data.replace("view_country_", "")
        
        cursor = db.conn.cursor()
        cursor.execute('SELECT owner_id FROM countries WHERE name = ?', (country_name,))
        result = cursor.fetchone()
        if not result:
            await query.edit_message_text("⛔ مملکت یافت نشد!")
            return
            
        owner_id = result[0]
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (owner_id,))
        result = cursor.fetchone()
        owner_username = result[0] if result else "ناشناس"
        
        equipments = db.get_country_equipments(country_name)
        eq_text = "\n".join([f"{EQUIPMENTS[eq_id]['name']}: {qty}" for eq_id, qty in equipments.items()])
        
        allies = db.get_allies(country_name)
        allies_text = "\n".join([f"• {ally}" for ally in allies]) if allies else "بدون متحد"
        
        message = (
            f"🏰 مملکت: {country_name}\n"
            f"👤 مالک: @{owner_username}\n\n"
            f"🤝 متحدان:\n{allies_text}\n\n"
            f"⚔️ امکانات:\n{eq_text if eq_text else 'بدون امکانات'}"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="visit_countries")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif data == "start_game":
        if user_id not in OWNER_IDS and "start_game" not in db.get_admin_permissions(user_id):
            return

        db.set_game_setting("game_started", "1")
        
        all_countries = []
        cursor = db.conn.cursor()
        cursor.execute('SELECT name, owner_id FROM countries WHERE owner_id IS NOT NULL')
        for country, owner_id in cursor.fetchall():
            cursor.execute('SELECT username FROM users WHERE user_id = ?', (owner_id,))
            result = cursor.fetchone()
            owner_username = result[0] if result else "ناشناس"
            all_countries.append(f"{country} - 👤 مالک: @{owner_username}")
        
        countries_list = "\n".join(all_countries) if all_countries else "هنوز هیچ مملکتی تأسیس نشده است"
        
        channel = db.get_game_setting("channel")
        if channel:
            try:
                await context.bot.send_message(
                    f"@{channel}",
                    f"""
✅ بازی مملکت من شروع شد! ✅

‼️ قوانین بازی ‼️

1. بازی توسط ربات مدیریت می‌شود ⭕️
2. مملکت‌ها می‌توانند با هم متحد شوند ⭕️
3. پس از سقوط، امکان بازگشت نیست ⭕️
4. حداقل شرکت‌کنندگان: {db.get_game_setting('min_players', 0)} ⭕️
5. جایزه برنده: {db.get_game_setting('prize_name', 'تعیین نشده')} ⭕️

🔱 لیست مملکت‌ها 🔱
{countries_list}
"""
                )
            except Exception as e:
                logger.error(f"Failed to send message to channel: {e}")
        
        await query.edit_message_text("✅ بازی با موفقیت شروع شد!")

    elif data == "end_game":
        if user_id not in OWNER_IDS and "end_game" not in db.get_admin_permissions(user_id):
            return

        keyboard = [
            [InlineKeyboardButton("✅ بله، بازی را پایان بده", callback_data="confirm_end_game")],
            [InlineKeyboardButton("❌ خیر، لغو", callback_data="panel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚠️ آیا مطمئنید که می‌خواهید بازی را پایان دهید؟\n\nتمام مملکت‌ها و امکانات بازنشانی خواهند شد و بازی به حالت اولیه بازمی‌گردد.", reply_markup=reply_markup)

    elif data == "confirm_end_game":
        if user_id not in OWNER_IDS and "end_game" not in db.get_admin_permissions(user_id):
            return

        db.end_game()
        
        channel = db.get_game_setting("channel")
        if channel:
            try:
                await context.bot.send_message(
                    f"@{channel}",
                    "🛑 بازی مملکت من به پایان رسید! 🛑\n\n"
                    "همه مملکت‌ها و امکانات بازنشانی شدند. "
                    "برای شروع بازی جدید از دستور /start استفاده کنید."
                )
            except Exception as e:
                logger.error(f"Failed to send message to channel: {e}")
        
        await query.edit_message_text("✅ بازی با موفقیت به پایان رسید و همه چیز بازنشانی شد!")

    elif data == "set_country_price":
        if user_id not in OWNER_IDS and "set_country_price" not in db.get_admin_permissions(user_id):
            return

        available_countries = db.get_available_countries()
        keyboard = [
            [InlineKeyboardButton(country, callback_data=f"setprice_{country}")]
            for country in available_countries
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💰 مملکت مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("setprice_"):
        country = data.replace("setprice_", "")
        context.user_data["setting_price_for"] = country
        await query.edit_message_text(f"💰 قیمت {country} را به عدد وارد کنید:")

    elif data == "set_equipment_price":
        if user_id not in OWNER_IDS and "set_equipment_price" not in db.get_admin_permissions(user_id):
            return

        keyboard = [
            [InlineKeyboardButton(eq["name"], callback_data=f"set_eq_price_{eq_id}")]
            for eq_id, eq in EQUIPMENTS.items()
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚔️ امکان مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("set_eq_price_"):
        equipment_id = data.replace("set_eq_price_", "")
        context.user_data["setting_eq_price_for"] = equipment_id
        await query.edit_message_text(f"💰 قیمت {EQUIPMENTS[equipment_id]['name']} را به عدد وارد کنید:")

    elif data == "set_prize":
        if user_id not in OWNER_IDS and "set_prize" not in db.get_admin_permissions(user_id):
            return

        context.user_data["setting_prize"] = True
        await query.edit_message_text("🏆 نام جایزه را وارد کنید:")

    elif data == "set_min_players":
        if user_id not in OWNER_IDS and "set_min_players" not in db.get_admin_permissions(user_id):
            return

        context.user_data["setting_min_players"] = True
        await query.edit_message_text("👥 حداقل تعداد شرکت‌کنندگان را وارد کنید:")

    elif data.startswith("confirm_payment_"):
        request_id = data.replace("confirm_payment_", "")
        request = payment_requests.get(request_id)
        
        if not request:
            await query.edit_message_text("⛔ درخواست پرداخت یافت نشد یا منقضی شده است!")
            return
            
        try:
            if request["type"] == "country":
                country = request["country"]
                user_id_req = request["user_id"]
                username_req = request["username"]
                
                db.set_country_owner(country, user_id_req, username_req)
                
                channel = db.get_game_setting("channel")
                if channel:
                    try:
                        await context.bot.send_message(
                            f"@{channel}",
                            f"🎉 مملکت {country} توسط @{username_req} تأسیس شد!",
                        )
                    except Exception as e:
                        logger.error(f"Failed to send message to channel: {e}")
                
                await context.bot.send_message(
                    user_id_req,
                    f"✅ تأسیس مملکت {country} با موفقیت انجام شد!",
                )
                
                await query.edit_message_text("✅ پرداخت با موفقیت تایید شد!")
                
            elif request["type"] == "equipment":
                equipment_id = request["equipment_id"]
                quantity = request["quantity"]
                user_id_req = request["user_id"]
                username_req = request["username"]
                equipment = EQUIPMENTS.get(equipment_id)
                
                if not equipment:
                    await query.edit_message_text("⛔ امکانات مورد نظر یافت نشد!")
                    return
                    
                user_countries = db.get_user_countries(user_id_req)
                if not user_countries:
                    await query.edit_message_text("⛔ مملکت کاربر یافت نشد!")
                    return
                    
                user_country = user_countries[0]
                db.add_equipment(user_id_req, user_country, equipment_id, quantity)
                
                channel = db.get_game_setting("channel")
                if channel:
                    try:
                        await context.bot.send_message(
                            f"@{channel}",
                            f"🎉 مملکت {user_country} تعداد {quantity} عدد {equipment['name']} خریداری کرد!",
                        )
                    except Exception as e:
                        logger.error(f"Failed to send message to channel: {e}")
                
                await context.bot.send_message(
                    user_id_req,
                    f"✅ خرید {quantity} عدد {equipment['name']} با موفقیت انجام شد!",
                )
                
                await query.edit_message_text("✅ پرداخت با موفقیت تایید شد!")
                
        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            await query.edit_message_text("⛔ خطا در تایید پرداخت!")
        finally:
            if request_id in payment_requests:
                del payment_requests[request_id]

    elif data.startswith("cancel_payment_"):
        request_id = data.replace("cancel_payment_", "")
        request = payment_requests.get(request_id)
        
        if not request:
            await query.edit_message_text("⛔ درخواست پرداخت یافت نشد یا منقضی شده است!")
            return
            
        try:
            user_id_req = request["user_id"]
            await context.bot.send_message(
                user_id_req,
                "⛔ پرداخت شما توسط ادمین رد شد!",
            )
            await query.edit_message_text("⛔ پرداخت رد شد!")
        except Exception as e:
            logger.error(f"Error canceling payment: {e}")
            await query.edit_message_text("⛔ خطا در رد پرداخت!")
        finally:
            if request_id in payment_requests:
                del payment_requests[request_id]

    elif data == "confirm_attack":
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ خطا در پیدا کردن مملکت شما!")
            return
            
        user_country = user_countries[0]
        target_countries = context.user_data.get("attack_targets", [])
        equipment_id = context.user_data.get("attack_equipment")
        quantity_per_target = context.user_data.get("attack_quantity")
        
        if not target_countries or not equipment_id or not quantity_per_target:
            await query.edit_message_text("⛔ خطا در پردازش عملیات!")
            return

        total_quantity = quantity_per_target * len(target_countries)
        
        if not db.remove_equipment(user_id, user_country, equipment_id, total_quantity):
            await query.edit_message_text("⛔ تعداد امکانات کافی نیست!")
            return

        equipment = EQUIPMENTS.get(equipment_id)
        if not equipment:
            await query.edit_message_text("⛔ امکانات مورد نظر یافت نشد!")
            return

        destroyed_countries = []
        for target_country in target_countries:
            try:
                cursor = db.conn.cursor()
                cursor.execute('SELECT owner_id FROM countries WHERE name = ?', (target_country,))
                result = cursor.fetchone()
                if not result:
                    continue
                    
                owner_id = result[0]
                
                if owner_id == INVINCIBLE_USER:
                    continue
                
                equipments = db.get_user_equipments(owner_id, target_country)
                defense = equipments.get("school", 0)
                shield = equipments.get("shield", 0)
                
                damage_info = DAMAGE_VALUES.get(equipment_id, {"defense": 0, "shield": 0})
                damage_defense_per_target = damage_info["defense"] * quantity_per_target
                damage_shield_per_target = damage_info["shield"] * quantity_per_target

                required_shield = damage_shield_per_target
                required_defense = damage_defense_per_target
                
                if shield >= required_shield:
                    shield_destroyed = required_shield
                    new_shield = shield - shield_destroyed
                    db.remove_equipment(owner_id, target_country, "shield", shield_destroyed)
                else:
                    remaining_damage = (required_shield - shield) * 3
                    total_required_defense = required_defense + remaining_damage
                    
                    if defense >= total_required_defense:
                        shield_destroyed = shield
                        defense_destroyed = total_required_defense
                        db.remove_equipment(owner_id, target_country, "shield", shield_destroyed)
                        db.remove_equipment(owner_id, target_country, "school", defense_destroyed)
                    else:
                        db.destroy_country(target_country)
                        destroyed_countries.append(target_country)
                        try:
                            await context.bot.send_message(
                                owner_id,
                                f"💀 مملکت {target_country} شما سقوط کرد!",
                            )
                        except Exception as e:
                            logger.error(f"Failed to send destruction message: {e}")
                
            except Exception as e:
                logger.error(f"Error processing attack: {e}")

        channel = db.get_game_setting("channel")
        if channel:
            try:
                message = f"💥 مملکت {user_country} به {len(target_countries)} مملکت عملیات انجام داد!\n"
                if destroyed_countries:
                    message += f"مملکت‌های سقوط کرده: {', '.join(destroyed_countries)}\n"
                message += f"امکانات استفاده شده: {total_quantity} {equipment['name']}"
                await context.bot.send_message(f"@{channel}", message)
            except Exception as e:
                logger.error(f"Failed to send message to channel: {e}")

        await query.edit_message_text(f"✅ عملیات با موفقیت انجام شد! {len(destroyed_countries)} مملکت سقوط کردند.")
        context.user_data.pop("attack_targets", None)
        context.user_data.pop("attack_equipment", None)
        context.user_data.pop("attack_quantity", None)
        context.user_data.pop("max_quantity", None)

    elif data == "cancel_attack":
        await query.edit_message_text("⛔ عملیات لغو شد!")
        context.user_data.pop("attack_targets", None)
        context.user_data.pop("attack_equipment", None)
        context.user_data.pop("attack_quantity", None)
        context.user_data.pop("max_quantity", None)

    elif data.startswith("reply_"):
        user_id = int(data.replace("reply_", ""))
        context.user_data["reply_to_user"] = user_id
        await query.edit_message_text("✉️ لطفاً پاسخ خود را بنویسید:")

    elif data == "change_channel":
        if user_id not in OWNER_IDS and "change_channel" not in db.get_admin_permissions(user_id):
            return

        context.user_data["changing_channel"] = True
        await query.edit_message_text("📢 یوزرنیم کانال جدید را وارد کنید (مثال: @channel_username):")

    elif data == "bot_stats":
        if user_id not in OWNER_IDS and "bot_stats" not in db.get_admin_permissions(user_id):
            return

        cursor = db.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 0')
        total_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
        total_banned = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM countries WHERE status = "✅"')
        active_countries = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM countries WHERE status = "❌"')
        owned_countries = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM countries WHERE status = "💀"')
        destroyed_countries = cursor.fetchone()[0]
        required_channels = db.get_required_channels()
        min_players = db.get_game_setting("min_players", 0)
        prize_name = db.get_game_setting("prize_name", "تعیین نشده")
        channel = db.get_game_setting("channel", "cyber43")
        game_started = db.get_game_setting("game_started")
        
        stats_text = f"""
📊 آمار ربات:

👥 تعداد کاربران: {total_users}
🚫 تعداد کاربران بن شده: {total_banned}
🌍 مملکت‌های فعال: {active_countries}
🏰 مملکت‌های تأسیس شده: {owned_countries}
💀 مملکت‌های سقوط کرده: {destroyed_countries}
🎮 وضعیت بازی: {'شروع شده' if game_started else 'شروع نشده'}
🏆 جایزه: {prize_name}
👥 حداقل بازیکنان: {min_players}
📢 کانال اطلاع‌رسانی: @{channel}
📌 کانال‌های اجباری: {len(required_channels)}
"""
        await query.edit_message_text(stats_text)

    elif data == "give_equipment":
        if user_id not in OWNER_IDS and "give_equipment" not in db.get_admin_permissions(user_id):
            return

        all_users = db.get_all_users()
        if not all_users:
            await query.edit_message_text("⛔ هیچ کاربری وجود ندارد!")
            return

        keyboard = []
        for user_id_db, username in all_users:
            user_countries = db.get_user_countries(user_id_db)
            if user_countries:
                country = user_countries[0]
                keyboard.append([InlineKeyboardButton(f"@{username} - {country}", callback_data=f"give_eq_target_{user_id_db}")])

        if not keyboard:
            await query.edit_message_text("⛔ هیچ کاربری با مملکت وجود ندارد!")
            return
            
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🎁 کاربر مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("give_eq_target_"):
        target_user = int(data.replace("give_eq_target_", ""))
        user_countries = db.get_user_countries(target_user)
        if not user_countries:
            await query.edit_message_text("⛔ کاربر مملکت ندارد!")
            return
            
        context.user_data["give_eq_target"] = {"user_id": target_user, "country": user_countries[0]}
        
        keyboard = [
            [InlineKeyboardButton(eq["name"], callback_data=f"give_eq_type_{eq_id}")]
            for eq_id, eq in EQUIPMENTS.items()
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="give_equipment")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚔️ امکان مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("give_eq_type_"):
        equipment_id = data.replace("give_eq_type_", "")
        context.user_data["give_eq_type"] = equipment_id
        await query.edit_message_text(f"🎁 تعداد {EQUIPMENTS[equipment_id]['name']} را وارد کنید:")

    elif data == "give_country":
        if user_id not in OWNER_IDS and "give_country" not in db.get_admin_permissions(user_id):
            return

        context.user_data["give_country_step"] = "select_user"
        await query.edit_message_text("👤 آیدی عددی کاربری که می‌خواهید مملکت را به او بدهید را وارد کنید:")

    elif data.startswith("give_country_"):
        country = data.replace("give_country_", "")
        target_user = context.user_data.get("give_country_user")
        if not target_user:
            await query.edit_message_text("⛔ کاربر یافت نشد!")
            return
            
        cursor = db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user,))
        result = cursor.fetchone()
        
        if not result:
            await query.edit_message_text("⛔ کاربر یافت نشد!")
            return
            
        target_username = result[0] or "ناشناس"
        
        db.set_country_owner(country, target_user, target_username)
        
        await context.bot.send_message(
            target_user,
            f"🎉 مملکت {country} به شما واگذار شد!",
        )
        
        channel = db.get_game_setting("channel")
        if channel:
            try:
                await context.bot.send_message(
                    f"@{channel}",
                    f"🎉 مملکت {country} توسط ادمین به @{target_username} واگذار شد!",
                )
            except Exception as e:
                logger.error(f"Failed to send message to channel: {e}")
        
        await query.edit_message_text(f"✅ مملکت {country} با موفقیت به @{target_username} واگذار شد!")
        context.user_data.pop("give_country_user", None)
        context.user_data.pop("give_country_step", None)

    elif data == "destroy_country":
        if user_id not in OWNER_IDS and "destroy_country" not in db.get_admin_permissions(user_id):
            return

        cursor = db.conn.cursor()
        cursor.execute('SELECT name FROM countries WHERE status = "❌"')
        owned_countries = [row[0] for row in cursor.fetchall()]
        
        if not owned_countries:
            await query.edit_message_text("⛔ هیچ مملکتی وجود ندارد!")
            return

        keyboard = [
            [InlineKeyboardButton(country, callback_data=f"destroy_target_{country}")]
            for country in owned_countries
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💀 مملکت مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("destroy_target_"):
        target_country = data.replace("destroy_target_", "")
        cursor = db.conn.cursor()
        cursor.execute('SELECT owner_id FROM countries WHERE name = ?', (target_country,))
        result = cursor.fetchone()
        
        if not result:
            await query.edit_message_text("⛔ مملکت مورد نظر یافت نشد!")
            return
            
        owner_id = result[0]
        db.destroy_country(target_country)
        
        await context.bot.send_message(
            owner_id,
            f"💀 مملکت {target_country} شما توسط ادمین سقوط کرد!",
        )
        
        channel = db.get_game_setting("channel")
        if channel:
            try:
                await context.bot.send_message(
                    f"@{channel}",
                    f"💀 مملکت {target_country} توسط ادمین سقوط کرد!",
                )
            except Exception as e:
                logger.error(f"Failed to send message to channel: {e}")
        
        await query.edit_message_text(f"✅ مملکت {target_country} با موفقیت سقوط کرد!")

    elif data == "ban_user":
        if user_id not in OWNER_IDS and "ban_user" not in db.get_admin_permissions(user_id):
            return

        all_users = db.get_all_users()
        if not all_users:
            await query.edit_message_text("⛔ هیچ کاربری وجود ندارد!")
            return

        keyboard = [
            [InlineKeyboardButton(f"@{username}", callback_data=f"ban_target_{user_id}")]
            for user_id, username in all_users
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🚫 کاربر مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("ban_target_"):
        target_user = int(data.replace("ban_target_", ""))
        db.ban_user(target_user)
        
        await context.bot.send_message(
            target_user,
            "⛔ شما از ربات بن شده‌اید!",
        )
        
        await query.edit_message_text("✅ کاربر با موفقیت بن شد!")

    elif data == "unban_user":
        if user_id not in OWNER_IDS and "unban_user" not in db.get_admin_permissions(user_id):
            return

        banned_users = db.get_banned_users()
        if not banned_users:
            await query.edit_message_text("⛔ هیچ کاربر بن شده‌ای وجود ندارد!")
            return

        keyboard = [
            [InlineKeyboardButton(f"@{username}", callback_data=f"unban_target_{user_id}")]
            for user_id, username in banned_users
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("✅ کاربر مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("unban_target_"):
        target_user = int(data.replace("unban_target_", ""))
        db.unban_user(target_user)
        
        await context.bot.send_message(
            target_user,
            "✅ شما از بن خارج شدید!",
        )
        
        await query.edit_message_text("✅ کاربر با موفقیت آنبن شد!")

    elif data == "broadcast":
        if user_id not in OWNER_IDS and "broadcast" not in db.get_admin_permissions(user_id):
            return

        context.user_data["broadcasting"] = True
        await query.edit_message_text("📢 پیام همگانی خود را وارد کنید:")

    elif data == "reset_bot":
        if user_id not in OWNER_IDS and "reset_bot" not in db.get_admin_permissions(user_id):
            return

        keyboard = [
            [InlineKeyboardButton("✅ بله", callback_data="confirm_reset")],
            [InlineKeyboardButton("❌ خیر", callback_data="panel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚠️ آیا مطمئنید که می‌خواهید ربات را ریست کنید؟", reply_markup=reply_markup)

    elif data == "confirm_reset":
        if user_id not in OWNER_IDS and "reset_bot" not in db.get_admin_permissions(user_id):
            return

        cursor = db.conn.cursor()
        cursor.execute('DELETE FROM users')
        cursor.execute('DELETE FROM countries')
        cursor.execute('DELETE FROM equipments')
        cursor.execute('DELETE FROM game_settings')
        cursor.execute('DELETE FROM required_channels')
        cursor.execute('DELETE FROM alliances')
        db.conn.commit()
        
        db.initialize_countries()
        db.initialize_settings()
        await query.edit_message_text("✅ ربات با موفقیت ریست شد!")

    elif data == "add_admin":
        if user_id not in OWNER_IDS:
            return

        all_users = db.get_all_users()
        if not all_users:
            await query.edit_message_text("⛔ هیچ کاربری وجود ندارد!")
            return

        keyboard = [
            [InlineKeyboardButton(f"@{username}", callback_data=f"add_admin_target_{user_id}")]
            for user_id, username in all_users
            if not db.is_admin(user_id) and user_id not in OWNER_IDS
        ]
        
        if not keyboard:
            await query.edit_message_text("⛔ همه کاربران ادمین هستند یا کاربری وجود ندارد!")
            return
            
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("👤 کاربر مورد نظر را به عنوان ادمین انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("add_admin_target_"):
        target_user = int(data.replace("add_admin_target_", ""))
        context.user_data["adding_admin"] = target_user
        
        keyboard = [
            [InlineKeyboardButton("✅ تایید", callback_data="confirm_add_admin")],
            [InlineKeyboardButton("❌ لغو", callback_data="panel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("آیا مطمئنید که می‌خواهید این کاربر را به عنوان ادمین اضافه کنید؟", reply_markup=reply_markup)

    elif data == "confirm_add_admin":
        if user_id not in OWNER_IDS:
            return

        target_user = context.user_data.get("adding_admin")
        if not target_user:
            await query.edit_message_text("⛔ خطا در پردازش درخواست!")
            return
            
        cursor = db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user,))
        result = cursor.fetchone()
        
        if not result:
            await query.edit_message_text("⛔ کاربر یافت نشد!")
            return
            
        target_username = result[0] or "ناشناس"
        
        db.add_admin(target_user, [])
        
        await context.bot.send_message(
            target_user,
            "🎉 شما به عنوان ادمین ربات منصوب شدید!",
        )
        
        await query.edit_message_text(f"✅ کاربر @{target_username} با موفقیت به عنوان ادمین اضافه شد!")
        context.user_data.pop("adding_admin", None)

    elif data == "manage_admin_permissions":
        if user_id not in OWNER_IDS:
            return

        all_admins = db.get_all_admins()
        if not all_admins:
            await query.edit_message_text("⛔ هیچ ادمینی وجود ندارد!")
            return

        keyboard = [
            [InlineKeyboardButton(f"@{username}", callback_data=f"manage_admin_{admin_id}")]
            for admin_id, username, _ in all_admins
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("👤 ادمین مورد نظر را برای مدیریت دسترسی انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("manage_admin_"):
        admin_id = int(data.replace("manage_admin_", ""))
        context.user_data["managing_admin"] = admin_id
        
        cursor = db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (admin_id,))
        result = cursor.fetchone()
        
        if not result:
            await query.edit_message_text("⛔ ادمین یافت نشد!")
            return
            
        admin_username = result[0] or "ناشناس"
        
        current_permissions = db.get_admin_permissions(admin_id)
        
        keyboard = []
        for perm_id, perm_name in ADMIN_PERMISSIONS.items():
            if perm_id in ["add_admin", "manage_admin_permissions"] and user_id != OWNER_IDS[0]:
                continue
                
            checked = "✅" if perm_id in current_permissions else "❌"
            keyboard.append([InlineKeyboardButton(f"{checked} {perm_name}", callback_data=f"toggle_perm_{perm_id}")])
        
        keyboard.append([InlineKeyboardButton("💾 ذخیره تغییرات", callback_data="save_admin_permissions")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="manage_admin_permissions")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🔧 مدیریت دسترسی ادمین @{admin_username}:\n\n"
            "✅ = فعال | ❌ = غیرفعال\n\n"
            "برای تغییر وضعیت هر دسترسی روی آن کلیک کنید:",
            reply_markup=reply_markup
        )

    elif data.startswith("toggle_perm_"):
        if user_id not in OWNER_IDS:
            return

        perm_id = data.replace("toggle_perm_", "")
        admin_id = context.user_data.get("managing_admin")
        
        if not admin_id:
            await query.edit_message_text("⛔ خطا در پردازش درخواست!")
            return
            
        current_permissions = db.get_admin_permissions(admin_id)
        
        if perm_id in current_permissions:
            current_permissions.remove(perm_id)
        else:
            current_permissions.append(perm_id)
        
        context.user_data["temp_permissions"] = current_permissions
        
        cursor = db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (admin_id,))
        result = cursor.fetchone()
        
        if not result:
            await query.edit_message_text("⛔ ادمین یافت نشد!")
            return
            
        admin_username = result[0] or "ناشناس"
        
        keyboard = []
        for perm_id_db, perm_name in ADMIN_PERMISSIONS.items():
            if perm_id_db in ["add_admin", "manage_admin_permissions"] and user_id != OWNER_IDS[0]:
                continue
                
            checked = "✅" if perm_id_db in current_permissions else "❌"
            keyboard.append([InlineKeyboardButton(f"{checked} {perm_name}", callback_data=f"toggle_perm_{perm_id_db}")])
        
        keyboard.append([InlineKeyboardButton("💾 ذخیره تغییرات", callback_data="save_admin_permissions")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="manage_admin_permissions")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🔧 مدیریت دسترسی ادمین @{admin_username}:\n\n"
            "✅ = فعال | ❌ = غیرفعال\n\n"
            "برای تغییر وضعیت هر دسترسی روی آن کلیک کنید:",
            reply_markup=reply_markup
        )

    elif data == "save_admin_permissions":
        if user_id not in OWNER_IDS:
            return

        admin_id = context.user_data.get("managing_admin")
        temp_permissions = context.user_data.get("temp_permissions", [])
        
        if not admin_id:
            await query.edit_message_text("⛔ خطا در پردازش درخواست!")
            return
            
        db.add_admin(admin_id, temp_permissions)
        
        cursor = db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (admin_id,))
        result = cursor.fetchone()
        
        if not result:
            await query.edit_message_text("⛔ ادمین یافت نشد!")
            return
            
        admin_username = result[0] or "ناشناس"
        
        await query.edit_message_text(f"✅ دسترسی‌های ادمین @{admin_username} با موفقیت ذخیره شد!")
        
        context.user_data.pop("managing_admin", None)
        context.user_data.pop("temp_permissions", None)

    elif data == "add_required_channel":
        if user_id not in OWNER_IDS and "manage_channels" not in db.get_admin_permissions(user_id):
            return

        context.user_data["adding_required_channel"] = True
        await query.edit_message_text("📢 یوزرنیم کانال را برای الزام عضویت وارد کنید (بدون @):")

    elif data == "remove_required_channel":
        if user_id not in OWNER_IDS and "manage_channels" not in db.get_admin_permissions(user_id):
            return

        required_channels = db.get_required_channels()
        if not required_channels:
            await query.edit_message_text("⛔ کانال اجباری وجود ندارد!")
            return

        keyboard = [
            [InlineKeyboardButton(f"@{channel}", callback_data=f"remove_channel_{channel}")]
            for channel in required_channels
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("➖ کانال مورد نظر برای حذف را انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("remove_channel_"):
        channel = data.replace("remove_channel_", "")
        db.remove_required_channel(channel)
        await query.edit_message_text(f"✅ کانال @{channel} از لیست الزام عضویت حذف شد!")

    elif data == "back_to_main":
        await show_main_menu(query, context, user_id)
        
    elif data == "refresh":
        await show_main_menu(query, context, user_id)
        
    elif data == "send_to_channel":
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما مملکتی ندارید!")
            return
            
        context.user_data["sending_to_channel"] = True
        await query.edit_message_text("📢 پیام خود را برای ارسال به کانال وارد کنید:")
        
    elif data == "alliance_request":
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما مملکتی ندارید!")
            return
            
        user_country = user_countries[0]
        allies = db.get_allies(user_country)
        
        cursor = db.conn.cursor()
        cursor.execute('SELECT name, owner_id FROM countries WHERE status = "❌" AND owner_id != ?', (user_id,))
        other_countries = []
        for country, owner_id in cursor.fetchall():
            if country not in allies:
                cursor.execute('SELECT username FROM users WHERE user_id = ?', (owner_id,))
                result = cursor.fetchone()
                owner_username = result[0] if result else "ناشناس"
                other_countries.append((country, owner_username))
        
        if not other_countries:
            await query.edit_message_text("⛔ هیچ مملکتی برای درخواست اتحاد وجود ندارد!")
            return
            
        keyboard = [
            [InlineKeyboardButton(f"{country} - @{owner}", callback_data=f"select_alliance_target_{country}")]
            for country, owner in other_countries
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🤝 مملکت مورد نظر برای درخواست اتحاد را انتخاب کنید:", reply_markup=reply_markup)
        
    elif data.startswith("select_alliance_target_"):
        target_country = data.replace("select_alliance_target_", "")
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما مملکتی ندارید!")
            return
            
        user_country = user_countries[0]
        
        if db.are_allies(user_country, target_country):
            await query.edit_message_text("⛔ شما قبلاً با این مملکت متحد هستید!")
            return
            
        request_id = f"{user_country}_{target_country}"
        if request_id in alliance_requests:
            await query.edit_message_text("⛔ درخواست اتحاد شما قبلاً برای این مملکت ارسال شده است!")
            return
            
        alliance_requests[request_id] = {
            "sender_country": user_country,
            "receiver_country": target_country,
            "sender_id": user_id,
            "receiver_id": db.get_country_owner(target_country)
        }
        
        try:
            await context.bot.send_message(
                alliance_requests[request_id]["receiver_id"],
                f"🤝 درخواست اتحاد جدید!\n\n"
                f"مملکت {user_country} از شما برای اتحاد درخواست داده است.\n"
                f"در صورت قبول:\n"
                f"- نمی‌توانید به یکدیگر عملیات انجام دهید\n"
                f"- می‌توانید امکانات مبادله کنید\n"
                f"- در صورت پیروزی، جایزه تقسیم می‌شود",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ قبول اتحاد", callback_data=f"accept_alliance_{request_id}"),
                        InlineKeyboardButton("❌ رد درخواست", callback_data=f"reject_alliance_{request_id}")
                    ]
                ])
            )
        except Exception as e:
            logger.error(f"Failed to send alliance request: {e}")
            del alliance_requests[request_id]
            await query.edit_message_text("⛔ خطا در ارسال درخواست اتحاد!")
            return
            
        await query.edit_message_text(f"✅ درخواست اتحاد شما به مملکت {target_country} ارسال شد!")
        
    elif data.startswith("accept_alliance_"):
        request_id = data.replace("accept_alliance_", "")
        request = alliance_requests.get(request_id)
        
        if not request:
            await query.edit_message_text("⛔ درخواست اتحاد یافت نشد!")
            return
            
        db.create_alliance(request["sender_country"], request["receiver_country"])
        
        try:
            await context.bot.send_message(
                request["sender_id"],
                f"✅ درخواست اتحاد شما با مملکت {request['receiver_country']} پذیرفته شد!\n\n"
                "اکنون شما متحد هستید و نمی‌توانید به یکدیگر عملیات انجام دهید."
            )
            
            await context.bot.send_message(
                request["receiver_id"],
                f"✅ شما با مملکت {request['sender_country']} متحد شدید!"
            )
            
            channel = db.get_game_setting("channel")
            if channel:
                try:
                    await context.bot.send_message(
                        f"@{channel}",
                        f"🤝 مملکت‌های {request['sender_country']} و {request['receiver_country']} با هم متحد شدند!",
                    )
                except Exception as e:
                    logger.error(f"Failed to send message to channel: {e}")
        except Exception as e:
            logger.error(f"Failed to notify alliance acceptance: {e}")
        
        await query.edit_message_text(f"✅ اتحاد با مملکت {request['sender_country']} ایجاد شد!")
        del alliance_requests[request_id]
        
    elif data.startswith("reject_alliance_"):
        request_id = data.replace("reject_alliance_", "")
        request = alliance_requests.get(request_id)
        
        if not request:
            await query.edit_message_text("⛔ درخواست اتحاد یافت نشد!")
            return
            
        try:
            await context.bot.send_message(
                request["sender_id"],
                f"⛔ درخواست اتحاد شما با مملکت {request['receiver_country']} رد شد."
            )
        except Exception as e:
            logger.error(f"Failed to notify alliance rejection: {e}")
        
        await query.edit_message_text(f"⛔ درخواست اتحاد از مملکت {request['sender_country']} رد شد!")
        del alliance_requests[request_id]

    elif data == "send_to_ally":
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما مملکتی ندارید!")
            return
            
        user_country = user_countries[0]
        allies = db.get_allies(user_country)
        
        if not allies:
            await query.edit_message_text("⛔ شما متحدی ندارید!")
            return
            
        context.user_data["sending_to_ally"] = True
        
        keyboard = [
            [InlineKeyboardButton(ally, callback_data=f"select_ally_target_{ally}")]
            for ally in allies
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🤝 متحد مورد نظر را انتخاب کنید:", reply_markup=reply_markup)
        
    elif data.startswith("select_ally_target_"):
        target_country = data.replace("select_ally_target_", "")
        context.user_data["ally_target"] = target_country
        
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما مملکتی ندارید!")
            return
            
        user_country = user_countries[0]
        equipments = db.get_user_equipments(user_id, user_country)
        
        if not equipments:
            await query.edit_message_text("⛔ شما امکاناتی ندارید!")
            return
            
        keyboard = [
            [InlineKeyboardButton(f"{EQUIPMENTS[eq_id]['name']} ({qty})", callback_data=f"select_ally_eq_{eq_id}")]
            for eq_id, qty in equipments.items() if qty > 0
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="send_to_ally")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚔️ امکان مورد نظر برای ارسال را انتخاب کنید:", reply_markup=reply_markup)
        
    elif data.startswith("select_ally_eq_"):
        equipment_id = data.replace("select_ally_eq_", "")
        context.user_data["ally_equipment"] = equipment_id
        
        user_countries = db.get_user_countries(user_id)
        if not user_countries:
            await query.edit_message_text("⛔ شما مملکتی ندارید!")
            return
            
        user_country = user_countries[0]
        equipments = db.get_user_equipments(user_id, user_country)
        max_quantity = equipments.get(equipment_id, 0)
        
        await query.edit_message_text(f"📦 تعداد {EQUIPMENTS[equipment_id]['name']} برای ارسال را وارد کنید (حداکثر: {max_quantity}):")

    elif data.startswith("spy_report_"):
        operation_id = data.replace("spy_report_", "")
        operation = spy_operations.get(operation_id)
        
        if not operation:
            await query.edit_message_text("⛔ عملیات جاسوسی یافت نشد!")
            return
            
        target_country = operation["target_country"]
        target_owner_id = operation["target_owner_id"]
        target_equipments = db.get_user_equipments(target_owner_id, target_country)
        
        if not target_equipments:
            await query.edit_message_text("⛔ هدف هیچ امکاناتی ندارد!")
            return
            
        keyboard = [
            [InlineKeyboardButton(f"{EQUIPMENTS[eq_id]['name']} ({qty})", callback_data=f"steal_{eq_id}_{operation_id}")]
            for eq_id, qty in target_equipments.items() if qty > 0
        ]
        keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data=f"cancel_steal_{operation_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🕵️‍♂️ کدام امکان را می‌خواهید بدزدید؟", reply_markup=reply_markup)

    elif data.startswith("steal_"):
        parts = data.split("_")
        equipment_id = parts[1]
        operation_id = parts[2]
        operation = spy_operations.get(operation_id)
        
        if not operation:
            await query.edit_message_text("⛔ عملیات جاسوسی یافت نشد!")
            return
            
        attacker_id = operation["attacker_id"]
        attacker_country = operation["attacker_country"]
        target_country = operation["target_country"]
        target_owner_id = operation["target_owner_id"]
        
        if not db.remove_equipment(target_owner_id, target_country, equipment_id, 1):
            await query.edit_message_text("⛔ امکان مورد نظر در هدف یافت نشد!")
            return
            
        db.add_equipment(attacker_id, attacker_country, equipment_id, 1)
        
        await context.bot.send_message(
            attacker_id,
            f"✅ جاسوس شما با موفقیت 1 عدد {EQUIPMENTS[equipment_id]['name']} از مملکت {target_country} دزدید!"
        )
        
        await context.bot.send_message(
            target_owner_id,
            f"⚠️ یک جاسوس از مملکت {attacker_country} 1 عدد {EQUIPMENTS[equipment_id]['name']} شما را دزدید!"
        )
        
        channel = db.get_game_setting("channel")
        if channel:
            try:
                await context.bot.send_message(
                    f"@{channel}",
                    f"🕵️‍♂️ جاسوس مملکت {attacker_country} با موفقیت از مملکت {target_country} دزدی کرد!",
                )
            except Exception as e:
                logger.error(f"Failed to send message to channel: {e}")
        
        await query.edit_message_text(f"✅ دزدی با موفقیت انجام شد! 1 عدد {EQUIPMENTS[equipment_id]['name']} به مملکت شما اضافه شد.")
        del spy_operations[operation_id]

    elif data.startswith("cancel_steal_"):
        operation_id = data.replace("cancel_steal_", "")
        operation = spy_operations.get(operation_id)
        
        if operation:
            del spy_operations[operation_id]
            await query.edit_message_text("⛔ عملیات دزدی لغو شد!")
        else:
            await query.edit_message_text("⛔ عملیات جاسوسی یافت نشد!")

    else:
        logger.warning(f"Unknown callback data: {data}")
        await query.edit_message_text("⛔ دستور نامعتبر!")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "کاربر ناشناس"
    message_text = update.message.text

    if db.is_banned(user_id):
        return

    try:
        if "setting_price_for" in context.user_data:
            country = context.user_data["setting_price_for"]
            try:
                price = int(message_text)
                if price <= 0:
                    await update.message.reply_text("⛔ قیمت باید بیشتر از صفر باشد!")
                    return
                    
                db.set_country_price(country, price)
                await update.message.reply_text(f"✅ قیمت {country} به {price} داگز تنظیم شد.")
                context.user_data.pop("setting_price_for", None)
            except ValueError:
                await update.message.reply_text("⛔ لطفاً یک عدد معتبر وارد کنید!")
            return

        elif "setting_eq_price_for" in context.user_data:
            equipment_id = context.user_data["setting_eq_price_for"]
            try:
                price = int(message_text)
                if price <= 0:
                    await update.message.reply_text("⛔ قیمت باید بیشتر من صفر باشد!")
                    return
                    
                EQUIPMENTS[equipment_id]["price"] = price
                await update.message.reply_text(f"✅ قیمت {EQUIPMENTS[equipment_id]['name']} به {price} داگز تنظیم شد.")
                context.user_data.pop("setting_eq_price_for", None)
            except ValueError:
                await update.message.reply_text("⛔ لطفاً یک عدد معتبر وارد کنید!")
            return

        elif "selected_equipment" in context.user_data:
            equipment_id = context.user_data["selected_equipment"]
            equipment = EQUIPMENTS.get(equipment_id)
            if not equipment:
                await update.message.reply_text("⛔ امکانات مورد نظر یافت نشد!")
                return
                
            try:
                quantity = int(message_text)
                if quantity <= 0:
                    await update.message.reply_text("⛔ تعداد باید بیشتر از صفر باشد!")
                    return
                    
                await update.message.reply_text(
                    f"💰 مبلغ قابل پرداخت: {equipment['price'] * quantity} داگز\n\n"
                    f"لطفاً پیام پرداخت خود را ارسال کنید (متن دلخواه). درخواست شما به ادمین ارسال خواهد شد."
                )
                context.user_data["equipment"] = equipment_id
                context.user_data["quantity"] = quantity
                context.user_data.pop("selected_equipment", None)
            except ValueError:
                await update.message.reply_text("⛔ لطفاً یک عدد معتبر وارد کنید!")
            return

        elif "attack_equipment" in context.user_data:
            equipment_id = context.user_data["attack_equipment"]
            equipment = EQUIPMENTS.get(equipment_id)
            if not equipment:
                await update.message.reply_text("⛔ امکانات مورد نظر یافت نشد!")
                return
                
            try:
                quantity = int(message_text)
                max_quantity = context.user_data.get("max_quantity", 0)
                target_count = len(context.user_data.get("attack_targets", []))
                total_needed = quantity * target_count
                
                if quantity <= 0 or total_needed > max_quantity:
                    msg = f"⛔ تعداد باید بین 1 تا {max_quantity//target_count} برای هر مملکت باشد! (کل مورد نیاز: {total_needed})"
                    await update.message.reply_text(msg)
                    return
                    
                context.user_data["attack_quantity"] = quantity
                
                if equipment_id == "spy":
                    keyboard = [
                        [InlineKeyboardButton("✅ تایید عملیات جاسوسی", callback_data="confirm_spy")],
                        [InlineKeyboardButton("❌ لغو عملیات", callback_data="cancel_attack")],
                    ]
                else:
                    keyboard = [
                        [InlineKeyboardButton("✅ تایید عملیات", callback_data="confirm_attack")],
                        [InlineKeyboardButton("❌ لغو عملیات", callback_data="cancel_attack")],
                    ]
                    
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"⚠️ آیا مطمئنید که می‌خواهید با {quantity} {equipment['name']} برای هر مملکت عملیات انجام دهید؟ "
                    f"(تعداد کل: {total_needed} برای {target_count} مملکت)",
                    reply_markup=reply_markup,
                )
            except ValueError:
                await update.message.reply_text("⛔ لطفاً یک عدد معتبر وارد کنید!")
            return

        elif "waiting_for_support_msg" in context.user_data:
            for owner_id in OWNER_IDS:
                try:
                    await context.bot.send_message(
                        owner_id,
                        f"📩 پیام پشتیبانی از @{username}:\n\n{message_text}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📤 پاسخ", callback_data=f"reply_{user_id}")]
                        ])
                    )
                except Exception as e:
                    logger.error(f"Failed to send support message to owner {owner_id}: {e}")
            await update.message.reply_text("✅ پیام شما به پشتیبانی ارسال شد!")
            context.user_data.pop("waiting_for_support_msg", None)
            return

        elif "reply_to_user" in context.user_data:
            reply_user_id = context.user_data["reply_to_user"]
            await context.bot.send_message(
                reply_user_id,
                f"📩 پاسخ پشتیبانی:\n\n{message_text}",
            )
            await update.message.reply_text("✅ پاسخ شما ارسال شد!")
            context.user_data.pop("reply_to_user", None)
            return

        elif "setting_prize" in context.user_data:
            db.set_game_setting("prize_name", message_text)
            await update.message.reply_text(f"✅ جایزه با موفقیت تنظیم شد: {message_text}")
            context.user_data.pop("setting_prize", None)
            return

        elif "setting_min_players" in context.user_data:
            try:
                min_players = int(message_text)
                if min_players < 0:
                    await update.message.reply_text("⛔ تعداد باید بیشتر من صفر باشد!")
                    return
                    
                db.set_game_setting("min_players", str(min_players))
                await update.message.reply_text(f"✅ حداقل شرکت‌کنندگان به {min_players} تنظیم شد!")
                context.user_data.pop("setting_min_players", None)
            except ValueError:
                await update.message.reply_text("⛔ لطفاً یک عدد معتبر وارد کنید!")
            return

        elif "changing_channel" in context.user_data:
            message_text = message_text.strip()
            if message_text.startswith("@"):
                channel_username = message_text[1:]
                db.set_game_setting("channel", channel_username)
                await update.message.reply_text(f"✅ کانال اطلاع‌رسانی به @{channel_username} تغییر یافت!")
            else:
                await update.message.reply_text("⛔ لطفاً یوزرنیم کانال را به درستی وارد کنید (مثال: @channel_username)")
            context.user_data.pop("changing_channel", None)
            return

        elif "give_eq_type" in context.user_data:
            target_info = context.user_data.get("give_eq_target")
            equipment_id = context.user_data.get("give_eq_type")
            
            if not target_info or not equipment_id:
                await update.message.reply_text("⛔ خطا در پردازش درخواست!")
                return
                
            try:
                quantity = int(message_text)
                if quantity <= 0:
                    await update.message.reply_text("⛔ تعداد باید بیشتر از صفر باشد!")
                    return
                    
                db.add_equipment(target_info["user_id"], target_info["country"], equipment_id, quantity)
                
                await context.bot.send_message(
                    target_info["user_id"],
                    f"🎁 ادمین به شما {quantity} عدد {EQUIPMENTS[equipment_id]['name']} هدیه داد!",
                )
                
                await update.message.reply_text(f"✅ امکانات با موفقیت ارسال شد!")
                
            except ValueError:
                await update.message.reply_text("⛔ لطفاً یک عدد معتبر وارد کنید!")
            finally:
                context.user_data.pop("give_eq_target", None)
                context.user_data.pop("give_eq_type", None)
            return

        elif "broadcasting" in context.user_data:
            all_users = db.get_all_users()
            sent = 0
            failed = 0
            
            for user_id_db, username in all_users:
                try:
                    await context.bot.send_message(
                        user_id_db,
                        f"📢 پیام همگانی از ادمین:\n\n{message_text}",
                    )
                    sent += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast to {user_id_db}: {e}")
                    failed += 1
                    
            await update.message.reply_text(f"✅ پیام به {sent} کاربر ارسال شد. ({failed} ناموفق)")
            context.user_data.pop("broadcasting", None)
            return

        elif "give_country_step" in context.user_data:
            if context.user_data["give_country_step"] == "select_user":
                try:
                    target_user = int(message_text)
                    cursor = db.conn.cursor()
                    cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user,))
                    result = cursor.fetchone()
                    
                    if not result:
                        await update.message.reply_text("⛔ کاربر یافت نشد!")
                        return
                    
                    context.user_data["give_country_user"] = target_user
                    context.user_data["give_country_step"] = "select_country"
                    
                    available_countries = db.get_available_countries()
                    if not available_countries:
                        await update.message.reply_text("⛔ هیچ مملکتی برای واگذاری موجود نیست!")
                        context.user_data.pop("give_country_step", None)
                        context.user_data.pop("give_country_user", None)
                        return
                    
                    keyboard = [
                        [InlineKeyboardButton(country, callback_data=f"give_country_{country}")]
                        for country in available_countries
                    ]
                    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="panel")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("🏰 مملکت مورد نظر را انتخاب کنید:", reply_markup=reply_markup)
                except ValueError:
                    await update.message.reply_text("⛔ لطفاً یک آیدی عددی معتبر وارد کنید!")
            return

        elif "selected_country" in context.user_data:
            country = context.user_data["selected_country"]
            price = db.get_country_price(country)
            
            if not country or not price:
                await update.message.reply_text("⛔ خطا در پردازش پرداخت!")
                return
                
            request_id = str(uuid.uuid4())
            
            payment_requests[request_id] = {
                "type": "country",
                "user_id": user_id,
                "username": username,
                "country": country,
                "price": price,
                "message_text": message_text
            }
            
            for owner_id in OWNER_IDS:
                try:
                    await context.bot.send_message(
                        owner_id,
                        f"💳 درخواست پرداخت برای تأسیس مملکت:\n\n"
                        f"مملکت: {country}\n"
                        f"قیمت: {price} داگز\n"
                        f"کاربر: @{username}\n\n"
                        f"پیام پرداخت:\n{message_text}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"confirm_payment_{request_id}")],
                            [InlineKeyboardButton("❌ رد پرداخت", callback_data=f"cancel_payment_{request_id}")],
                        ])
                    )
                except Exception as e:
                    logger.error(f"Failed to send payment request to owner {owner_id}: {e}")
            
            await update.message.reply_text("✅ درخواست پرداخت شما به ادمین ارسال شد!")
            context.user_data.pop("selected_country", None)
            return

        elif "equipment" in context.user_data and "quantity" in context.user_data:
            equipment_id = context.user_data["equipment"]
            quantity = context.user_data["quantity"]
            equipment = EQUIPMENTS.get(equipment_id)
            
            if not equipment:
                await update.message.reply_text("⛔ خطا در پردازش پرداخت!")
                return
                
            price = equipment["price"] * quantity
            
            request_id = str(uuid.uuid4())
            
            payment_requests[request_id] = {
                "type": "equipment",
                "user_id": user_id,
                "username": username,
                "equipment_id": equipment_id,
                "quantity": quantity,
                "price": price,
                "message_text": message_text
            }
            
            for owner_id in OWNER_IDS:
                try:
                    await context.bot.send_message(
                        owner_id,
                        f"💳 درخواست پرداخت برای خرید امکانات:\n\n"
                        f"امکانات: {equipment['name']}\n"
                        f"تعداد: {quantity}\n"
                        f"قیمت: {price} داگز\n"
                        f"کاربر: @{username}\n\n"
                        f"پیام پرداخت:\n{message_text}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"confirm_payment_{request_id}")],
                            [InlineKeyboardButton("❌ رد پرداخت", callback_data=f"cancel_payment_{request_id}")],
                        ])
                    )
                except Exception as e:
                    logger.error(f"Failed to send payment request to owner {owner_id}: {e}")
            
            await update.message.reply_text("✅ درخواست پرداخت شما به ادمین ارسال شد!")
            context.user_data.pop("equipment", None)
            context.user_data.pop("quantity", None)
            return

        elif "adding_required_channel" in context.user_data:
            channel_username = message_text.strip()
            if not channel_username:
                await update.message.reply_text("⛔ نام کانال نمی‌تواند خالی باشد!")
                return
                
            channel_username = channel_username.lstrip('@')
            db.add_required_channel(channel_username)
            await update.message.reply_text(f"✅ کانال @{channel_username} به لیست الزام عضویت افزوده شد!")
            context.user_data.pop("adding_required_channel", None)
            return
            
        elif "sending_to_channel" in context.user_data:
            channel = db.get_game_setting("channel")
            if not channel:
                await update.message.reply_text("⛔ کانال اطلاع‌رسانی تنظیم نشده است!")
                context.user_data.pop("sending_to_channel", None)
                return
                
            user_countries = db.get_user_countries(user_id)
            if not user_countries:
                await update.message.reply_text("⛔ شما مملکتی ندارید!")
                context.user_data.pop("sending_to_channel", None)
                return
                
            user_country = user_countries[0]
            username = update.effective_user.username or "ناشناس"
            
            try:
                await context.bot.send_message(
                    f"@{channel}",
                    f"📢 پیام از مملکت {user_country}:\n"
                    f"👤 فرستنده: @{username}\n\n"
                    f"{message_text}"
                )
                await update.message.reply_text("✅ پیام شما با موفقیت به کانال ارسال شد!")
            except Exception as e:
                logger.error(f"Failed to send message to channel: {e}")
                await update.message.reply_text("⛔ خطا در ارسال پیام به کانال!")
                
            context.user_data.pop("sending_to_channel", None)
            return

        elif "sending_to_ally" in context.user_data and "ally_target" in context.user_data and "ally_equipment" in context.user_data:
            try:
                quantity = int(message_text)
                if quantity <= 0:
                    await update.message.reply_text("⛔ تعداد باید بیشتر از صفر باشد!")
                    return
                    
                user_countries = db.get_user_countries(user_id)
                if not user_countries:
                    await update.message.reply_text("⛔ شما مملکتی ندارید!")
                    return
                    
                user_country = user_countries[0]
                equipment_id = context.user_data["ally_equipment"]
                target_country = context.user_data["ally_target"]
                
                if not db.remove_equipment(user_id, user_country, equipment_id, quantity):
                    await update.message.reply_text("⛔ تعداد امکانات کافی نیست!")
                    return
                    
                target_owner = db.get_country_owner(target_country)
                if not target_owner:
                    await update.message.reply_text("⛔ مملکت مقصد یافت نشد!")
                    return
                    
                db.add_equipment(target_owner, target_country, equipment_id, quantity)
                
                await context.bot.send_message(
                    target_owner,
                    f"🎁 مملکت {user_country} برای شما {quantity} عدد {EQUIPMENTS[equipment_id]['name']} ارسال کرد!",
                )
                
                await update.message.reply_text(f"✅ {quantity} عدد {EQUIPMENTS[equipment_id]['name']} با موفقیت به مملکت {target_country} ارسال شد!")
                
            except ValueError:
                await update.message.reply_text("⛔ لطفاً یک عدد معتبر وارد کنید!")
            finally:
                context.user_data.pop("sending_to_ally", None)
                context.user_data.pop("ally_target", None)
                context.user_data.pop("ally_equipment", None)
            return

    except Exception as e:
        logger.error(f"Error in message_handler: {e}")
        await update.message.reply_text("⛔ خطای سیستمی رخ داد!")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("panel", panel))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error)

    application.run_polling()

if __name__ == "__main__":
    main()