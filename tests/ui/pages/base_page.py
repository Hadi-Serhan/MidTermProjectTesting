from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

    # ----- internals: helpers for overlays/dialogs -----
    def _wait_for_no_overlay(self, timeout=10):
        """Wait until Angular CDK overlay/backdrop is gone so clicks aren't intercepted."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-backdrop-showing")
                )
            )
        except TimeoutException:
            pass  # we'll JS-click as a fallback

    def _dismiss_dialogs(self, timeout=10):
        """
        Aggressively close any open Vault item dialog:
        1) click a close button (several selectors),
        2) click the backdrop,
        3) send Escape,
        then wait until overlays are gone.
        """
        # 1) Try close buttons
        close_selectors = [
            "button[aria-label='Close']",
            "button[title='Close']",
            "button[aria-label='Close dialog']",
            ".dialog-close",
        ]
        for sel in close_selectors:
            try:
                btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", btn)
                break
            except Exception:
                continue

        # 2) If still there, click the backdrop
        try:
            backdrop = WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-backdrop-showing")
                )
            )
            try:
                backdrop.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", backdrop)
        except Exception:
            pass

        # 3) As a last resort, send ESC
        try:
            self.driver.switch_to.active_element.send_keys("\ue00c")  # Keys.ESCAPE
        except Exception:
            pass

        # Wait until panes/backdrops are gone
        self._wait_for_no_overlay(timeout)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane"))
            )
        except TimeoutException:
            pass

    # ----- your existing public API (names unchanged) -----
    def wait_for_element(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click_element(self, by, value):
        """Robust click with overlay wait + JS fallback."""
        el = self.wait.until(EC.presence_of_element_located((by, value)))
        self._wait_for_no_overlay(10)
        self.wait.until(EC.element_to_be_clickable((by, value)))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass
        try:
            el.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            self._wait_for_no_overlay(10)
            el = self.driver.find_element(by, value)
            self.driver.execute_script("arguments[0].click();", el)
        return self

    def enter_text(self, by, value, text):
        element = self.wait_for_element(by, value)
        element.send_keys(text)
        return self

    def assert_toast_message(self, expected_text, timeout=5):
        try:
            # Support multiple snackbar/toast implementations
            selectors = [
                '[data-testid="toast-message"]',
                '.toast-message',
                '.simple-snack-bar',
                '.snackbar',
                '.mat-mdc-snack-bar-label',
            ]
            def toast_with_text(driver):
                for sel in selectors:
                    try:
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        if el.text.strip():
                            return el
                    except Exception:
                        continue
                return False

            toast = WebDriverWait(self.driver, timeout).until(toast_with_text)
            actual_text = toast.text.strip()
            assert expected_text.lower() in actual_text.lower(), \
                f"Expected toast '{expected_text}', got '{actual_text}'"
            # let any backdrops fade before the next action
            self._wait_for_no_overlay(10)
            return self
        except TimeoutException:
            raise AssertionError(f"Toast with text '{expected_text}' not found within {timeout} seconds.")
