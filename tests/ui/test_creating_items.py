# tests/ui/test_creating_items.py
import os
from tests.ui.pages.login_page import LoginPage
from tests.ui.base_ui import BaseVaultwardenTest  
EMAIL = os.getenv("VW_EMAIL", "hadixserhan@gmail.com")
PASSWORD = os.getenv("VW_PASSWORD", "Hadi123456789123")

class CreatingItemsTest(BaseVaultwardenTest):
    def test_create_new_item(self):
        (LoginPage(self.driver)
            .enter_email(EMAIL).click_continue()
            .enter_password(PASSWORD).click_login()
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