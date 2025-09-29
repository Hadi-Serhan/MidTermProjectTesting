from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
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
            self._dismiss_backdrops(timeout=0.2)
            self.driver.execute_script("arguments[0].click();", save_button)
        return self

    def close_popup(self):
        self._dismiss_backdrops(timeout=0.2)
        return self

    def open_item_options_for(self, item_name):
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
                ".//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'options')]"
            )

        try:
            btn.click()
        except ElementClickInterceptedException:
            self._dismiss_backdrops(timeout=0.2)
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
                    self._dismiss_backdrops(timeout=0.2)
                    self.driver.execute_script("arguments[0].click();", b)
                return self
        raise AssertionError("Delete menu item not found")

    def confirm_delete(self):
        try:
            self.click_element(By.CSS_SELECTOR, 'button[type="submit"]')
        except ElementClickInterceptedException:
            self._dismiss_backdrops(timeout=0.2)
            self.click_element(By.CSS_SELECTOR, 'button[type="submit"]')
        return self
