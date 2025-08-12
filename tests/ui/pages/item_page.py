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
        save_button.click()
        return self
    
    def close_popup(self):
        # Click the close button
        self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Close']"))
        ).click()
        return self 

    def open_item_options_for(self, item_name):
        # Wait until the table body and at least one row exist
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody")))
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr[bitrow]")))

        # Find the row that contains the name button with the exact visible text
        row_xpath = (
            "//table//tbody//tr[@bitrow]"
            "[.//button[@bitlink and contains(@title,'Edit item') "
            f"and normalize-space()='{item_name}']]"
        )
        row = self.wait.until(EC.visibility_of_element_located((By.XPATH, row_xpath)))

        # Scroll into view to avoid intercepted click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'})", row)

        # Click that row's Options button (independent of column order)
        try:
            btn = row.find_element(By.XPATH, ".//button[@aria-label='Options']")
        except Exception:
            btn = row.find_element(
                By.XPATH,
                ".//button[contains(translate(@aria-label,"
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'options')]"
            )
        btn.click()
        return self

    def click_delete(self):
        items = self.driver.find_elements(By.CSS_SELECTOR, 'button[role="menuitem"]')
        for b in items:
            if "delete" in b.text.lower():
                b.click()
                return self
        raise AssertionError("Delete menu item not found")

    def confirm_delete(self):
        # confirmation dialog primary button (submit)
        self.click_element(By.CSS_SELECTOR, 'button[type="submit"]')
        return self
