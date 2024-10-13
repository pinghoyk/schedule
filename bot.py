import parser
import config
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
import telebot
import pytz
import os
from datetime import datetime, timedelta
import sqlite3
import threading
import ast
import json
import requests


bot = telebot.TeleBot(config.API)  # создание бота

# глобальные переменные
VERSION = "1.0.0"
DB_NAME = 'database.db'
DB_PATH = DB_NAME
YEAR = 25
COMPLEX_LINKS = {
"Российская 23": "https://pronew.chenk.ru/blocks/manage_groups/website/list.php?id=3",
"Блюхера 91": "https://pronew.chenk.ru/blocks/manage_groups/website/list.php?id=1"
}

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

LOG = "Логи: "


commands = [  # команды бота
telebot.types.BotCommand("start", "Перезапуск"),
telebot.types.BotCommand("today", "Расписание на сегодня"),
telebot.types.BotCommand("tomorrow", "Расписание на завтра"),
telebot.types.BotCommand("week", "Расписание на всю неделю"),
telebot.types.BotCommand("info", "Дополнительная информация"),
]

# кнопки
btn_ros23 = InlineKeyboardButton(text="Российская 23", callback_data="complex_Российская 23")
btn_blux91 = InlineKeyboardButton(text="Блюхера 91", callback_data="complex_Блюхера 91")
btn_return_complex = InlineKeyboardButton(text="< Назад", callback_data="back_complex")

btn_select_teachers = InlineKeyboardButton(text="Я преподаватель", callback_data='teachers_select')


btn_day = InlineKeyboardButton(text="День", callback_data="select_day")
btn_week = InlineKeyboardButton(text="Неделя", callback_data="select_week")
btn_change_group = InlineKeyboardButton(text="Изменить группу", callback_data="back_courses")

btn_return_main = InlineKeyboardButton(text="< Назад", callback_data="back_main")

days_buttons = [InlineKeyboardButton(text=day, callback_data=f"day_{day.lower()}") for day in DAYS]
btn_dayback = InlineKeyboardButton(text="< Назад", callback_data="back_day")

back = InlineKeyboardButton(text="< Назад", callback_data="back_courses")

btn_bug_report = InlineKeyboardButton(text="Нашли ошибку?", url="https://github.com/pinghoyk/schedule/issues/new?assignees=Falbue&labels=%D0%B1%D0%B0%D0%B3&projects=&template=%D0%B1%D0%B0%D0%B3-%D0%BE%D1%82%D1%87%D1%91%D1%82.md&title=")
btn_new_function = InlineKeyboardButton(text="Новая идея!", url="https://github.com/pinghoyk/schedule/issues/new?assignees=Falbue&labels=%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D1%82%D1%8C&projects=&template=%D0%B7%D0%B0%D0%BF%D1%80%D0%BE%D1%81-%D0%BD%D0%B0-%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D0%B8%D0%B5.md&title=")
btn_github = InlineKeyboardButton(text="Репозиторий на Github", url="https://github.com/pinghoyk/schedule")
btn_readme = InlineKeyboardButton(text="Описание", callback_data='readme')
btn_what_new = InlineKeyboardButton(text="Что нового?", callback_data='what_new')
btn_return_in_info = InlineKeyboardButton(text="< Назад", callback_data='back_in_info')
btn_return_info = InlineKeyboardButton(text="< Назад", callback_data='back_info')

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


def now_day(day = None):
    today = datetime.today().weekday()
    if day == "tomorrow": 
        today += 1
    if today >= 6:
        today = 0
    return DAYS[today]


def markup_text(schedule, is_teacher_format=False):
    # Сортируем расписание по порядку дней недели
    sorted_schedule = sorted(schedule.items(), key=lambda x: DAYS.index(x[0].split(", ")[-1]))

    result = []
    for key, lessons in sorted_schedule:
        result.append(f"*{key}*\n————————————————")
        
        # Сортируем уроки по времени начала, пропуская невалидные значения
        lessons.sort(key=lambda lesson: (
            int(lesson['time_start'].replace('.', '').replace(':', '')) if lesson['time_start'] != '???' else float('inf')
        ))

        for i, lesson in enumerate(lessons, start=1):
            time_start = lesson['time_start']
            time_finish = lesson['time_finish']
            lesson_info = f"\n{i}.  _{time_start} - {time_finish}_\n"

            if is_teacher_format:
                group = lesson['group']
                lesson_name = lesson['lesson_name']
                classroom = lesson['classroom'] if lesson['classroom'] else ''
                lesson_info += f"*Предмет*: {lesson_name}\n_*Группа:* {group}_  *{classroom}*\n"
            else:
                for l in lesson['lessons']:
                    lesson_info += f"*Предмет: *{l['name']}\n"
                    for data in l["data"]:
                        teacher_name = f"*Преподаватель: * {data['teacher']}".replace("отмена", "").strip()
                        lesson_info += f"_{teacher_name}_  *{data['classroom']}*\n"

            result.append(lesson_info)

        result.append("\n\n")

    result = ''.join(result)  # Объединяем список в строку
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
    keyboard.add(*buttons, btn_select_teachers)
    keyboard.add(btn_return_complex)
    return keyboard


