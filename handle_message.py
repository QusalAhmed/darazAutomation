import re
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.common.exceptions import (TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

# Local imports
import telegram
from database import Connection
from instance import Locator
from setup_chat import setup_chat_interface
from text_modifier import to_md


def to_only_alphabet(text):
    return re.sub(r'[^a-zA-Z ➛]', '', text).lower()


class CheckMessage(Locator):
    def __init__(self, instance, row):
        self.instance = instance
        self.row = row
        self.driver: webdriver.Chrome = instance.get_driver()
        self.wait: WebDriverWait = instance.get_wait()
        super().__init__(instance)
        self.shop_name = row[1]

        self.connection = Connection()
        self.cursor = self.connection.cursor

    def infinity_checking(self):
        start_time = time.time()
        print(f'Message checking {self.shop_name}...')
        # Collect external reply to delete unused reply
        self.cursor.execute('SELECT * FROM external_reply WHERE shop_name = %s', (self.shop_name,))
        external_reply_array = self.cursor.fetchall()
        self.cursor.execute('SELECT execution_time FROM process_time WHERE shop_name = %s AND process_name = %s',
                            (self.shop_name, 'check_message_status',))
        setting_time = self.cursor.fetchone()[0]
        if datetime.now() - setting_time > timedelta(hours=1):
            setup_chat_interface(self.instance, self.row)
            self.cursor.execute(
                'UPDATE process_time SET execution_time = %s WHERE (shop_name, process_name) = (%s, %s)',
                (datetime.now(), self.shop_name, 'check_message_status',))
        self.main(external_reply_array)
        self.delete_reply(external_reply_array)
        print(f'Message checked {self.shop_name} in {time.time() - start_time:.2f} seconds')
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.cursor.execute('SELECT * FROM run_time WHERE shop_name = %s', (self.shop_name,))
        if self.cursor.fetchone():
            self.cursor.execute('UPDATE run_time SET message_check_duration = %s WHERE shop_name = %s',
                                (f'{elapsed_time:.2f}', self.shop_name,))
        else:
            self.cursor.execute('INSERT INTO run_time (shop_name, message_check_duration) VALUES (%s, %s)',
                                (self.shop_name, f'{elapsed_time:.2f}',))
        # self.cursor.execute('UPDATE run_time SET message_check_duration = %s WHERE shop_name = %s',
        #                     (f'{elapsed_time:.2f}', self.shop_name,))
        self.cursor.execute('UPDATE run_time SET message_check = %s WHERE shop_name = %s',
                            (datetime.now(), self.shop_name,))
        self.connection.commit()

    def main(self, pre_external_reply_array):
        unreplied_text = self.locate_clickable(
            (By.XPATH, "//*[contains(@class, 'filter-bar')]//*[contains(text(), 'Unreplied (')]")).text
        if int(unreplied_text.split('(')[1].split(')')[0]) > 0:
            message_elements = self.wait.until(ec.presence_of_all_elements_located(
                (By.CSS_SELECTOR, '.im-ui-session-virtualize-list [data-spm="im_session_item"]')))
            for message_element in message_elements:
                message_element.click()
                # Checking for message interface is ready
                self.wait.until_not(
                    ec.visibility_of_element_located(
                        (By.CSS_SELECTOR, '.next-loading.next-open.next-loading-inline')) or
                    ec.visibility_of_element_located((By.CSS_SELECTOR, '.next-icon.next-icon-loading.next-medium'))
                )

                customer_name = message_element.find_element(
                    By.CSS_SELECTOR, '[style="flex-flow: row; justify-content: space-between;"] span').text
                receive_time_element = message_element.find_element(
                    By.CSS_SELECTOR, '[style="flex-flow: row; justify-content: space-between;"] div').text
                try:
                    receiving_hour, receiving_minute = receive_time_element.split(':')
                except ValueError:
                    receiving_hour, receiving_minute = [0, 0]
                receive_time = datetime.now().replace(hour=int(receiving_hour), minute=int(receiving_minute))

                query_array = self.scrap_query()
                raw_query = '➛'.join(query_array).strip()

                # Check if there is auto reply
                auto_reply_array = []
                for query in query_array:
                    self.cursor.execute('SELECT reply FROM auto_reply WHERE message = %s',
                                        (to_only_alphabet(query),))
                    auto_reply = self.cursor.fetchone()
                    if auto_reply:
                        auto_reply_array.append(auto_reply[0])
                    else:
                        self.cursor.execute("SELECT reply FROM auto_reply WHERE SIMILARITY (message, %s) > 0.75",
                                            (to_only_alphabet(query),))
                        auto_reply = self.cursor.fetchone()
                        if auto_reply:
                            auto_reply_array.append(auto_reply[0])
                        else:
                            auto_reply_array.clear()
                            break

                # If auto reply found, reply
                if auto_reply_array:
                    if (''.join(auto_reply_array) == 'কিভাবে সহায়তা করতে পারি?' and
                            datetime.now() - receive_time < timedelta(minutes=1)):
                        break
                    if not self.send_reply(auto_reply_array):
                        return False
                    self.fix_check(query_array, self.shop_name, customer_name)
                    for auto_reply in auto_reply_array:
                        telegram.send_message(
                            '{} ♯{} ➤{}\n➥ {}'.
                            format(to_md(self.shop_name), receive_time_element,
                                   to_md(raw_query), to_md(auto_reply)), bot_name='response_bot')
                    self.fix_check(query_array, self.shop_name, customer_name)
                    self.main(pre_external_reply_array)
                    break

                # Check for external reply
                self.cursor.execute(
                    'SELECT reply FROM external_reply WHERE (shop_name, customer_name, query) = (%s, %s, %s)',
                    (self.shop_name, customer_name, raw_query))
                external_reply_array = [x[0] for x in self.cursor.fetchall()]
                if external_reply_array:
                    if not self.send_reply(external_reply_array):
                        return False
                    for external_reply in external_reply_array:
                        telegram.send_message(
                            '{} ♯{} ➤{}\n╰┈➤ {}'.
                            format(to_md(self.shop_name), receive_time_element, to_md(raw_query),
                                   to_md(external_reply.replace('\n', '╗'))), bot_name='response_bot')
                        self.cursor.execute(
                            'DELETE FROM external_reply WHERE (shop_name, customer_name, reply) = (%s, %s, %s)',
                            (self.shop_name, customer_name, external_reply,))
                    self.cursor.execute(
                        'DELETE FROM send_time WHERE (shop_name, customer_name, query) = (%s, %s, %s)',
                        (self.shop_name, customer_name, raw_query))
                    self.connection.commit()
                    # Remove reply from pre_external_reply_array
                    for pre_external_reply in pre_external_reply_array:
                        for external_reply in external_reply_array:
                            if pre_external_reply[4] == external_reply:
                                pre_external_reply_array.remove(pre_external_reply)
                    self.fix_check(query_array, self.shop_name, customer_name)
                    self.main(pre_external_reply_array)
                    break

                # No reply found. Send query
                self.cursor.execute(
                    'SELECT send_time FROM send_time WHERE (shop_name, customer_name, query) = (%s, %s, %s)',
                    (self.shop_name, customer_name, raw_query))
                if self.cursor.rowcount > 0:
                    send_time = self.cursor.fetchone()[0]
                else:
                    self.cursor.execute('DELETE FROM send_time WHERE (shop_name, customer_name) = (%s, %s)',
                                        (self.shop_name, customer_name,))
                    # Insert new send time
                    self.cursor.execute(
                        'INSERT INTO send_time (shop_name, customer_name, query, send_time) VALUES (%s, %s, %s, %s)',
                        (self.shop_name, customer_name, raw_query, datetime.now()),
                    )
                    self.connection.commit()
                    send_time = datetime(1970, 1, 1)
                if datetime.now() - send_time > timedelta(minutes=30):
                    telegram.send_photo(
                        self.driver.get_screenshot_as_png(), '*{}* ♯{} ➤{}\n࿐{}'.
                        format(to_md(self.shop_name), receive_time_element, to_md(raw_query), to_md(customer_name)))
                    self.cursor.execute(
                        'UPDATE send_time SET send_time = %s WHERE (shop_name, customer_name, query) = (%s, %s, %s)',
                        (datetime.now(), self.shop_name, customer_name, raw_query,))
                    self.connection.commit()

        # Check for fixed reply
        self.cursor.execute('SELECT reply, customer_name FROM reply_fix WHERE shop_name = %s', (self.shop_name,))
        if self.cursor.rowcount > 0:
            fixed_reply, customer_name = self.cursor.fetchone()
            self.locate_clickable((By.XPATH, f'//div[@style="flex-flow: row; justify-content: space-between;"]'
                                             f'//*[text()="{customer_name}"]/../..')).click()
            if self.scrap_query():
                telegram.send_message('*☠Drop Fix Reply* 彡{} 🕊{}✸'.
                                      format(to_md(self.shop_name), to_md(fixed_reply)))
            else:
                self.send_reply(fixed_reply)

    def scrap_query(self, deep_level=0) -> list:
        enable = True
        query = []
        message_lines = self.locate_all((By.CSS_SELECTOR, '.im-ui-message-list .im-ui-message-item'))
        message_lines.reverse()  # Reverse the list to read the latest message
        for message_line in message_lines:
            line_class = message_line.get_attribute('class')
            if 'message-item-from-self' in line_class:
                if enable:
                    if deep_level == 0:
                        return query[::-1]
                    deep_level -= 1
                    enable = False
                if 'row-card-image' in line_class:
                    self.driver.execute_script("""
                        var element = arguments[0];
                        element.parentNode.removeChild(element);
                    """, message_line)
            elif 'message-item-from-opposite' in line_class:
                enable = True
                if 'row-card-text' in line_class:
                    query.append(message_line.text)
                elif 'row-card-image' in line_class:
                    # img_url = message_line.find_element(By.CLASS_NAME, 'card-img').get_attribute('style')
                    # query.append(img_url.split('url("')[1].split('");')[0])
                    self.driver.execute_script("""
                        var element = arguments[0];
                        element.parentNode.removeChild(element);
                    """, message_line)
                elif 'row-card-order' in line_class:
                    query.append('')
                elif 'row-card-product' in line_class:
                    query.append('')

        return query[::-1]

    def send_reply(self, reply_array):
        for reply_text in set(reply_array):
            self.locate((By.CSS_SELECTOR, '.message-input-field textarea')).send_keys(reply_text)
            self.wait.until(ec.element_to_be_clickable(
                (By.CSS_SELECTOR, '.message-bottom-field .aplus-auto-exp .im-ui-icon'))).click()
        # Check inserted data is correct
        scraped_reply_array = []
        self.wait.until_not(ec.presence_of_element_located((
            By.XPATH, "//i[@class='next-icon next-icon-loading next-medium read-type']")))
        message_lines = self.locate_all((By.CSS_SELECTOR, '.im-ui-message-list .im-ui-message-item'))
        message_lines.reverse()  # Reverse the list to read the latest message
        # Check server got the reply
        try:
            WebDriverWait(message_lines[0], 10).until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, '.message-contain .text-right')))
        except TimeoutException:
            print('Reply not sent')
            self.send_reply(reply_array)
        for message_line in message_lines:
            line_class = message_line.get_attribute('class')
            if 'message-item-from-self' in line_class:
                scraped_reply_array.append(message_line.find_element(By.CLASS_NAME, 'card-text').text)
            else:
                break
        reply_array = [x.split('\n') for x in reply_array][0]
        if '➛'.join(scraped_reply_array[:(len(reply_array) + 1)]) == '➛'.join(reply_array).replace('\n', '➛'):
            print('Reply success')
            return True
        else:
            print('Reply failed')
            print(scraped_reply_array, reply_array)
            return False

    def fix_check(self, query, shop_name, customer_name):
        # Check replied query
        replied_query = self.scrap_query(deep_level=1)
        if replied_query != query:
            telegram.send_message(f'*Fix Reply* 彡{to_md(shop_name)} 🕊{to_md(query)}✸ ࿐{to_md(customer_name)}')

    def delete_reply(self, external_reply_array):
        # Delete external reply
        for external_reply in external_reply_array:
            serial, _, customer_name, query, reply, message_id, chat_id = external_reply
            self.cursor.execute('DELETE FROM external_reply WHERE serial = %s', (serial,))
            telegram.send_message(
                '*☠Reply Dropped* 彡{} 🕊{} ➥{}\n࿐{} 🗝️{}, {}'.
                format(to_md(self.shop_name), to_md(query), to_md(reply), to_md(customer_name), message_id,
                       chat_id), message_id=message_id)
            # telegram.delete_message(chat_id, message_id)
        self.connection.commit()
