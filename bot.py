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
YEAR = 25


# кнопки
x = parser.table_courses()
buttons = []
for i in range(len(x)):
    button = InlineKeyboardButton(text=f"{i+1} курс", callback_data=f"select_course_{i+1}")
    buttons.append(button)


btn_day = InlineKeyboardButton(text="День", callback_data="select_day")
btn_week = InlineKeyboardButton(text="Неделя", callback_data="select_week")
btn_change_group = InlineKeyboardButton(text="Изменить группу", callback_data="back_courses")

btn_return_main = InlineKeyboardButton(text="Назад", callback_data="back_main")

# клавиатуры
keyboard_courses = InlineKeyboardMarkup(row_width=2)
keyboard_courses.add(*buttons)

keyboard_main = InlineKeyboardMarkup(row_width=2)
keyboard_main.add(btn_day, btn_week, btn_change_group)

keyboard_week = InlineKeyboardMarkup(row_width=2)
keyboard_week.add(btn_return_main)

keyboard_error = InlineKeyboardMarkup()
keyboard_error.add(btn_change_group)


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
def now_time(): # функция получения текущего времени по мск
    now = datetime.now()
    tz = pytz.timezone('Europe/Moscow')
    now_moscow = now.astimezone(tz)
    current_time = now_moscow.strftime("%H:%M")
    current_date = now_moscow.strftime("%m.%d.%Y")
    date = f"{current_date} {current_time}"
    return date


def user_group(user_id):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    cursor.execute("SELECT groups FROM users WHERE id = ?", (int(user_id),))
    group =list(cursor.fetchone()) # отправляем запрос в бд и ничего не меняя полоуучаем данные понятные пользователю
    connect.close()
    return group[0]

def transform_week(text):
    result = ""
    for day in text:
        result += f"{day}\n"
        lessons = text[day]
        for lesson in lessons:
            result += f"\n"
            result += f"Пара: {lesson['number']}\n"
            result += f"Время: {lesson['time_start']} - {lesson['time_finish']}\n"
            result += f"Предмет: {lesson['name']}\n"
            for data in lesson["data"]:
                result += f"Преподаватель: {data['teacher']}\n"
                result += f"Кабинет: {data['classroom']}\n"
        result += "\n\n"
    return result







# команды
@bot.message_handler(commands=['start']) # отслеживание команды старт
def start(message):
    user_id = message.chat.id
    message_id = message.id
    time = now_time()
    
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


@bot.callback_query_handler(func=lambda call:True) # цикл чтобы функция ниже всегда работала
def callback_query(call): #обработчик вызовов
    print(f"Вызов: {call.data}")

    if (call.data).split("_")[0] == "select" and (call.data).split("_")[1] == "course":
        x = parser.table_courses()
        try:
            groups = (x[f'{(call.data).split("_")[2]} курс'])
            keys = (list(groups.keys()))
            buttons = []
    
            for group in keys:
                button = InlineKeyboardButton(text=f"{group}", callback_data=f"select_group_{group}")
                buttons.append(button) # добавление в массив
    
            back = InlineKeyboardButton(text="Назад", callback_data="back_courses")
    
    
            keyboard_groups = InlineKeyboardMarkup(row_width=3)
            keyboard_groups.add(*buttons)
            keyboard_groups.add(back)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите группу:", reply_markup=keyboard_groups)
        except:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выбранный курс не найден :(", reply_markup= keyboard_error)

    if call.data == "back_courses":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите курс:", reply_markup=keyboard_courses)

    if (call.data).split("_")[0] == "select" and (call.data).split("_")[1] == "group":
        user_id = call.message.chat.id

        groups = call.data.split('_')[2]

        connect = sqlite3.connect(DB_PATH)
        cursor = connect.cursor()
        
        cursor.execute("""UPDATE users
                          SET groups = ?
                          WHERE id = ?""", (groups, user_id))
        connect.commit()
        connect.close()

        print(f"{LOG}записана группа пользователя")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите расписание:", reply_markup=keyboard_main)

    if call.data == "select_week":
        y = parser.table_courses()
        group = user_group(call.message.chat.id)

        year_start = int(group.split('-')[2])
        course = YEAR - year_start
        groups = (y[f'{course} курс'])
        url = (groups[group])
        schedule_week = parser.schedule(f'https://pronew.chenk.ru/blocks/manage_groups/website/{url}')
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"{schedule_week}", reply_markup=keyboard_week)


    if call.data == "back_main":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите расписание:", reply_markup=keyboard_main)













print("бот запущен...")
bot.polling()