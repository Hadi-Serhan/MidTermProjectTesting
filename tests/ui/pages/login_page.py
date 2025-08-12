from selenium.webdriver.common.by import By

from .dashboard_page import DashboardPage
from .base_page import BasePage

class LoginPage(BasePage):
    def enter_email(self, email):
        return self.enter_text(By.ID, "bit-input-0", email)
        

    def click_continue(self):
        return self.click_element(By.CSS_SELECTOR, 'button[buttontype="primary"]')

    def enter_password(self, password):
        return self.enter_text(By.CSS_SELECTOR, 'input[formcontrolname="masterPassword"]', password)

    def click_login(self):
        buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[buttontype="primary"]')
        buttons[1].click()
        
        self.wait.until(lambda d: "Vault" in d.title)
        return DashboardPage(self.driver)  # navigate to next page