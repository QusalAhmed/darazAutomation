from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import (TimeoutException, NoSuchElementException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

# Local imports
from load_page import LoadPage
from database import Connection

connection = Connection()
cursor = connection.cursor


def setup_chat_interface(instance, row):
    print(f'Setting up chat interface for {row[1]}...')
    driver: webdriver.Chrome = instance.get_driver()
    wait: WebDriverWait = instance.get_wait()

    load_page = LoadPage(instance)
    load_page.chat_page_load()
    try:
        additional_setup(instance)
    except NoSuchElementException:
        print('Additional setup failed')
        pass
    try:
        WebDriverWait(driver, 5).until(ec.element_to_be_clickable((By.CLASS_NAME, 'next-dialog-close-icon'))).click()
    except TimeoutException:
        print('Chat setting dialog close failed')
        pass
    except Exception as e:
        print(e)
        pass
    # wait.until_not(ec.presence_of_all_elements_located((By.CLASS_NAME, 'next-loading-tip')))
    wait.until(ec.element_to_be_clickable(
        (By.CSS_SELECTOR, '.next-tabs-tab:nth-child(1) .next-tabs-tab-inner'))).click()
    wait.until(ec.element_to_be_clickable(
        (By.CSS_SELECTOR, '.aplus-auto-exp:nth-child(2) .next-tag-body'))).click()
    unread_text = driver.find_element(
        By.XPATH, "//*[contains(@class, 'filter-bar')]//*[contains(text(), 'UnRead (')]").text
    if int(unread_text.split('(')[1].split(')')[0]) > 0:  # Check unread message number
        try:
            wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "[role='alert'] button"))).click()
        except TimeoutException:
            pass
    cursor.execute('UPDATE process_time SET execution_time = %s WHERE (shop_name, process_name) = (%s, %s)',
                   (datetime.now(), row[1], 'check_message_status',))
    connection.commit()


def additional_setup(instance):
    driver: webdriver.Chrome = instance.get_driver()
    wait: WebDriverWait = instance.get_wait()
    if driver.find_element(By.ID, '___reactour'):
        wait.until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, '.asc-tour-helper-control .next-btn-helper'))).click()
        wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '.asc-tour-helper-close.next-dialog-close'))).click()
        wait.until(ec.element_to_be_clickable((By.XPATH, '//div[@data-spm="d_btn_link_chat"]'))).click()
