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