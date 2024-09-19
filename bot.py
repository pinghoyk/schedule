import parser
import config
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
import telebot
import pytz
import os
from datetime import datetime, timedelta
import sqlite3


bot = telebot.TeleBot(config.API)  # создание бота

# глобальные переменные
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
]

# кнопки
btn_ros23 = InlineKeyboardButton(text="Российская 23", callback_data="complex_Российская 23")
btn_blux91 = InlineKeyboardButton(text="Блюхера 91", callback_data="complex_Блюхера 91")
btn_return_complex = InlineKeyboardButton(text="Назад", callback_data="back_complex")


btn_day = InlineKeyboardButton(text="День", callback_data="select_day")
btn_week = InlineKeyboardButton(text="Неделя", callback_data="select_week")
btn_change_group = InlineKeyboardButton(text="Изменить группу", callback_data="back_courses")

btn_return_main = InlineKeyboardButton(text="Назад", callback_data="back_main")

days_buttons = [InlineKeyboardButton(text=day, callback_data=f"day_{day.lower()}") for day in DAYS]
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


def now_day(day = None):
    today = datetime.today().weekday()
    if day == "tomorrow": 
        today += 1
    if today == 6: 
        today == 1
    return DAYS[today]


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
        schedule = get_day_schedule(complex_choice, group, day)
    
        if schedule:
              text = markup_text(schedule)
              bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text=text, reply_markup=keyboard_day_back, parse_mode="MarkdownV2")
        else:
              bot.edit_message_text(message.chat.id, message_id=user[1], text="Расписание на сегодня не найдено", reply_markup=keyboard_day_back)



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

@bot.message_handler(commands=['week'])  # обработка команды week
def send_week_schedule(message):
    bot.delete_message(message.chat.id, message.message_id)
    user_id = message.chat.id
    bot.edit_message_text(chat_id=message.chat.id, message_id=user_id, text="Загрузка расписания...")
    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),))
    weekly_schedule = get_week_schedule(user[4], user[2])
    if weekly_schedule:
        text = markup_text(weekly_schedule)
        bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text=text, reply_markup=keyboard_week, parse_mode="MarkdownV2")
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=user[1], text="Расписание не найдено", reply_markup=keyboard_week)



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
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Расписание не найдено", reply_markup=keyboard_week)

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
        


@bot.message_handler(func=lambda message: True)
def handle_text_message(message): # удаляет сообщения от пользователя
    bot.delete_message(message.chat.id, message.message_id)



bot.set_my_commands(commands)
print(f"{LOG}бот запущен...")
bot.polling(none_stop=True)