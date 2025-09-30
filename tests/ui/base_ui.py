# tests/ui/base_ui.py
import atexit
import os
import shutil
import tempfile
import unittest
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from tests.common.envtools import headless_default, pick_url


class BaseVaultwardenTest(unittest.TestCase):
    def setUp(self):
        headless = headless_default()
        opts = webdriver.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")

        # Disable Chrome password manager + leak detection popups
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "autofill.profile_enabled": False,
            "autofill.credit_card_enabled": False,
            "credentials_enable_autosignin": False,
            "profile.password_manager_leak_detection": False,
            "password_manager_leak_detection": False,
        }
        opts.add_experimental_option("prefs", prefs)
        opts.add_argument("--disable-save-password-bubble")
        opts.add_argument("--disable-extensions")  # cuts off GPM UI in many builds
        opts.add_argument("--disable-component-extensions-with-background-pages")
        opts.add_argument(
            "--disable-features=PasswordLeakDetection,PasswordReuseDetection,PasswordManagerOnboarding"
        )

        # Make ngrok skip the abuse splash (works in CI and locally)
        is_ci = (
            os.getenv("GITHUB_ACTIONS", "").lower() == "true"
            or os.getenv("CI", "").lower() == "true"
        )
        ua = "vw-ci-bot/1.0" if is_ci else "vw-local-tester/1.0"
        opts.add_argument(f"--user-agent={ua}")

        # unique Chrome profile to avoid lock issues
        self._profile_dir = tempfile.mkdtemp(prefix="vw_chrome_")
        opts.add_argument(f"--user-data-dir={self._profile_dir}")

        # server-friendly flags
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1280,900")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts
        )
        self.wait = WebDriverWait(self.driver, 30)

        # Start at login
        base_url = pick_url().rstrip("/")
        self.base_url = base_url
        login_url = f"{base_url}/#/login"
        self.driver.get(login_url)

        # If ngrok splash appears, bypass it once
        self._bypass_ngrok_splash()

        atexit.register(lambda: shutil.rmtree(self._profile_dir, ignore_errors=True))

    def tearDown(self):
        try:
            self.driver.quit()
        finally:
            shutil.rmtree(self._profile_dir, ignore_errors=True)

    def _bypass_ngrok_splash(self):
        try:
            cur = self.driver.current_url
            host = urlparse(cur).netloc
            if "ngrok-free.app" in host:
                # Try query param trick (some edges honor it)
                if "ngrok-skip-browser-warning" not in cur:
                    u = urlparse(cur)
                    q = dict(parse_qsl(u.query))
                    q["ngrok-skip-browser-warning"] = "true"
                    self.driver.get(urlunparse(u._replace(query=urlencode(q))))
                # If still showing splash, click "Visit Site"
                if (
                    "Visit Site" in self.driver.page_source
                    or "ngrok" in (self.driver.title or "").lower()
                ):
                    btn = self.wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "//*[self::a or self::button][normalize-space()='Visit Site']",
                            )
                        )
                    )
                    btn.click()
        except Exception:
            # Don’t block tests if bypass fails
            pass

    def debug_dump(self, name: str = "login_timeout"):
        try:
            os.makedirs("reports", exist_ok=True)
            self.driver.save_screenshot(f"reports/{name}.png")
            with open(f"reports/{name}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        except Exception:
            pass
