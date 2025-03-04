import telebot 

bot = telebot.TeleBot('7571918160:AAH0WwDkgK5qhWQQGmC6m-r0SkC-ig9tIp8')

@bot.message_handlers(commands=['start'])
def main(message): #информация про пользователя и чат 
    bot.send_message(message.chat.id, 'Привет!')
