from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

# Local imports
from load_page import LoadPage


def setup(instance):
    driver: webdriver.Chrome = instance.get_driver()
    wait: WebDriverWait = instance.get_wait()

    load_page = LoadPage(instance)

    load_page.chat_page_load()
    try:
        driver.find_element(By.CLASS_NAME, 'next-overlay-inner')
        wait.until(ec.visibility_of_element_located((By.CLASS_NAME, 'next-dialog-close-icon'))).click()
    except NoSuchElementException:
        pass
    wait.until(ec.element_to_be_clickable(
        (By.CSS_SELECTOR, '.next-tabs-tab:nth-child(1) .next-tabs-tab-inner'))).click()
    wait.until(ec.element_to_be_clickable(
        (By.CSS_SELECTOR, '.aplus-auto-exp:nth-child(2) .next-tag-body'))).click()

