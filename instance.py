from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# local imports
from connection import check_connection


class DriverSetup:
    def __init__(self):
        print('Driver setup started')
        if check_connection():
            service = ChromeService(ChromeDriverManager().install())
        else:
            raise ConnectionError("No internet connection")
        print('Driver setup completed')
        options = webdriver.ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument('--start-maximized')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument("--window-size=1280,1080")
        options.add_argument("--zoom=1.5")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-save-password-bubble")
        options.add_argument("--disable-single-click-autofill")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-webgl")
        options.add_argument("--enable-local-file-accesses")
        options.add_argument("--enable-automation")
        options.add_argument("--enable-javascript")
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 1,  # Allow notifications
            "profile.managed_default_content_settings.notifications": 1,
            "profile.content_settings.exceptions.notifications": {
                "https://sellercenter.daraz.com.bd,*": {
                    "setting": 1
                }
            }
        })

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(1)
        self.driver.set_page_load_timeout(20)

        self.wait = WebDriverWait(self.driver, 10)
        self.mouse = webdriver.ActionChains(self.driver)

    def get_driver(self):
        return self.driver

    def get_wait(self):
        return self.wait

    def quit_driver(self):
        self.driver.quit()


class Locator:
    def __init__(self, instance):
        self.driver: webdriver.Chrome = instance.get_driver()
        self.wait: WebDriverWait = instance.get_wait()

    def locate(self, locator):
        return self.wait.until(ec.presence_of_element_located(locator))

    def locate_all(self, locator):
        return self.wait.until(ec.presence_of_all_elements_located(locator))

    def locate_clickable(self, locator):
        return self.wait.until(ec.element_to_be_clickable(locator))
