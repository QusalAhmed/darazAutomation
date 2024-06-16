# Local imports
from .bot_instance import TeleBot
from database import Connection
from sender import campaign_alert
from text_modifier import to_md, simplified_text

bot = TeleBot().bot
connection = Connection()
cursor = connection.cursor


@bot.message_handler(commands=['start', 'info'])
def send_welcome(message):
    cursor.execute('SELECT remark FROM login_credential order by remark')
    stat = ''
    for shop_stat in cursor.fetchall():
        stat += "{}\n".format(shop_stat[0])
    bot.send_message(message.chat.id, stat)


@bot.message_handler(commands=['retry'])
def retry(message):
    replied_text = message.reply_to_message.text
    if replied_text.startswith('☠Reply Dropped'):
        query = replied_text.split('🕊')[1].split('➥')[0].strip()
        reply = replied_text.split('➥')[1].split('࿐')[0].strip()
        shop_name = replied_text.split('彡')[1].split('🕊')[0].strip()
        customer_name = replied_text.split('࿐')[1].split('🗝️')[0].strip()
        message_id = int(replied_text.split('🗝️')[1].strip())
        cursor.execute('INSERT INTO external_reply '
                       '(query, reply, shop_name, customer_name, message_id) VALUES (%s, %s, %s, %s, %s)',
                       (query, reply, shop_name, customer_name, message_id))
        connection.commit()
        bot.reply_to(message, '_Inserted to retry_࿐')


@bot.message_handler(commands=['debug'])
def send_welcome(message):
    cursor.execute('SELECT value from essentials WHERE name = %s', ('debug',))
    debug_status = '1' if cursor.fetchone()[0] == '0' else '0'
    cursor.execute('UPDATE essentials SET value = %s WHERE name = %s', (debug_status, 'debug'))
    connection.commit()
    bot.send_message(message.chat.id, '_Debug Mode {}_'.format('On' if not debug_status else 'Off'))


@bot.message_handler(commands=['send'])
def send_welcome(message):
    cursor.execute('DELETE FROM send_time where TRUE')
    connection.commit()
    bot.reply_to(message, '_Message Queue Cleared_')


@bot.message_handler(commands=['campaign'])
def send_welcome(message):
    campaign_alert('message')
    bot.reply_to(message, '_Processed_')


@bot.message_handler(commands=['pause', 'p'])
def pause_campaign_alert(message):
    replied_text = message.reply_to_message.text
    try:
        if replied_text.split(' ')[0] == 'Join' and replied_text.split(' ')[1] == 'Campaign':
            campaign_name = replied_text.split('☪')[1].strip()
            shop_name = replied_text.split('彡')[1].split('🪐')[0].strip()
            cursor.execute('UPDATE campaign_alert SET status = %s WHERE name = %s AND shop_name = %s',
                           ('False', campaign_name, shop_name))
            connection.commit()
            bot.reply_to(message, '_Campaign Alert Paused_\n📌{}'.format(to_md(campaign_name)))
            return True
    except Exception as pause_error:
        print(pause_error)
        bot.reply_to(message, '_Can\'t process your reply_࿐')


@bot.message_handler(commands=['clear'])
def pause_campaign_alert(message):
    argument = message.text.split(' ')[1]
    if argument is None:
        bot.reply_to(message, '_Give an argument_')
        return True
    allowed_process = ('send_time', 'external_reply', 'reply_fix', 'campaign_alert')
    if argument in allowed_process:
        cursor.execute('DELETE FROM {} where TRUE'.format(argument))
        connection.commit()
        bot.reply_to(message, '•{}• _Cleared_✄'.format(to_md(argument)))
    else:
        bot.reply_to(message, '_Access not found_ 🗝️')


@bot.message_handler(commands=['process'])
def show_process(message):
    cursor.execute('SELECT * FROM process_time order by process_name')
    process_details = cursor.fetchall()
    message_text = ''
    for process_detail in process_details:
        serial, name, execution_time, shop_name = process_detail
        message_text += '*{}*: {} ➤ {}\n'.format(to_md(name), to_md(shop_name), execution_time)
    bot.send_message(message.chat.id, message_text)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    message_text = message.text

    # Check if the message is a reply to another message
    if message.reply_to_message:
        replied_message_text = message.reply_to_message.text
        if not replied_message_text:
            replied_message_text = message.reply_to_message.caption
        # Store replied messages in the database
        store_replied_message(message, chat_id, message_text, replied_message_text)
    else:
        echo_message(chat_id, message_text)


# Function to store replied messages in the database
def store_replied_message(message, chat_id, message_text, replied_message):
    if replied_message.startswith('✺Extra'):
        replied_message_text = replied_message.split('✺Extra')[1].strip()
    else:
        replied_message_text = replied_message
    try:
        shop_name = replied_message_text.split('♯')[0].strip()
        query = replied_message_text.split('➤')[1].split('࿐')[0].strip()
        customer_name = replied_message_text.split('࿐')[1].strip()
    except IndexError:
        bot.reply_to(message, "_Can't process your reply_࿐")
        # bot.send_message(chat_id, "_Can't process your reply_࿐")
        return True
    if message_text[-1] == '*':
        message_text = message_text[:-1]
        cursor.execute(
            'INSERT INTO reply_fix (reply, shop_name, customer_name, message_id) VALUES (%s, %s, %s, %s)',
            (message_text, shop_name, customer_name, message.message_id))
        connection.commit()
        return True
    if message_text[0] == '$':
        message_text = message_text[1:]
        # Store the replied message in the database if already not present
        cursor.execute("SELECT * FROM auto_reply WHERE message = %s", (simplified_text(query),))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO auto_reply (message, reply) VALUES (%s, %s)',
                           (simplified_text(query), message_text))
            connection.commit()
            bot.send_message(chat_id, "_Reply saved successfully_࿐")
            return True
    elif replied_message.startswith('✺Extra'):
        cursor.execute(
            'INSERT INTO reply_fix (reply, shop_name, customer_name, message_id) VALUES (%s, %s, %s, %s)',
            (message_text, shop_name, customer_name, message.message_id))
        connection.commit()
        return True
    cursor.execute('SELECT * FROM external_reply WHERE (query, shop_name, customer_name) = (%s, %s, %s)',
                   (simplified_text(query), shop_name, customer_name,))
    if cursor.fetchone() is not None:
        bot.send_message(chat_id, "_Already replied_࿐")
    cursor.execute(
        'INSERT INTO external_reply ('
        'query, reply, shop_name, customer_name, message_id) VALUES (%s, %s, %s, %s, %s)',
        (simplified_text(query), message_text, shop_name, customer_name, message.message_id))
    connection.commit()
    cursor.execute('DELETE FROM send_time WHERE (shop_name, customer_name) = (%s, %s)',
                   (shop_name, customer_name))
    connection.commit()


# Function to echo normal replies
def echo_message(chat_id, message_text):
    bot.send_message(chat_id, '{}: {}'.format(chat_id, to_md(message_text)))
