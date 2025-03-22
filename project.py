import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("7571918160:AAH0WwDkgK5qhWQQGmC6m-r0SkC-ig9tIp8", parse_mode="MARKDOWN")

@bot.message_handler(commands=['start'])
def start(message, page=1, previous_message=None):

    #подключаемся к БД
    connect = sqlite3.connect("C:/Users/Redmi/OneDrive/Рабочий стол/sql/test1.db")
    cursor = connect.cursor()

    pages_count_query = cursor.execute(f"SELECT COUNT(*) FROM `mesta`")
    pages_count = int(pages_count_query.fetchone()[0])


    page_query = cursor.execute(f"SELECT `name`, `text` FROM `mesta` WHERE `id` = ?;", (page,))
    name, text = page_query.fetchone()

    msg = f"*{name}*\n       Что вас ждет?\n  - {text}" # вывод текста

    cursor.execute("SELECT `photo` FROM `mesta` WHERE id= ?;", (page,))  # фото из БД &&&&&&&&&&
    row = cursor.fetchone()
    a = bytes
    if row is not None:
        a = row[0]

    buttons = types.InlineKeyboardMarkup()

    left = (int(page) - 1) if (page != 1) else pages_count
    right = (int(page) + 1) if (page != pages_count) else 1

    # кнопки
    left_button = types.InlineKeyboardButton("←", callback_data=f"to {left}")
    right_button = types.InlineKeyboardButton("→", callback_data=f"to {right}")
    buy_button = types.InlineKeyboardButton("Меню", callback_data="return")
    buttons.add(left_button, right_button)
    buttons.add(buy_button)


    bot.send_photo(message.chat.id, photo=a, caption=msg, reply_markup=buttons)

    try:
        bot.delete_message(message.chat.id, previous_message.id)
    except:
        pass

    cursor.close()
    connect.close()

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if 'to' in c.data:
        page = c.data.split(' ')[1]
        start(c.message, page=page, previous_message=c.message)
    if 'return' == c.data:
        bot.send_message(c.message.chat.id, f'Чем могу Вам еще помочь?')
