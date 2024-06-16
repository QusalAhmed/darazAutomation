from selenium.webdriver.common.by import By
from selenium.common.exceptions import (TimeoutException)
from selenium.webdriver.support import expected_conditions as ec

# local imports
import telegram
from connection import wait_for_connection


class LoadPage:
    def __init__(self, instance):
        self.driver = instance.get_driver()
        self.wait = instance.get_wait()
        self.triumph: int = 0

    def page_load(self, url, element='body'):
        try:
            self.driver.get(url)
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, element)))
        except TimeoutException:
            print('Page loading failed: {}'.format(url))
            self.triumph += 1
            if self.triumph > 10:
                raise Exception('Page loading failed {} times'.format(self.triumph))
            elif self.triumph >= 5:
                print('Page loading failed {} times'.format(self.triumph))
                wait_for_connection()
            self.page_load(element)
        return True

    def chat_page_load(self):
        try:
            self.driver.get('https://sellercenter.daraz.com.bd/apps/im/chat')
            self.wait.until(
                ec.presence_of_element_located((By.CSS_SELECTOR, '.next-tabs-nav-container-scrolling')))
        except TimeoutException:
            print('Chat page loading failed')
            self.triumph += 1
            if self.triumph >= 5:
                print('Chat page loading failed {} times'.format(self.triumph))
                telegram.bot.send_message(telegram.chat_id, 'Chat page loading failed {} times'.
                                          format(self.triumph))
                wait_for_connection()
            self.chat_page_load()
