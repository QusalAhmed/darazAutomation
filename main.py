import multiprocessing


# Local imports
import telegram
from database import Connection
from handle_message import CheckMessage
from instance import DriverSetup
from login import Login
from setup_chat import setup_chat_interface

if __name__ == "__main__":
    # Start telegram bot
    multiprocessing.Process(target=telegram.start_bot, args=()).start()
    print('Bot started')

    # Collect all instances and setup chat window
    instances: list = []
    cursor = Connection().cursor
    cursor.execute("SELECT * FROM login_credential ORDER BY id")
    for row in cursor.fetchall():
        instance = DriverSetup()
        Login(row, instance).full()
        try:
            setup_chat_interface(instance, row)
        except Exception as e:
            print(e)
            setup_chat_interface(instance, row)
        instances.append((instance, row))
        print(f'Instance {row[1]} setup')

    # Check messages
    while True:
        for instance, row in instances:
            check_message = CheckMessage(instance, row)
            try:
                check_message.infinity_checking()
            except Exception as e:
                print(e)
                setup_chat_interface(instance, row)

        print('{}'.format(' Cycle Completed '.center(40, '━')))

# import multiprocessing
# import time
# import telegram
# from test import Test
# from database import Connection
#
# connection = Connection()
# cursor = connection.cursor
#
# if __name__ == '__main__':
#     # Start telegram bot
#     multiprocessing.Process(target=telegram.start_bot, args=()).start()
#     print('Bot started')
#
#     cursor.execute("SELECT * FROM login_credential ORDER BY id LIMIT 3")
#     for row in cursor.fetchall():
#         test = Test(row)
#         test.infinity_checking()
#         time.sleep(5)
