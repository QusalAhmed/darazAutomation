import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

# Local imports
from database import Connection
from load_page import LoadPage

# Database connection
connection = Connection()
cursor = connection.cursor


class Login:
    def __init__(self, login_credentials, instance):
        self.shop_id, self.shop_name, self.email, self.password, self.cookie, self.remark = login_credentials
        self.driver: webdriver.Chrome = instance.get_driver()
        self.wait: WebDriverWait = instance.get_wait()
        self.load_page = LoadPage(instance).page_load
        self.load_chat_page = LoadPage(instance).chat_page_load

    def full(self):
        if not self.load_cookie():
            self.fill_credentials()

    def load_cookie(self):
        self.load_page('https://sellercenter.daraz.com.bd/apps/seller/login')
        cookies = json.loads(self.cookie)
        for cookie_data in cookies:
            self.driver.add_cookie(cookie_data)
        print('Cookies loaded')
        if self.login_status():
            print('Login successful using cookie')
            return True
        else:
            print('Login failed via cookie')
            return False

    def fill_credentials(self):
        self.driver.delete_all_cookies()
        self.load_page('https://sellercenter.daraz.com.bd/apps/seller/login')
        # self.wait.until(ec.presence_of_element_located((By.ID, 'account'))).send_keys(self.email)
        # self.wait.until(ec.presence_of_element_located((By.ID, 'password'))).send_keys(self.password)
        # self.wait.until(ec.presence_of_element_located((By.NAME, 'submit'))).click()

        # For old login page
        (self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, ".accountContent [type='text']"))).
         send_keys(self.email))
        self.driver.find_element(By.CSS_SELECTOR, ".accountContent [type='password']").send_keys(self.password)
        self.driver.find_element(By.CSS_SELECTOR, ".loginButtonStyle").click()
        self.wait.until(ec.url_contains('https://sellercenter.daraz.com.bd/apps/home/new'))

        if self.login_status():
            print('Login successful using credentials')
            # Update cookie
            new_cookie = json.dumps(self.driver.get_cookies())
            cursor.execute('UPDATE login_credential SET cookie = %s WHERE id = %s', (new_cookie, self.shop_id))
            cursor.execute(
                "UPDATE process_time SET execution_time = %s WHERE (shop_name, process_name) = (%s, %s)",
                (datetime.now(), self.shop_name, 'login_time'))
            connection.commit()
        else:
            print('Login failed via credentials')
            return False

    def login_status(self):
        self.load_chat_page()
        return 'apps/im/chat' in self.driver.current_url
