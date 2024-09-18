import parser
import config
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import telebot
import pytz
import os
from datetime import datetime
import sqlite3


bot = telebot.TeleBot(config.API)  # создание бота

# глобальные переменные
DB_NAME = 'database.db'
DB_PATH = DB_NAME
LOG = "Логи: "
YEAR = 25
COMPLEX_LINKS = {
"Российская 23": "https://pronew.chenk.ru/blocks/manage_groups/website/list.php?id=3",
"Блюхера 91": "https://pronew.chenk.ru/blocks/manage_groups/website/list.php?id=1"
}
commands = [
telebot.types.BotCommand("start", "Запустить бота"),
telebot.types.BotCommand("today", "Расписание на сегодня"),
telebot.types.BotCommand("tommorow", "Расписание на завтра"),
]
bot.set_my_commands(commands)

LAST_MESSAGE = {}


# кнопки
btn_ros23 = InlineKeyboardButton(text="Российская 23", callback_data="complex_Российская 23")
btn_blux91 = InlineKeyboardButton(text="Блюхера 91", callback_data="complex_Блюхера 91")
btn_return_complex = InlineKeyboardButton(text="Назад", callback_data="back_complex")


btn_day = InlineKeyboardButton(text="День", callback_data="select_day")
btn_week = InlineKeyboardButton(text="Неделя", callback_data="select_week")
btn_change_group = InlineKeyboardButton(text="Изменить группу", callback_data="back_courses")

btn_return_main = InlineKeyboardButton(text="Назад", callback_data="back_main")

days_buttons = [InlineKeyboardButton(text=day, callback_data=f"day_{day.lower()}") for day in ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]]
btn_dayback = InlineKeyboardButton(text="Назад", callback_data="back_day")

back = InlineKeyboardButton(text="Назад", callback_data="back_courses")

# клавиатуры
keyboard_complex = InlineKeyboardMarkup(row_width=1)
keyboard_complex.add(btn_ros23, btn_blux91)

keyboard_main = InlineKeyboardMarkup(row_width=2)
keyboard_main.add(btn_day, btn_week, btn_change_group)

keyboard_week = InlineKeyboardMarkup(row_width=2)
keyboard_week.add(btn_return_main)

keyboard_days = InlineKeyboardMarkup(row_width=2)
keyboard_days.add(*days_buttons, btn_return_main)

keyboard_day_back = InlineKeyboardMarkup(row_width=1)
keyboard_day_back.add(btn_dayback)

keyboard_error = InlineKeyboardMarkup()
keyboard_error.add(btn_change_group)


