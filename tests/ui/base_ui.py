import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class BaseVaultwardenTest(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.wait = WebDriverWait(self.driver, 300)
        self.driver.get("http://localhost:3000")

    def tearDown(self):
        self.driver.quit()

    def login(self, email, password):
        self.wait.until(EC.presence_of_element_located((By.ID, "bit-input-0"))).send_keys(email)
        self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[buttontype="primary"]'))).click()
        
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[formcontrolname="masterPassword"]'))).send_keys(password)
        
        self.driver.find_elements(By.CSS_SELECTOR, 'button[buttontype="primary"]')[1].click()