from load_page import LoadPage


def check_message(instance, login_credentials):
    driver = instance.get_driver()
    wait = instance.get_wait()
    shop_id, shop_name, email, password, cookie, remark = login_credentials
    load_page = LoadPage(instance)

    load_page.chat_page_load()
