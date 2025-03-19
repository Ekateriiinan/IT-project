import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("7571918160:AAH0WwDkgK5qhWQQGmC6m-r0SkC-ig9tIp8", parse_mode="MARKDOWN")

@bot.message_handler(commands=['start'])
def start(message):
    #кнопки
    buttons = types.InlineKeyboardMarkup()
    left_button = types.InlineKeyboardButton("←", callback_data="None")
    page_button = types.InlineKeyboardButton("1", callback_data="None")
    right_button = types.InlineKeyboardButton("→", callback_data="None")
    buy_button = types.InlineKeyboardButton("Вернуться", callback_data="None")
    buttons.add(left_button, page_button, right_button)
    buttons.add(buy_button)

    #подключаемся к БД
    db_file = "C:/Users/Redmi/OneDrive/Рабочий стол/sql/test1.db"
    connect = sqlite3.connect(db_file)
    cursor = connect.cursor()
    page_query = cursor.execute("SELECT `name`, `text` FROM `mesta` WHERE `id` = 1;")
    name, text = page_query.fetchone()
    msg = f"*{name}*\n       Что вас ждет?\n  - {text}" # вывод текста

    query = "SELECT `photo` FROM `mesta` WHERE id=1" # фото из БД
    cursor.execute(query)
    row = cursor.fetchone()
    a = bytes
    if row is not None:
        a = row[0]

    bot.send_photo(message.chat.id, photo=a, caption=msg, reply_markup=buttons)
    cursor.close()
    connect.close()

bot.polling(none_stop=True)
