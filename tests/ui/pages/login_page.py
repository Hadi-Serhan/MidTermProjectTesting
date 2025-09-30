# tests/ui/pages/login_page.py
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from .base_page import BasePage
from .dashboard_page import DashboardPage


class LoginPage(BasePage):
    def enter_email(self, email):
        try:
            return self.enter_text(By.ID, "bit-input-0", email)
        except TimeoutException:
            return self.enter_text(By.CSS_SELECTOR, 'input[type="email"]', email)

    def click_continue(self):
        return self.click_element(By.CSS_SELECTOR, 'button[buttontype="primary"]')

    def enter_password(self, password):
        return self.enter_text(By.CSS_SELECTOR, 'input[formcontrolname="masterPassword"]', password)

    def click_login(self):
        buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[buttontype="primary"]')
        buttons[1].click()

        self.wait.until(lambda d: "Vault" in d.title)
        return DashboardPage(self.driver)  # navigate to next page
