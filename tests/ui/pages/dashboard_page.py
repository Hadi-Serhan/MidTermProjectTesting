# tests/ui/pages/dashboard_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .item_page import ItemPage
from .base_page import BasePage

class DashboardPage(BasePage):
    def click_new_button(self):
        return self.click_element(By.ID, 'newItemDropdown')

    def select_menu_item(self, item_text):
        self.wait_for_element(By.CSS_SELECTOR, 'button[role="menuitem"]')
        items = self.driver.find_elements(By.CSS_SELECTOR, 'button[role="menuitem"]')
        for it in items:
            if item_text.lower() in it.text.lower():
                it.click()
                break
        return ItemPage(self.driver)

    # NEW: open the item by name (click the name button) -> returns ItemPage (View dialog)
    def open_item_by_name(self, item_name: str) -> ItemPage:
        self._dismiss_backdrops(0.2)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody")))
        row_xpath = (
            "//table//tbody//tr[@bitrow]"
            f"[.//button[@bitlink and normalize-space()='{item_name}']]"
        )
        row = self.wait.until(EC.visibility_of_element_located((By.XPATH, row_xpath)))
        name_btn = row.find_element(By.XPATH, ".//button[@bitlink]")
        try:
            name_btn.click()
        except Exception:
            self._dismiss_backdrops(0.2)
            self.driver.execute_script("arguments[0].click();", name_btn)
        return ItemPage(self.driver)

    # NEW: open options menu for an item (⋮) -> returns ItemPage so you can .click_delete()
    def open_item_options_for(self, item_name: str) -> ItemPage:
        self._dismiss_backdrops(0.2)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody")))
        row_xpath = (
            "//table//tbody//tr[@bitrow]"
            "[.//button[@bitlink and contains(@title,'Edit item') "
            f"and normalize-space()='{item_name}']]"
        )
        row = self.wait.until(EC.visibility_of_element_located((By.XPATH, row_xpath)))
        try:
            btn = row.find_element(By.XPATH, ".//button[@aria-label='Options']")
        except Exception:
            btn = row.find_element(
                By.XPATH,
                ".//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'options')]"
            )
        try:
            btn.click()
        except Exception:
            self._dismiss_backdrops(0.2)
            self.driver.execute_script("arguments[0].click();", btn)
        return ItemPage(self.driver)
