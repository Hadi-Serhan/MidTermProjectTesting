from .base_ui import BaseVaultwardenTest
from .pages.login_page import LoginPage

class CreatingItemsTest(BaseVaultwardenTest):

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