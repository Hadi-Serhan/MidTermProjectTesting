from selenium.webdriver.common.by import By

from ui.pages.item_page import ItemPage
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
