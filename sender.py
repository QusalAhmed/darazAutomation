import time
from datetime import datetime, timedelta

# Local imports
import telegram
from database import Connection
from text_modifier import to_md

connection = Connection()
cursor = connection.cursor


def send_message(message_text, notify=False, bot_name='message'):
    chat_id = '1783177827'
    chat_ids = ('1783177827', '6378024334')
    bot_list = telegram.bot_list
    match bot_name:
        case 'response':
            bot_list['response_bot'].send_message(chat_id, message_text, disable_notification=notify)
        case 'campaign':
            bot_list['campaign_bot'].send_message(chat_id, message_text, disable_notification=notify)
        case 'general':
            for chat_id in chat_ids:
                bot_list['general_bot'].send_message(chat_id, message_text, disable_notification=notify)
        case 'message':
            for chat_id in chat_ids:
                bot_list['message'].send_message(chat_id, message_text, disable_notification=notify)


def campaign_alert(bot_name='campaign'):
    cursor.execute('SELECT * FROM campaign_alert')
    for campaign in cursor.fetchall():
        serial, campaign_name, shop_name, time_left, status = campaign
        time_difference = (datetime.strptime(time_left, '%Y-%m-%d %H:%M:%S') -
                           datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S'))
        hour_left = time_difference.seconds // 3600
        minute_left = (time_difference.seconds % 3600) // 60
        if time_difference > timedelta(minutes=0) and status == 'True':
            send_message('Join Campaign 彡*{}* 🪐{}Hour(s) {}Minute(s) left\n☪{}'.
                         format(shop_name, hour_left, minute_left, to_md(campaign_name)), bot_name=bot_name)
        elif time_difference <= timedelta(minutes=0):
            cursor.execute('DELETE FROM campaign_alert WHERE serial = %s', (serial,))
            connection.commit()
    cursor.execute("UPDATE process_time SET execution_time = %s WHERE process_name = %s",
                   (datetime.now(), 'campaign_alert'))
    connection.commit()
