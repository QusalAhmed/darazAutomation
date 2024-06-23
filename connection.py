import time
import requests


def check_connection():
    response = requests.get('https://fast.com/')
    if response.status_code == 200:
        return True
    else:
        return False


def wait_for_connection():
    while True:
        try:
            request = requests.get('https://sellercenter.daraz.com.bd')
            if request.status_code == 200:
                break
        except Exception as connection_error:
            print(connection_error)
            time.sleep(30)
