# from .base_ui import BaseVaultwardenTest
# from .pages.login_page import LoginPage

# class CreatingItemsTest(BaseVaultwardenTest):

#     def test_create_new_item(self):
#         (LoginPage(self.driver)
#             .enter_email("hadixserhan@gmail.com").click_continue()
#             .enter_password("Hadi123456789123").click_login()
#             .click_new_button().select_menu_item("Login")
#             .enter_item_name("Test Login Item")
#             .enter_item_username("testuser")
#             .enter_item_password("testpassword")
#             .enter_website("https://example.com")
#             .save_item()
#             .assert_toast_message("Item added") 
#             .close_popup()
#             .open_item_options_for("Test Login Item")
#             .click_delete()
#             .confirm_delete()
#             .assert_toast_message("Item sent to trash")
#         )


# tests/ui/test_creating_items.py
import os
from tests.ui.pages.login_page import LoginPage
from tests.ui.base_ui import BaseVaultwardenTest  # whatever your base class is named

VW_URL = os.getenv("VAULTWARDEN_URL", "http://localhost:3000")
VW_EMAIL = os.getenv("VW_EMAIL")
VW_PASSWORD = os.getenv("VW_PASSWORD")

class CreatingItemsTest(BaseVaultwardenTest):
    def setUp(self):
        super().setUp(base_url=VW_URL)  # your BaseUITest should accept base_url

    def test_create_new_item(self):
        assert VW_EMAIL and VW_PASSWORD, "VW_EMAIL/VW_PASSWORD must be set for UI tests"

        (LoginPage(self.driver)
            .enter_email(VW_EMAIL).click_continue()
            .enter_password(VW_PASSWORD).click_login()
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
