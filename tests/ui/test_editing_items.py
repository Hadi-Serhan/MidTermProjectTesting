import os
import uuid

from tests.ui.base_ui import BaseVaultwardenTest
from tests.ui.pages.dashboard_page import DashboardPage
from tests.ui.pages.login_page import LoginPage

EMAIL = os.getenv("VW_EMAIL", "hadixserhan@gmail.com")
PASSWORD = os.getenv("VW_PASSWORD", "Hadi123456789123")


class EditItemTest(BaseVaultwardenTest):
    def test_edit_item_username_and_cleanup(self):
        # unique item name to avoid collisions
        name = f"EditFlow {str(uuid.uuid4())[:6]}"
        new_user = "after_user"

        # Create item
        (
            LoginPage(self.driver)
            .enter_email(EMAIL)
            .click_continue()
            .enter_password(PASSWORD)
            .click_login()
            .click_new_button()
            .select_menu_item("Login")
            .enter_item_name(name)
            .enter_item_username("before_user")
            .enter_item_password("before_pass")
            .enter_website("https://example.com")
            .save_item()
            .assert_toast_message(any_of=["Item added", "Item saved", "Item created"], timeout=10)
            .close_popup()
        )

        # Open item by name → View dialog → click Edit
        dp = DashboardPage(self.driver)
        (
            dp.open_item_by_name(name)
            .click_edit_in_view()
            .update_username(new_user)
            .save_changes()
            .assert_toast_message(any_of=["Item updated", "Item saved"], timeout=10)
            .close_popup()
        )
        (
            dp.open_item_options_for(name)
            .click_delete()
            .confirm_delete()
            .assert_toast_message(
                any_of=["Item sent to trash", "Item moved to trash", "Item deleted"], timeout=10
            )
        )
