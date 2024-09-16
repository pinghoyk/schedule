# Стандартная библиотека Python
"""
    библиотека os - представляет функции для работы с операционной системой
    модуль datetime - представляет классы для работы с датой и временем
    sqlite3 - бд
"""
import parser
import config
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import telebot
import pytz
import os
from datetime import datetime
import sqlite3

# Библиотеки сторонних разработчиков
"""
    pytz - позволяет работать с часовыми поясами
    telebot - работа с ботом
    типы для создания клавиатуры и кнопок
"""

# Локальные модули

bot = telebot.TeleBot(config.API)

# глобальные переменные
DB_NAME = 'database.db'
DB_PATH = DB_NAME
LOG = "Логи: "
YEAR = 25


# кнопки
btn_ros23 = InlineKeyboardButton(text="Российская 23", callback_data="ros_23")
btn_blux91 = InlineKeyboardButton(text="Блюхера 91", callback_data="blux91")
btn_return_complex = InlineKeyboardButton(
    text="Назад", callback_data="return_complex")

btn_day = InlineKeyboardButton(text="День", callback_data="select_day")
btn_week = InlineKeyboardButton(text="Неделя", callback_data="select_week")
btn_change_group = InlineKeyboardButton(
    text="Изменить группу", callback_data="back_courses")


btn_return_main = InlineKeyboardButton(text="Назад", callback_data="back_main")

days_buttons = [InlineKeyboardButton(text=day, callback_data=f"day_{day.lower()}") for day in ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]]
btn_dayback = InlineKeyboardButton(text="Назад", callback_data="day_back")

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


