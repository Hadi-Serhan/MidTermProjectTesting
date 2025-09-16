# tests/ui/base_ui.py
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

        # Always start on the login route (modern web vault)
        base_url = pick_url().rstrip("/")
        self.base_url = base_url
        self.driver.get(f"{base_url}/#/login")

        atexit.register(lambda: shutil.rmtree(self._profile_dir, ignore_errors=True))

    def tearDown(self):
        try:
            self.driver.quit()
        finally:
            shutil.rmtree(self._profile_dir, ignore_errors=True)

    def debug_dump(self, name: str = "login_timeout"):
        """Save a screenshot and HTML to ./reports for CI artifacts."""
        try:
            os.makedirs("reports", exist_ok=True)
            self.driver.save_screenshot(f"reports/{name}.png")
            with open(f"reports/{name}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        except Exception:
            pass

    def login(self, email, password):
        """Robust login using stable selectors."""
        try:
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
            ).send_keys(email)

            self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            ).click()

            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
            ).send_keys(password)

            self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            ).click()

            # Consider login successful when the vault/home is visible
            self.wait.until(
                lambda d: "Vault" in (d.title or "") or
                          d.find_elements(By.CSS_SELECTOR, '[data-testid="tab-vault"], [data-testid="tab-all-items"]')
            )
        except Exception:
            self.debug_dump()
            raise
