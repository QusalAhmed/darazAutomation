import telebot

from .message_handler import Handler

bot_list = Handler().bot_list

chat_id_list = ('1783177827', '6378024334',)


def send_message(message, bot_name='message', message_id=None):
    try:
        for chat_id in chat_id_list:
            bot_list[bot_name].send_message(chat_id, message, reply_to_message_id=message_id)
    except telebot.apihelper.ApiTelegramException as e:
        print(e)
        send_message(message, bot_name, message_id)


def send_photo(photo_url, caption):
    try:
        for chat_id in chat_id_list:
            bot_list['message'].send_photo(chat_id, photo_url, caption=caption, show_caption_above_media=True)
    except telebot.apihelper.ApiTelegramException as e:
        print(e)
        send_photo(photo_url, caption)


def delete_message(chat_id, message_id, bot_name='message'):
    try:
        bot_list[bot_name].delete_message(chat_id, message_id)
    except telebot.apihelper.ApiTelegramException as e:
        print(e)


def start_bot():
    bot = Handler().bot
    bot.infinity_polling()
