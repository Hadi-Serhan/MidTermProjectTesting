# ui/test_login.py
from ui.base_ui_test import BaseVaultwardenTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class VaultwardenLoginUITest(BaseVaultwardenTest):
    def test_login_correct(self):
        self.login("hadixserhan@gmail.com", "Hadi123456789123")
        self.wait.until(EC.title_contains("Vault"))
        self.assertIn("Vault", self.driver.title)
        time.sleep(2)