# проверка
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
            complex TEXT,
            -- notification TIME
        )
    """)
    connect.commit()
    connect.close()
    print(f"{LOG}бд создана")


# функции
def now_time():  # функция получения текущего времени по мск
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
    # отправляем запрос в бд и ничего не меняя полоуучаем данные понятные пользователю
    group = list(cursor.fetchone())
    connect.close()
    return group[0]


def transform_week(text):
    result = ""
    for day in text:
        result += f"*{day}*\n————————————————"
        lessons = text[day]
        for lesson in lessons:
            result += f"\n"
            result += f"{lesson['number']}.  "
            result += f"_{lesson['time_start']} - {lesson['time_finish']}_\n"
            result += f"*Предмет: *{lesson['name']}\n"
            for data in lesson["data"]:
                teacher_name = f"*Преподаватель: * {data['teacher']}"
                teacher_name = teacher_name.replace("отмена", "").strip()
                result += f"_{teacher_name}_  "
                result += f"*{data['classroom']}*\n"
        result += "\n\n"
    result = tg_markdown(result)
    result = result.replace("???", "**???**")
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


def get_week_schedule(complex_choice, user_group, parser, complex_links, YEAR):
    # Получаем список курсов для данного комплекса
    courses = parser.table_courses(complex_links[complex_choice])
    group = user_group

    year_start = int(group.split('-')[2])
    course = YEAR - year_start

    # Получаем группу по курсу и её URL
    groups = courses.get(f'{course} курс', None)
    if not groups or group not in groups:
        return None  # Возвращаем None, если расписание не найдено

    # Получаем URL для расписания на неделю
    url = groups[group]
    schedule_week = parser.schedule(f'https://pronew.chenk.ru/blocks/manage_groups/website/{url}')

    # Возвращаем расписание на неделю
    return schedule_week


def get_day_schedule(complex_choice, user_group, parser, complex_links, YEAR, selected_day):
    # Получаем список курсов для данного комплекса
    courses = parser.table_courses(complex_links[complex_choice])
    group = user_group

    year_start = int(group.split('-')[2])
    course = YEAR - year_start

    # Получаем группу по курсу и её URL
    groups = courses.get(f'{course} курс', None)
    if not groups or group not in groups:
        return None  # Возвращаем None, если расписание не найдено

    # Получаем URL для расписания на неделю
    url = groups[group]
    schedule_week = parser.schedule(f'https://pronew.chenk.ru/blocks/manage_groups/website/{url}')

    # Получаем расписание на выбранный день
    day_schedule = {}
    for key in schedule_week.keys():
        if selected_day.lower() in key.lower():
            day_schedule[key] = schedule_week[key]

    return day_schedule


# команды
@bot.message_handler(commands=['start'])
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

    bot.send_message(message.chat.id, text="Выберите комплекс:",
                     reply_markup=keyboard_complex)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(f"Вызов: {call.data}")

    user_id = call.message.chat.id
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    # ссылки на комплексы
    complex_links = {
        "Российская 23": "https://pronew.chenk.ru/blocks/manage_groups/website/list.php?id=3",
        "Блюхера 91": "https://pronew.chenk.ru/blocks/manage_groups/website/list.php?id=1"
    }

    # выбор комплекса
    if call.data == "ros_23":
        complex_choice = "Российская 23"
        cursor.execute("""UPDATE users
                          SET complex = ?
                          WHERE id = ?""", (complex_choice, user_id))
        connect.commit()

        # Получение курсов и создание кнопок
        courses = parser.table_courses(complex_links[complex_choice])
        buttons = []
        for i in range(len(courses)):
            button = InlineKeyboardButton(text=f"{i+1} курс", callback_data=f"select_course_{i+1}")
            buttons.append(button)

        # Создание клавиатуры с курсами
        keyboard_courses = InlineKeyboardMarkup(row_width=2)
        keyboard_courses.add(*buttons)
        keyboard_courses.add(btn_return_complex)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите курс:", reply_markup=keyboard_courses)
    elif call.data == "blux91":
        complex_choice = "Блюхера 91"
        cursor.execute("""UPDATE users
                          SET complex = ?
                          WHERE id = ?""", (complex_choice, user_id))
        connect.commit()

        # Получение курсов и создание кнопок
        courses = parser.table_courses(complex_links[complex_choice])
        buttons = []
        for i in range(len(courses)):
            button = InlineKeyboardButton(text=f"{i+1} курс", callback_data=f"select_course_{i+1}")
            buttons.append(button)

        # Создание клавиатуры с курсами
        keyboard_courses = InlineKeyboardMarkup(row_width=2)
        keyboard_courses.add(*buttons)
        keyboard_courses.add(btn_return_complex)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите курс:", reply_markup=keyboard_courses)
    elif call.data == "return_complex":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите комплекс:", reply_markup=keyboard_complex)

    if call.data.startswith("select_course_"):
        course_number = call.data.split("_")[-1]
        complex_choice = cursor.execute(
            "SELECT complex FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        try:
            x = parser.table_courses(complex_links[complex_choice])
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

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Выберите группу:", reply_markup=keyboard_groups)
        except:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Выбранный курс не найден :(", reply_markup=keyboard_error)

    if call.data == "back_courses":
        complex_choice = cursor.execute(
            "SELECT complex FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        courses = parser.table_courses(complex_links[complex_choice])
        buttons = []
        for i in range(len(courses)):
            button = InlineKeyboardButton(text=f"{i+1} курс", callback_data=f"select_course_{i+1}")
            buttons.append(button)

        # Создание клавиатуры с курсами
        keyboard_courses = InlineKeyboardMarkup(row_width=2)
        keyboard_courses.add(*buttons)
        keyboard_courses.add(btn_return_complex)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите курс:", reply_markup=keyboard_courses)

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
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите расписание:", reply_markup=keyboard_main)

    if call.data == "select_week":
        user_id = call.message.chat.id
        complex_choice = cursor.execute(
            "SELECT complex FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        group = user_group(call.message.chat.id)

        # Получаем расписание на неделю через функцию
        weekly_schedule = get_week_schedule(
            complex_choice, group, parser, complex_links, YEAR)

        if weekly_schedule:
            text = transform_week(weekly_schedule)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text, reply_markup=keyboard_week, parse_mode="MarkdownV2")
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Расписание не найдено", parse_mode="MarkdownV2")

    if call.data == "back_main":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите расписание:", reply_markup=keyboard_main)

    if call.data == "select_day":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите день недели:", reply_markup=keyboard_days)

    # Обработка выбора конкретного дня
    if call.data.startswith("day_"):
        selected_day = call.data.split("_")[1]
        complex_choice = cursor.execute(
            "SELECT complex FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        group = user_group(call.message.chat.id)

        day_schedule = get_day_schedule(
            complex_choice, group, parser, complex_links, YEAR, selected_day)

        if day_schedule:
            text = transform_week(day_schedule)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text, reply_markup=keyboard_day_back, parse_mode="MarkdownV2")

    # Обработка кнопки "Назад" в расписании на день
    if call.data == "day_back":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите день недели:", reply_markup=keyboard_days)


print("бот запущен...")
try:
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)
