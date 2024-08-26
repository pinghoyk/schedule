import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import config

bot = telebot.TeleBot(config.API)

btn_1course = InlineKeyboardButton(text='1 курс', callback_data="select_course_1")
btn_2course = InlineKeyboardButton(text='2 курс', callback_data="select_course_2")
btn_3course = InlineKeyboardButton(text='3 курс', callback_data="select_course_3")
btn_4course = InlineKeyboardButton(text='4 курс', callback_data="select_course_4")
btn_5course = InlineKeyboardButton(text='5 курс', callback_data="select_course_5")

keyboard_courses = InlineKeyboardMarkup(row_width=2)
keyboard_courses.add(btn_1course, btn_2course, btn_3course, btn_4course, btn_5course)
@bot.message_handler(commands=['start'])
def start(message):
	bot.send_message(message.chat.id, text="Выберите курс:", reply_markup=keyboard_courses)






print("бот запущен...")
bot.polling()