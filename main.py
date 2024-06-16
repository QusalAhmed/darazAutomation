# Local imports
from database import Connection
from instance import DriverSetup
from login import Login
from setup_chat import setup
from check_message import check_message

if __name__ == "__main__":
    # Collect all instances and setup chat window
    instances: list = []
    cursor = Connection().cursor
    cursor.execute("SELECT * FROM login_credential ORDER BY id LIMIT 1")
    for row in cursor.fetchall():
        instance = DriverSetup()
        Login(row, instance).full()
        setup(instance)
        instances.append((instance, row))

    # Check messages
    for instance, row in instances:
        # check_message(instance, row)
        pass

    cursor.close()
    Connection().close()
