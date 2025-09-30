# tests/ui/test_restore_items.py
import os
import uuid

from tests.ui.base_ui import BaseVaultwardenTest
from tests.ui.pages.dashboard_page import DashboardPage
from tests.ui.pages.login_page import LoginPage

EMAIL = os.getenv("VW_EMAIL", "hadixserhan@gmail.com")
PASSWORD = os.getenv("VW_PASSWORD", "Hadi123456789123")


class RestoreItemTest(BaseVaultwardenTest):
    def test_restore_item_from_trash(self):
        # unique item name
        name = f"RestoreFlow {str(uuid.uuid4())[:6]}"

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
            .enter_item_username("restore_user")
            .enter_item_password("restore_pass")
            .enter_website("https://example.com")
            .save_item()
            .assert_toast_message(any_of=["Item added", "Item saved", "Item created"], timeout=10)
            .close_popup()
        )

        dp = DashboardPage(self.driver)

        # Delete it (to send to Trash)
        (
            dp.open_item_options_for(name)
            .click_delete()
            .confirm_delete()
            .assert_toast_message(
                any_of=["Item sent to trash", "Item moved to trash", "Item deleted"], timeout=10
            )
        )

        # Go to Trash and verify it is there
        dp.go_to_trash().assert_row_present(name)

        # Restore -> assert toast
        (
            dp.restore_item_from_trash(name).assert_toast_message(
                any_of=["Item restored", "Item moved", "Item updated"], timeout=10
            )
        )

        # Back to All Items and verify it returned
        dp.go_to_all_items().assert_row_present(name)

        # Cleanup: remove again to keep vault clean
        (
            dp.open_item_options_for(name)
            .click_delete()
            .confirm_delete()
            .assert_toast_message(
                any_of=["Item sent to trash", "Item moved to trash", "Item deleted"], timeout=10
            )
        )
