import atexit
import os
import shutil
import tempfile
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from tests.common.envtools import pick_url, headless_default

class BaseVaultwardenTest(unittest.TestCase):
    def setUp(self):
        headless = headless_default()

        opts = webdriver.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")

        # Use a unique temp profile to avoid "user data dir already in use"
        self._profile_dir = tempfile.mkdtemp(prefix="vw_chrome_")
        opts.add_argument(f"--user-data-dir={self._profile_dir}")

        # Server-friendly flags
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1280,900")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts
        )
        self.wait = WebDriverWait(self.driver, 30)

        base_url = pick_url()
        self.driver.get(base_url)

        atexit.register(lambda: shutil.rmtree(self._profile_dir, ignore_errors=True))

    def tearDown(self):
        try:
            self.driver.quit()
        finally:
            shutil.rmtree(self._profile_dir, ignore_errors=True)
            

    def login(self, email, password):
        self.wait.until(EC.presence_of_element_located((By.ID, "bit-input-0"))).send_keys(email)
        self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[buttontype="primary"]'))).click()
        
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[formcontrolname="masterPassword"]'))).send_keys(password)
        
        self.driver.find_elements(By.CSS_SELECTOR, 'button[buttontype="primary"]')[1].click()