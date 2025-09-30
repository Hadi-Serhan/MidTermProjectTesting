# tests/ui/pages/item_page.py
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage


class ItemPage(BasePage):
    def enter_item_name(self, name):
        field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="name"]'))
        )
        field.send_keys(name)
        return self

    def enter_item_username(self, username):
        field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="username"]'))
        )
        field.send_keys(username)
        return self

    def enter_item_password(self, password):
        field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="password"]'))
        )
        field.send_keys(password)
        return self

    def enter_website(self, website):
        field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="uri"]'))
        )
        field.send_keys(website)
        return self

    def save_item(self):
        save_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
        )
        try:
            save_button.click()
        except ElementClickInterceptedException:
            self._wait_for_no_overlay(10)
            self.driver.execute_script("arguments[0].click();", save_button)
        return self

    def close_popup(self):
        # Generic dialog cleanup (ESC/backdrop/close button)
        self._dismiss_dialogs(timeout=10)
        return self

    # ------- NEW: click Edit inside the 'View Login' dialog -------
    def click_edit_in_view(self):
        xpath = "//cdk-dialog-container//footer//button[.//span[normalize-space(text())='Edit'] or normalize-space(text())='Edit']"
        btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        except Exception:
            pass
        try:
            btn.click()
        except ElementClickInterceptedException:
            self._dismiss_backdrops(0.2)
            self.driver.execute_script("arguments[0].click();", btn)
        return self

    # ------- NEW: update username in the edit form -------
    def update_username(self, new_username: str):
        inp = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="username"]'))
        )
        try:
            inp.clear()
        except Exception:
            # fallback JS clear
            self.driver.execute_script("arguments[0].value='';", inp)
        inp.send_keys(new_username)
        return self

    # ------- NEW: save changes in edit form (reuse submit button) -------
    def save_changes(self):
        return self.save_item()

    def open_item_options_for(self, item_name):
        self._wait_for_no_overlay(10)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody")))
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr[bitrow]")))

        row_xpath = (
            "//table//tbody//tr[@bitrow]"
            "[.//button[@bitlink and contains(@title,'Edit item') "
            f"and normalize-space()='{item_name}']]"
        )
        row = self.wait.until(EC.visibility_of_element_located((By.XPATH, row_xpath)))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
        except Exception:
            pass

        try:
            btn = row.find_element(By.XPATH, ".//button[@aria-label='Options']")
        except Exception:
            btn = row.find_element(
                By.XPATH,
                ".//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'options')]",
            )

        try:
            btn.click()
        except ElementClickInterceptedException:
            self._wait_for_no_overlay(10)
            self.driver.execute_script("arguments[0].click();", btn)
        return self

    def click_delete(self):
        items = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button[role="menuitem"]'))
        )
        for b in items:
            if "delete" in (b.text or "").lower():
                try:
                    b.click()
                except ElementClickInterceptedException:
                    self._wait_for_no_overlay(15)
                    self.driver.execute_script("arguments[0].click();", b)
                return self
        raise AssertionError("Delete menu item not found")

    def confirm_delete(self):
        self.click_element(By.CSS_SELECTOR, 'button[type="submit"]')
        return self

    # ---------------- NEW: explicit dialog close helper ----------------
    def click_dialog_close(self):
        """
        Click the 'X' close button on the currently open Vault item dialog.
        Falls back to _dismiss_dialogs if the button isn’t clickable.
        """
        selectors = [
            "cdk-dialog-container app-vault-item-dialog button[aria-label='Close']",
            "cdk-dialog-container button[aria-label='Close']",
            "cdk-dialog-container button[title='Close']",
            "cdk-dialog-container .dialog-close",
        ]
        for sel in selectors:
            try:
                btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    self._wait_for_no_overlay(2)
                    self.driver.execute_script("arguments[0].click();", btn)
                # ensure the dialog actually closed
                self._wait_for_no_overlay(5)
                return self
            except Exception:
                continue
        # last resort
        self._dismiss_dialogs(timeout=5)
        return self

    # ---------------- NEW: click the 'Edit' button in the dialog footer ----------------
    def click_edit(self):
        """
        Click the Edit button in the footer of the open 'View Login' dialog.
        Uses robust XPath that matches a button whose visible text is 'Edit'.
        """
        xpath = "//cdk-dialog-container//footer//button[.//span[normalize-space(text())='Edit'] or normalize-space(text())='Edit']"
        btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        except Exception:
            pass
        try:
            btn.click()
        except ElementClickInterceptedException:
            self._wait_for_no_overlay(2)
            self.driver.execute_script("arguments[0].click();", btn)
        return self

    def click_restore_in_view(self):
        """When viewing an item (in Trash), click the Restore button in the footer."""
        xpath = "//cdk-dialog-container//footer//button[.//span[normalize-space()='Restore'] or normalize-space()='Restore']"
        btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        except Exception:
            pass
        try:
            btn.click()
        except ElementClickInterceptedException:
            self._dismiss_backdrops(0.2)
            self.driver.execute_script("arguments[0].click();", btn)
        return self