def day_commads(message, tomorrow = None):
    bot.delete_message(message.chat.id, message.message_id)
    user_id = message.chat.id

    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),))

    if user[4] == None: 
        bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text="Сначала выберите корпус!", reply_markup=keyboard_complex)
    elif user[2] == None:
        courses = parser.table_courses(COMPLEX_LINKS[user[4]])
        keyboard = keyboard_courses(courses)
        bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text="Сначала выберите группу!", reply_markup=keyboard)
    else: 
        bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text="Загрузка расписания...")

        complex_choice = user[4]
        group = user[2]
        day = now_day(tomorrow) 
        if group.split(":")[0] == "teacher":
            try:
                text = get_day_teacher(complex_choice, group.split(":")[1], day)
                text = markup_text(text, is_teacher_format=True)
                bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text=text, reply_markup=keyboard_day_back, parse_mode="MarkdownV2")
            except Exception as e:
                print(f"Ошибка: {e}")
                bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text="Расписание не найдено", reply_markup=keyboard_day_back)
        else:
            schedule = get_day_schedule(complex_choice, group, day)
        
            if schedule:
                  text = markup_text(schedule)
                  bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text=text, reply_markup=keyboard_day_back, parse_mode="MarkdownV2")
            else:
                  bot.edit_message_text(message.chat.id, message_id=user[1], text="Расписание на сегодня не найдено", reply_markup=keyboard_day_back)


def save_teacher_schedule(x):  # сохранение данных для преподавателей
    teacher_schedule = parser.get_teacher_schedule(COMPLEX_LINKS[x])
    
    # Получаем текущее время
    current_time = datetime.now()
    
    # Форматируем данные для записи в файл
    file_content = f"Обновлено: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n{teacher_schedule}"
    
    # Сохраняем данные в файл с именем x.txt
    with open(f"{x}.txt", "w", encoding="utf-8") as file:
        file.write(file_content)
    
    print(f"Расписание для {x} сохранено.")


def check_and_update_schedule(x):  # проверка, нужно ли обновлять расписание
    file_name = f"{x}.txt"
    
    # Проверяем, существует ли файл
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as file:
            first_line = file.readline().strip()
            if first_line.startswith("Обновлено:"):
                last_update_time_str = first_line.split(": ")[1]
                last_update_time = datetime.strptime(last_update_time_str, '%Y-%m-%d %H:%M:%S')
                
                # Проверяем, прошло ли 6 часов с последнего обновления
                if (datetime.now() - last_update_time).total_seconds() < 6 * 3600:
                    print("Данные уже обновлены в течение последних 6 часов.")
                    return  # Обновление не требуется
    
    # Если файл не существует или прошло больше 6 часов, обновляем данные
    save_teacher_schedule(x)


def get_week_teacher(complex_choice, teacher):  # получение расписания, для выбранного преподавателя из большого списка
    with open(f"{complex_choice}.txt", "r", encoding="utf-8") as file:
        lines = file.readlines()  # Считываем все строки в список
        data = lines[1:]  # Получаем все строки, кроме первой
    data_text = ''.join(data) # Объединяем все строки в один текст
    
    data_dict = json.loads(data_text.replace("'", "\""))  # Заменяем одинарные кавычки на двойные
    x = (data_dict[teacher])
    return x


def get_day_teacher(complex_choice, teacher, selected_day):  # получение расписания на день
    schedule_week = get_week_teacher(complex_choice, teacher)

    day_schedule = {}
    for key in schedule_week.keys():
        if selected_day.lower() in key.lower():
            day_schedule[key] = schedule_week[key]

    return day_schedule


