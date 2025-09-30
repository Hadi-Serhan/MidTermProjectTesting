# tests/ui/pages/base_page.py
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

    # ---------------- overlays / dialogs ----------------
    def _wait_for_no_overlay(self, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-backdrop-showing")
                )
            )
        except TimeoutException:
            pass

    def _dismiss_dialogs(self, timeout=10):
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

        try:
            self.driver.switch_to.active_element.send_keys("\ue00c")
        except Exception:
            pass

        self._wait_for_no_overlay(timeout)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".cdk-overlay-pane"))
            )
        except TimeoutException:
            pass

    def _dismiss_backdrops(self, timeout=0.5):
        try:
            for bd in self.driver.find_elements(
                By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-backdrop-showing"
            ):
                try:
                    bd.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", bd)
            if timeout:
                WebDriverWait(self.driver, timeout).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-backdrop-showing")
                    )
                )
        except Exception:
            pass

    # ---------------- toast helpers ----------------
    def _find_toast_messages(self):
        """
        Return list of (toast_element, message_text) for any *visible* toast-ish node.
        Handles:
          1) ngx-toastr under [toastcontainer] #toast-container …
          2) polite live-region container: [role="status"] #toast-container …
          3) visible nodes with classes containing 'toast'/'notification'/'alert'
        Always reads text via innerText (fallback to .text).
        """
        results = []
        containers = []

        # Known containers
        try:
            containers += self.driver.find_elements(
                By.CSS_SELECTOR, "[toastcontainer] #toast-container.toast-container"
            )
            containers += self.driver.find_elements(
                By.CSS_SELECTOR, "#toast-container.toast-container"
            )
            containers += self.driver.find_elements(
                By.CSS_SELECTOR, '[role="status"] #toast-container.toast-container'
            )
        except Exception:
            pass

        # If no explicit container found, still scan page for visible toast-ish nodes.
        def _gather_in(container_or_root):
            sels = [
                ".ngx-toastr",
                ".toast",
                "[class*='toast']",
                "[class*='notification']",
                "[class*='alert']",
            ]
            found = []
            for sel in sels:
                try:
                    found += container_or_root.find_elements(By.CSS_SELECTOR, sel)
                except Exception:
                    pass
            return found

        # Search inside containers first
        for cont in containers:
            try:
                if not cont.is_displayed():
                    continue
            except Exception:
                continue
            candidates = _gather_in(cont)
            for node in candidates:
                try:
                    if not node.is_displayed():
                        continue
                except Exception:
                    pass
                # prefer a dedicated message child if present
                msg_text = ""
                try:
                    msg_els = node.find_elements(By.CSS_SELECTOR, ".toast-message, .message")
                    if msg_els:
                        msg_text = (self.driver.execute_script(
                            "return arguments[0].innerText || '';", msg_els[-1]
                        ) or "").strip()
                except Exception:
                    pass
                if not msg_text:
                    # fall back to the whole node's innerText
                    try:
                        msg_text = (self.driver.execute_script(
                            "return arguments[0].innerText || '';", node
                        ) or "").strip()
                    except Exception:
                        msg_text = (node.text or "").strip()
                if msg_text:
                    results.append((node, msg_text))

        # If still nothing, do a page-wide sweep
        if not results:
            try:
                roots = [self.driver.find_element(By.TAG_NAME, "body")]
            except Exception:
                roots = []
            for root in roots:
                for node in _gather_in(root):
                    try:
                        if not node.is_displayed():
                            continue
                    except Exception:
                        pass
                    try:
                        msg_text = (self.driver.execute_script(
                            "return arguments[0].innerText || '';", node
                        ) or "").strip()
                    except Exception:
                        msg_text = (node.text or "").strip()
                    if msg_text:
                        results.append((node, msg_text))

        return results

    def _dismiss_toast_element(self, toast_el):
        if not toast_el:
            return
        # Prefer explicit close buttons
        try:
            for btn in toast_el.find_elements(
                By.CSS_SELECTOR,
                ".toast-close-button, button[aria-label='Close'], button[title='Close']",
            ):
                if btn.is_displayed():
                    try:
                        btn.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", btn)
                    return
        except Exception:
            pass
        # Otherwise click/tap the toast
        try:
            toast_el.click()
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", toast_el)
            except Exception:
                pass

    def assert_toast_message(self, expected_text: str = None, timeout: int = 10,
                             any_of: list | None = None, dismiss: bool = True):
        """
        Wait for a toast-ish node to show non-empty text, assert it matches expected_text (or any_of),
        then optionally dismiss it.
        """
        wanted = [expected_text] if expected_text else []
        if any_of:
            wanted.extend([w for w in any_of if w])
        wanted = [w for w in wanted if w]

        # small grace so UI can render the toast after a click/save
        self.driver.execute_script("return new Promise(r=>setTimeout(r, 120));")

        deadline = self.driver.execute_script("return Date.now() + arguments[0]*1000;", timeout)
        last_text = ""
        while self.driver.execute_script("return Date.now();") < deadline:
            pairs = self._find_toast_messages()
            if pairs:
                toast_el, text = pairs[-1]
                last_text = text
                if not wanted or any(w.lower() in text.lower() for w in wanted):
                    if dismiss:
                        self._dismiss_toast_element(toast_el)
                    return self
            self.driver.execute_script("return new Promise(r=>setTimeout(r, 120));")

        if last_text:
            raise AssertionError(
                f"Toast text did not match within {timeout}s. Saw: {last_text!r} "
                f"Wanted: {wanted or '[any non-empty]'}"
            )
        raise AssertionError("No toast text found within timeout in known containers/selectors.")

    # ---------------- public API ----------------
    def wait_for_element(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click_element(self, by, value):
        el = self.wait.until(EC.presence_of_element_located((by, value)))
        self._wait_for_no_overlay(2)
        self.wait.until(EC.element_to_be_clickable((by, value)))
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass
        try:
            el.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            self._dismiss_backdrops(timeout=0.2)
            try:
                self.driver.execute_script("arguments[0].click();", el)
            except Exception:
                el = self.driver.find_element(by, value)
                self.driver.execute_script("arguments[0].click();", el)
        return self

    def enter_text(self, by, value, text):
        element = self.wait_for_element(by, value)
        element.send_keys(text)
        return self
