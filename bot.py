import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import config
import sqlite3
import os
from datetime import datetime
import pytz

bot = telebot.TeleBot(config.API)
# переменные
DB_NAME = 'database.db'
DB_PATH = DB_NAME

LOG = "Логи: "

# кнопки
btn_1course = InlineKeyboardButton(text='1 курс', callback_data="select_course_1")
btn_2course = InlineKeyboardButton(text='2 курс', callback_data="select_course_2")
btn_3course = InlineKeyboardButton(text='3 курс', callback_data="select_course_3")
btn_4course = InlineKeyboardButton(text='4 курс', callback_data="select_course_4")
btn_5course = InlineKeyboardButton(text='5 курс', callback_data="select_course_5")



# клавиатуры
keyboard_courses = InlineKeyboardMarkup(row_width=2)
keyboard_courses.add(btn_1course, btn_2course, btn_3course, btn_4course, btn_5course)

# проверки
if os.path.exists(DB_PATH):
	print(f'{LOG}бд есть!')
else: 
	connect = sqlite3.connect(DB_PATH)
	cursor = connect.cursor()
	cursor.execute("""
		CREATE TABLE users (
			id INTEGER,
			message INTEGER, 
			groups INTEGER,
			time_registration TIME

		)
		""")

	connect.commit()
	connect.close()
	print(f"{LOG}бд создана")

# функции
def now_time():
    now = datetime.now()
    tz = pytz.timezone('Europe/Moscow')
    now_moscow = now.astimezone(tz)
    current_time = now_moscow.strftime("%H:%M")
    current_date = now_moscow.strftime("%m.%d.%Y")
    date = f"{current_date} {current_time}"
    return date

# команды
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    message_id = message.id
    time = now_time()
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("""INSERT INTO users (id, message, time_registration)
                          VALUES (?, ?, ?)""", (user_id, message_id, time))
        connect.commit()
        print(f"{LOG}зарегистрирован новый пользователь")
    else:
        cursor.execute("""UPDATE users
                          SET message = ?
                          WHERE id = ?""", (message_id, user_id))
        connect.commit()
        print(f"{LOG}пользователь уже существует")
    connect.close()
    
    bot.send_message(message.chat.id, text="Выберите курс:", reply_markup=keyboard_courses)


@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
	if call.data == "select_course_1":
		pass




print("бот запущен...")
bot.polling()