# ПРОВЕРКИ
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
            time_registration TIME,
            complex TEXT
        )
    """)
    connect.commit()
    connect.close()
    print(f"{LOG}бд создана")


# ФУНКЦИИ
def SQL_request(request, params=()):  # sql запросы
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    if request.strip().lower().startswith('select'):
        cursor.execute(request, params)
        result = cursor.fetchone()
        return result
    else:
        cursor.execute(request, params)
        connect.commit()
    connect.close()


def now_time():  # функция получения текущего времени по мск
    now = datetime.now()
    tz = pytz.timezone('Europe/Moscow')
    now_moscow = now.astimezone(tz)
    current_time = now_moscow.strftime("%H:%M")
    current_date = now_moscow.strftime("%m.%d.%Y")
    date = f"{current_date} {current_time}"
    return date


def markup_text(text):  # разметка текста на неделю
    result = ""
    for day in text:
        result += f"*{day}*\n————————————————"
        lessons = text[day]
        for lesson in lessons:
            result += f"\n"
            result += f"{lesson['number']}.  "
            result += f"_{lesson['time_start']} - {lesson['time_finish']}_\n"
            
            # Перебираем все уроки в одно время
            for l in lesson['lessons']:
                result += f"*Предмет: *{l['name']}\n"
                for data in l["data"]:
                    teacher_name = f"*Преподаватель: * {data['teacher']}"
                    teacher_name = teacher_name.replace("отмена", "").strip()
                    result += f"_{teacher_name}_  "
                    result += f"*{data['classroom']}*\n"
        result += "\n\n"
    
    result = tg_markdown(result)  # Применяем функцию для обработки markdown в Telegram
    result = result.replace("???", "**???**")  # Подсвечиваем "???", если время неизвестно
    return result


def tg_markdown(text):  # экранирование только для телеграма
    special_characters = r'[]()>#+-=|{}.!'
    escaped_text = ''
    for char in text:
        if char in special_characters:
            escaped_text += f'\\{char}'
        else:
            escaped_text += char
    return escaped_text


def get_week_schedule(complex_choice, user_group):  # получение расписания на неделю
    courses = parser.table_courses(COMPLEX_LINKS[complex_choice])

    year_start = int(user_group.split('-')[2])
    course = YEAR - year_start

    groups = courses.get(f'{course} курс', None)
    if not groups or user_group not in groups:
        return None

    url = groups[user_group]
    schedule_week = parser.schedule(f'https://pronew.chenk.ru/blocks/manage_groups/website/{url}')

    return schedule_week


def get_day_schedule(complex_choice, user_group, selected_day):  # получение расписания на выбранный день
    schedule_week = get_week_schedule(complex_choice, user_group)

    day_schedule = {}
    for key in schedule_week.keys():
        if selected_day.lower() in key.lower():
            day_schedule[key] = schedule_week[key]

    return day_schedule


def keyboard_courses(courses):  # создание клавиатуры с курсами
    buttons = []
    for i in range(len(courses)):
        button = InlineKeyboardButton(text=f"{i+1} курс", callback_data=f"select_course_{i+1}")
        buttons.append(button)
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    keyboard.add(btn_return_complex)
    return keyboard


def get_today_schedule(complex_choice, user_group, selected_day):
    schedule_week = get_week_schedule(complex_choice, user_group)

    day_mapping = {
        0: "Понедельник",
        1: "Вторник",
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
    }

    if selected_day == "сегодня":
        today_index = datetime.now().weekday()  # Получаем номер дня недели (0 — понедельник, 6 — воскресенье)
        selected_day = day_mapping[today_index]

    elif selected_day == "завтра":
        tomorrow_index = (datetime.now() + timedelta(days=1)).weekday()  # Получаем номер завтрашнего дня
        selected_day = day_mapping[tomorrow_index]

    selected_day = selected_day.lower()

    day_schedule = {}
    for key in schedule_week.keys():
        if selected_day in key.lower():
            day_schedule[key] = schedule_week[key]

    return day_schedule



# КОМАНДЫ
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id in LAST_MESSAGE:  # удаляет последнее сообщене пользователя
        try:
            bot.delete_message(message.chat.id, LAST_MESSAGE[message.chat.id])
        except:
            pass

    user_id = message.chat.id
    message_id = message.message_id

    times = now_time()

    with sqlite3.connect(DB_PATH) as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute("""INSERT INTO users (id, message, time_registration)
                              VALUES (?, ?, ?)""", (user_id, message_id, times))
            print(f"{LOG}зарегистрирован новый пользователь")
        else:
            cursor.execute("""UPDATE users
                              SET message = ?
                              WHERE id = ?""", (message_id, user_id))
            print(f"{LOG}пользователь уже существует")
        connect.commit()

    LAST_MESSAGE[message.chat.id] = bot.send_message(message.chat.id, text="Выберите комплекс:", reply_markup=keyboard_complex).message_id
    bot.delete_message(message.chat.id, message.message_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):  # работа с вызовами inline кнопок
    # print(f"Вызов: {call.data}")
    user_id = call.message.chat.id

    if (call.data).split("_")[0] == "complex":  # выбор комплекса
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Получение курсов...")
        complex_choice = (call.data).split("_")[1]
        SQL_request("UPDATE users SET complex = ? WHERE id = ?", (complex_choice, user_id))

        courses = parser.table_courses(COMPLEX_LINKS[complex_choice])
        keyboard = keyboard_courses(courses)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите курс:", reply_markup=keyboard)

    if call.data.startswith("select_course_"):  # выбор курса
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Получение групп...")
        course_number = call.data.split("_")[-1]
        user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
        complex_choice = user[4]

        try:
            x = parser.table_courses(COMPLEX_LINKS[complex_choice])
            groups = x[f'{course_number} курс']
            keys = list(groups.keys())
            buttons = []

            for group in keys:
                button = InlineKeyboardButton(text=f"{group}", callback_data=f"select_group_{group}")
                buttons.append(button)

            back = InlineKeyboardButton(
                text="Назад", callback_data="back_courses")

            keyboard_groups = InlineKeyboardMarkup(row_width=3)
            keyboard_groups.add(*buttons)
            keyboard_groups.add(back)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите группу:", reply_markup=keyboard_groups)

        except:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выбранный курс не найден :(", reply_markup=keyboard_error)

    if (call.data).split("_")[0] == "select" and (call.data).split("_")[1] == "group":  # выбор группы
        groups = call.data.split('_')[2]

        SQL_request("UPDATE users SET groups = ? WHERE id = ?", (groups, user_id))

        print(f"{LOG}записана группа пользователя")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите расписание:", reply_markup=keyboard_main)

    if call.data == "select_week":  # расписание на неделю
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Загрузка расписания...")
        user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
        complex_choice = user[4]
        group = user[2]

        weekly_schedule = get_week_schedule(complex_choice, group)

        if weekly_schedule:
            text = markup_text(weekly_schedule)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard_week, parse_mode="MarkdownV2")
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Расписание не найдено")

    if call.data == "select_day":  # выбор дня недели
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите день недели:", reply_markup=keyboard_days)

    if call.data.startswith("day_"):  # обработка выбора конкретного дня
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Загрузка расписания...")
        selected_day = call.data.split("_")[1]
        user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
        complex_choice = user[4]
        group = user[2]

        day_schedule = get_day_schedule(complex_choice, group, selected_day)

        if day_schedule:
            text = markup_text(day_schedule)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard_day_back, parse_mode="MarkdownV2")
        else: bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Расписание не найдено...", reply_markup=keyboard_day_back)

    if call.data == "back_complex":  # возврат в комплексы
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите комплекс:", reply_markup=keyboard_complex)

    if call.data == "back_courses":  # возврат в курсы
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Получение курсов...")
        user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
        complex_choice = user[4]
        courses = parser.table_courses(COMPLEX_LINKS[complex_choice])
        keyboard = keyboard_courses(courses)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите курс:", reply_markup=keyboard)

    if call.data == "back_main":  # возврат на главную
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите расписание:", reply_markup=keyboard_main)

    if call.data == "back_day":  # возврат на дни недели
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите день недели:", reply_markup=keyboard_days)


@bot.message_handler(commands=['today'])
def send_today_schedule(message):
    user_id = message.chat.id
    delete_last_message(bot, message.chat.id)

    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
    if not user:
        bot.send_message(message.chat.id, 'Вы не зарегистрированы. Пожалуйста, выберите комплекс и группу.')
        return
    
    complex_choice = user[4]
    group = user[2] 

    schedule = get_today_schedule(complex_choice, group, "сегодня")

    if schedule:
          text = markup_text(schedule)
          bot.send_message(message.chat.id, text, reply_markup=keyboard_command, parse_mode="MarkdownV2")
    else:
          bot.send_message(message.chat.id, 'Расписание на сегодня не найдено.', reply_markup=keyboard_days)


@bot.message_handler(commands=['tomorrow'])
def send_tomorrow_schedule(message):
    user_id = message.chat.id
    delete_last_message(bot, message.chat.id)

    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
    if not user:
        bot.send_message(message.chat.id, 'Вы не зарегистрированы. Пожалуйста, выберите комплекс и группу.')
        return
    
    complex_choice = user[4]
    group = user[2]

    schedule = get_today_schedule(complex_choice, group, "завтра")
    
    if schedule:
          text = markup_text(schedule)
          bot.send_message(message.chat.id, text, reply_markup=keyboard_command, parse_mode="MarkdownV2")
    else:
          bot.send_message(message.chat.id, 'Расписание на сегодня не найдено.', reply_markup=keyboard_days)

@bot.message_handler(func=lambda message: True)
def handle_text_message(message): # удаляет сообщения от пользователя
    bot.delete_message(message.chat.id, message.message_id)


print(f"{LOG}бот запущен...")
bot.polling(none_stop=True)
