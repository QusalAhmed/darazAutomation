import telebot
from database import Connection


class TeleBot:
    def __init__(self):
        connection = Connection()
        cursor = connection.cursor
        cursor.execute('SELECT value FROM essentials WHERE name = %s', ('bot_token',))
        bot_token = cursor.fetchone()[0]
        self.bot = telebot.TeleBot(bot_token, parse_mode='MarkdownV2')

        # bot_names = ['bot', 'response_bot', 'campaign_bot', 'general_bot']
        # self.bot_list = {}
        # for bot_info in bot_names:
        #     cursor.execute('SELECT value FROM essentials WHERE name = %s', (bot_info + '_token',))
        #     bot_token = cursor.fetchone()[0]
        #     self.bot_list[bot_info] = telebot.TeleBot(bot_token, parse_mode='MarkdownV2')

        self.bot_list = {
            'message': self.bot,
            'response_bot': self.bot,
            'campaign_bot': self.bot,
            'general_bot': self.bot
        }
