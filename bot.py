# Стандартная библиотека Python
"""
    библиотека os - представляет функции для работы с операционной системой
    модуль datetime - представляет классы для работы с датой и временем
    sqlite3 - бд
"""
import os
from datetime import datetime
import sqlite3

# Библиотеки сторонних разработчиков
"""
    pytz - позволяет работать с часовыми поясами
    telebot - работа с ботом
    типы для создания клавиатуры и кнопок
"""
import pytz
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Локальные модули
import config
import parser

bot = telebot.TeleBot(config.API)

# глобальные переменные
DB_NAME = 'database.db'
DB_PATH = DB_NAME
LOG = "Логи: "
YEAR = 25

# кнопки
btn_ros23 = InlineKeyboardButton(text="Российская 23", callback_data="ros_23")
btn_blux91 = InlineKeyboardButton(text="Блюхера 91", callback_data="blux91")
btn_return_complex = InlineKeyboardButton(text="Назад", callback_data="return_complex")

btn_day = InlineKeyboardButton(text="День", callback_data="select_day")
btn_week = InlineKeyboardButton(text="Неделя", callback_data="select_week")
btn_change_group = InlineKeyboardButton(text="Изменить группу", callback_data="back_courses")

btn_return_main = InlineKeyboardButton(text="Назад", callback_data="back_main")

back = InlineKeyboardButton(text="Назад", callback_data="back_courses")