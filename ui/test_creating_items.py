from ui.base_ui_test import BaseVaultwardenTest
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.item_page import ItemPage
import time

class CreatingItemsTest(BaseVaultwardenTest):
    # def test_create_new_item(self):
    #     login_page = LoginPage(self.driver)
    #     login_page.enter_email("hadixserhan@gmail.com")
    #     login_page.click_continue()
    #     login_page.enter_password("Hadi123456789123")
    #     login_page.click_login()

    #     # Wait for dashboard
    #     self.wait.until(lambda d: "Vault" in d.title)

    #     dashboard_page = DashboardPage(self.driver)
    #     dashboard_page.click_new_button()
    #     time.sleep(1)
    #     dashboard_page.select_menu_item("Login")
    #     time.sleep(1)
    #     item_page = ItemPage(self.driver)
        # item_page.enter_item_name("Test Login Item")
        # item_page.enter_item_username("testuser")
        # item_page.enter_item_password("testpassword")
        # item_page.enter_website("https://example.com")
        # item_page.save_item()
        # item_page.assert_toast_message("Item added")
        # item_page.close_popup()
        # item_page.open_item_options()
        # item_page.click_delete()
        # item_page.assert_toast_message("Item sent to trash")

    def test_create_new_item(self):
        (LoginPage(self.driver)
            .enter_email("hadixserhan@gmail.com").click_continue()
            .enter_password("Hadi123456789123").click_login()
            .click_new_button().select_menu_item("Login")
            .enter_item_name("Test Login Item")
            .enter_item_username("testuser")
            .enter_item_password("testpassword")
            .enter_website("https://example.com")
            .save_item()
            .assert_toast_message("Item added") 
            .close_popup()
            .open_item_options_for("Test Login Item")
            .click_delete()
            .confirm_delete()
            .assert_toast_message("Item sent to trash")
        )