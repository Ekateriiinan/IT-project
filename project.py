import telebot 
import webbrowser
from telebot import types

bot = telebot.TeleBot('7571918160:AAH0WwDkgK5qhWQQGmC6m-r0SkC-ig9tIp8')

def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton("Перейти на сайт")
    markup.row(btn1)
    btn2 = types.KeyboardButton("Поставить рейтинг")
    btn3 = types.KeyboardButton("Написать отзыв")
    markup.row(btn2, btn3)
    bot.reply_to(message, 'Перейдите в карты', reply_markup=markup)


# @bot.message_handler(content_types=['photo'])
# def photo(message): #информация про пользователя и чат 
#     markup = types.InlineKeyboardMarkup()
#     btn1 = types.InlineKeyboardButton("Перейти на сайт", url='https://yandex.ru/maps/213/moscow/?ll=37.642884%2C55.772239&source=serp_navig&z=10')
#     markup.row(btn1)
#     btn2 = types.InlineKeyboardButton("Поставить рейтинг", callback_data='delete')
#     btn3 = types.InlineKeyboardButton("Написать отзыв", callback_data='рейтинг')
#     markup.row(btn2, btn3)
#     bot.reply_to(message, 'Перейдите в карты', reply_markup=markup)

# @bot.add_callback_query_handler(func=lambda callback: True)
# def callback_messange(callback):
#     if callback.data == 'delete':
#         bot.delete_message(callback.message.chat.id, callback.message.message_id)

@bot.message_handler(commands=['start'])
def main(message): #информация про пользователя и чат 
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')


@bot.message_handler(commands=['mesto']) # открываем сайт 
def site(message):
    webbrowser.open("https://kudago.com/msk/")



bot.polling(non_stop=True)

# @bot.message_handler()
# def info(message):
#     if message.text.lower() == 'место':
#         bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}")
#     elif message.text.lower() == 'id':
#         bot.reply_to(message, f'ID:{message.from_user.id}') #ответ на соообщение 

# @bot.message_handler(content_types=['photo'])
# def get_photo(message): #информация про пользователя и чат 
#     markup = types.InlineKeyboardMarkup()
#     markup.add(types.InlineKeyboardButton("Перейти на сайт", url='https://yandex.ru/maps/213/moscow/?ll=37.642884%2C55.772239&source=serp_navig&z=10'))



# @bot.message_handler(commands=['mesto'])
# def mesto(message): #информация про пользователя и чат 
#     bot.send_message(message.chat.id, 'Введите место')