def send_week_schedule(chat_id, message_id, user_id, is_button_click=False):    # отправка расписания на неделю
    user_id = chat_id

    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),))
    bot.edit_message_text(chat_id=chat_id, message_id=user[1], text="Загрузка расписания...")

    if user[4] == None: 
        bot.edit_message_text(chat_id=chat_id, message_id=user[1], text="Сначала выберите корпус!", reply_markup=keyboard_complex)
    if user[4] == None: 
        bot.edit_message_text(chat_id=chat_id, message_id=user[1], text="Сначала выберите корпус!", reply_markup=keyboard_complex)
    elif user[2] == None:
        courses = parser.table_courses(COMPLEX_LINKS[user[4]])
        keyboard = keyboard_courses(courses)
        bot.edit_message_text(chat_id=chat_id, message_id=user[1], text="Сначала выберите группу!", reply_markup=keyboard)
    else: 
        user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
        complex_choice = user[4]
        group = user[2]
    
        if group.split(":")[0] == "teacher":
            try:
                text = get_week_teacher(complex_choice, group.split(":")[1])
                text = markup_text(text, is_teacher_format=True)
                bot.edit_message_text(chat_id=chat_id, message_id=user[1], text=text, reply_markup=keyboard_week, parse_mode="MarkdownV2")
            except Exception as e:
                print(f"Ошибка: {e}")
                bot.edit_message_text(chat_id=chat_id, message_id=user[1], text="Расписание не найдено", reply_markup=keyboard_week)
        else:
            weekly_schedule = get_week_schedule(complex_choice, group)
            if weekly_schedule:
                text = markup_text(weekly_schedule)
                bot.edit_message_text(chat_id=chat_id, message_id=user[1], text=text, reply_markup=keyboard_week, parse_mode="MarkdownV2")
            else:
                bot.edit_message_text(chat_id=chat_id, message_id=user[1], text="Расписание не найдено", reply_markup=keyboard_week)
    


# КОМАНДЫ
@bot.message_handler(commands=['start'])  # обработка команды start
def start(message):
    user_id = message.chat.id
    message_id = message.message_id

    times = now_time()
    user = SQL_request("SELECT 0 FROM users WHERE id = ?", (user_id,))
    if user is None:
        SQL_request("""INSERT INTO users (id, message, time_registration)
                          VALUES (?, ?, ?)""", (user_id, message_id+1, times))
        print(f"{LOG}зарегистрирован новый пользователь")
    else:
        menu_id = SQL_request("SELECT message FROM users WHERE id = ?", (user_id,))  # получение id меню
        try: bot.delete_message(message.chat.id, menu_id[0])  # обработка ошибки, если чат пустой, но пользователь есть в базе
        except Exception as e: print(f"Ошибка: {e}")  # вывод текста ошибки
        SQL_request("""UPDATE users SET message = ? WHERE id = ?""", (message_id+1, user_id))  # добавление id нового меню
        print(f"{LOG}пользователь уже существует")
    bot.send_message(message.chat.id, text="Выберите комплекс:", reply_markup=keyboard_complex)
    bot.delete_message(message.chat.id, message_id)

@bot.message_handler(commands=['today'])  # обработка команды today
def send_today_schedule(message):
    day_commads(message)

@bot.message_handler(commands=['tomorrow'])  # обработка команды toworrow
def send_tomorrow_schedule(message):
    day_commads(message, "tomorrow")

@bot.message_handler(commands=['week'])
def handle_week_command(message):
    bot.delete_message(message.chat.id, message.message_id)
    send_week_schedule(message.chat.id, message.message_id, message.chat.id)



