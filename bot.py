import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import config
import sqlite3
import os
from datetime import datetime
import pytz
import parser

bot = telebot.TeleBot(config.API)
# переменные
DB_NAME = 'database.db'
DB_PATH = DB_NAME

LOG = "Логи: "


# кнопки
x = parser.table_courses()
buttons = []
for i in range(len(x)):
    button = InlineKeyboardButton(text=f"{i+1} курс", callback_data=f"select_course_{i+1}")
    buttons.append(button)


# клавиатуры
keyboard_courses = InlineKeyboardMarkup(row_width=2)
keyboard_courses.add(*buttons)



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
    print(call.data)
    if (call.data).split("_")[0] == "select" and (call.data).split("_")[1] == "course":
        x = parser.table_courses()
        groups = (x[f'{(call.data).split("_")[2]} курс'])
        keys = (list(groups.keys()))
        buttons = []

        for group in keys:
            button = InlineKeyboardButton(text=f"{group}", callback_data=f"select_group_{group}")
            buttons.append(button)

        back = InlineKeyboardButton(text="Назад", callback_data=f"back_courses")


        keyboard_groups = InlineKeyboardMarkup(row_width=3)
        keyboard_groups.add(*buttons)
        keyboard_groups.add(back)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите группу:", reply_markup=keyboard_groups)






print("бот запущен...")
bot.polling()