# INLINE КОМАНДЫ
@bot.inline_handler(lambda query: query.query == '')
def default_query(inline_query):
    user_id = inline_query.from_user.id
    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),))

    if not user:
        bot.answer_inline_query(
            inline_query.id, 
            [
                types.InlineQueryResultArticle(
                    id='no_user', 
                    title='Переход к боту',
                    thumbnail_url = "https://falbue.github.io/classroom-code/icons/registr.png",
                    description='Пожалуйста, зарегистрируйтесь для доступа к функциям.',
                    input_message_content=types.InputTextMessageContent("Вы не зарегистрированы. Перейдите по ссылке, для регистрации"),
                    reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    text='Перейти', 
                    url='https://t.me/schedule_chenk_bot'
                )
            )
                )
            ], 
            cache_time=1,
            switch_pm_text="Регистрация", 
            switch_pm_parameter="start"
        )
        return

    elif user[4] is not None and user[2] is None:
        bot.answer_inline_query(
            inline_query.id, 
            [types.InlineQueryResultArticle(
                    id='no_group', 
                    title='Группа не найдена',
                    thumbnail_url = "https://falbue.github.io/classroom-code/icons/danger.png",
                    description='Расписание на выбранную группу не найдено...',
                    input_message_content=types.InputTextMessageContent("Расписание на выбранную группу не найдено!")
                )
            ], 
            cache_time=1, 
            switch_pm_text="Группа не выбрана", 
            switch_pm_parameter="start"
        )
    else:
        complex_choice = user[4]
        group = user[2]
    
        week = get_week_schedule(complex_choice, group)
        week = markup_text(week)
    
        today_day = now_day()
        today = get_day_schedule(complex_choice, group, today_day)
        today = markup_text(today)
    
        tomorrow_day = now_day("tomorrow") 
        tomorrow = get_day_schedule(complex_choice, group, tomorrow_day)
        tomorrow = markup_text(tomorrow)
    
        commands = [
            types.InlineQueryResultArticle(
                id='1', title='Сегодня', description='Расписание на сегодняшний день',
                thumbnail_url = "https://falbue.github.io/classroom-code/icons/today.png",
                input_message_content=types.InputTextMessageContent(today, parse_mode="MarkdownV2")
            ),
            types.InlineQueryResultArticle(
                id='2', title='Завтра', description='Расписание на завтрашний день',
                thumbnail_url = "https://falbue.github.io/classroom-code/icons/toworrow.png",
                input_message_content=types.InputTextMessageContent(tomorrow, parse_mode="MarkdownV2")
            ),
            types.InlineQueryResultArticle(
                id='3', title='Неделя', description='Расписание на неделю',
                thumbnail_url = "https://falbue.github.io/classroom-code/icons/week.png",
                input_message_content=types.InputTextMessageContent(week, parse_mode="MarkdownV2")
            )
        ]
        
        bot.answer_inline_query(
            inline_query.id, 
            commands, 
            cache_time=1, 
            switch_pm_text=group, 
            switch_pm_parameter="start"
        )



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

            back = InlineKeyboardButton(text="< Назад", callback_data="back_courses")

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
        send_week_schedule(call.message.chat.id, call.message.message_id, call.message.chat.id, is_button_click=True)

    if call.data == "select_day":  # выбор дня недели
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите день недели:", reply_markup=keyboard_days)

    if call.data.startswith("day_"):  # обработка выбора конкретного дня
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Загрузка расписания...")
        selected_day = call.data.split("_")[1]
        user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
        complex_choice = user[4]
        group = user[2]

        if group.split(":")[0] == "teacher":
            try:
                text = get_day_teacher(complex_choice, group.split(":")[1], selected_day)
                text = markup_text(text, is_teacher_format=True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard_day_back, parse_mode="MarkdownV2")
            except Exception as e:
                print(f"Ошибка: {e}")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Расписание не найдено", reply_markup=keyboard_day_back)
        else:
            day_schedule = get_day_schedule(complex_choice, group, selected_day)
    
            if day_schedule:
                text = markup_text(day_schedule)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard_day_back, parse_mode="MarkdownV2")
            else: bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Расписание не найдено...", reply_markup=keyboard_day_back)

    if call.data == "teachers_select":
        user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),)) 
        complex_choice = user[4]

        back = InlineKeyboardButton(text="< Назад", callback_data="back_courses")

        with open(f"{complex_choice}.txt", 'r', encoding='utf-8') as file:
            data = file.read()

        data_dict_str = data.split("Обновлено:")[1].strip()
        data_dict_str = data_dict_str[data_dict_str.index('{'):]
        data_dict = ast.literal_eval(data_dict_str)
        fio_list = [fio for fio in data_dict.keys() if not fio.endswith('\nотмена')]
        fio_list = sorted(fio_list)

        buttons = []
        for i in range(len(fio_list)):
            button = InlineKeyboardButton(text=fio_list[i], callback_data=f"teacher:{fio_list[i]}")
            buttons.append(button)
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(*buttons)
        keyboard.add(back)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите нужного преподавателя", reply_markup=keyboard)

    if (call.data).split(":")[0] == "teacher":
        teacher_name = (call.data).split(":")[1]
        SQL_request("UPDATE users SET groups = ? WHERE id = ?", (f"teacher:{teacher_name}", user_id))
        print(f"{LOG}Выбран преподаватель {teacher_name}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите расписание:", reply_markup=keyboard_main)


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
        


@bot.message_handler(func=lambda message: True)
def handle_text_message(message): # удаляет сообщения от пользователя
    bot.delete_message(message.chat.id, message.message_id)


# запуск, обновления расписания для преподавателей
thread1 = threading.Thread(target=check_and_update_schedule, args=("Российская 23",))
thread2 = threading.Thread(target=check_and_update_schedule, args=("Блюхера 91",))
thread1.start()
thread2.start()


bot.set_my_commands(commands)
print(f"{LOG}бот запущен...")
bot.polling(none_stop=True)