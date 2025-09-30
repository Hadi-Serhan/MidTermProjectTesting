# tests/ui/pages/dashboard_page.py
import time

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage
from .item_page import ItemPage


class DashboardPage(BasePage):
    # ---- tiny local sleep (no BasePage dependency) ----
    def _tiny_sleep(self, ms: int = 150):
        try:
            self.driver.execute_script("return new Promise(r => setTimeout(r, arguments[0]));", ms)
        except Exception:
            time.sleep(ms / 1000.0)

    # ---- generic retry for stale DOM ----
    def _retry(self, fn, timeout=8.0, pause=0.2):
        end = time.time() + timeout
        last_err = None
        while time.time() < end:
            try:
                return fn()
            except StaleElementReferenceException as e:
                last_err = e
                self._tiny_sleep(int(pause * 1000))
            except Exception as e:
                # minor settle and retry — DOM can still be repainting
                last_err = e
                self._tiny_sleep(int(pause * 1000))
        if last_err:
            raise last_err
        raise AssertionError("Retry timed out")

    # ---------- create new ----------
    def click_new_button(self):
        return self.click_element(By.ID, "newItemDropdown")

    def select_menu_item(self, item_text):
        self.wait_for_element(By.CSS_SELECTOR, "button[role='menuitem']")
        items = self.driver.find_elements(By.CSS_SELECTOR, "button[role='menuitem']")
        for it in items:
            if item_text.lower() in (it.text or "").lower():
                try:
                    it.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", it)
                break
        return ItemPage(self.driver)

    # ---------- robust row location usable in main list *and* Trash ----------
    def _row_by_name_xpath(self, name):
        return (
            "//table//tbody//tr[@bitrow]"
            f"[.//button[(contains(@class,'tw-font-semibold') or @bitlink) "
            f"and normalize-space()='{name}']]"
        )

    def _row_by_name(self, name):
        xpath = self._row_by_name_xpath(name)

        def locate():
            self._dismiss_backdrops(0.1)
            self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            row = self.driver.find_element(By.XPATH, xpath)
            _ = row.is_displayed()  # forces refetch if stale
            return row

        return self._retry(locate, timeout=8.0, pause=0.2)

    # ---------- open item name (to View dialog) ----------
    def open_item_by_name(self, item_name: str) -> ItemPage:
        self._dismiss_backdrops(0.2)
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//table|//button[contains(.,'New item')]"))
        )
        row = self._row_by_name(item_name)

        def click_name():
            try:
                btn = row.find_element(
                    By.XPATH,
                    ".//button[(contains(@class,'tw-font-semibold') or @bitlink)]",
                )
            except Exception:
                fresh_row = self._row_by_name(item_name)
                btn = fresh_row.find_element(
                    By.XPATH, ".//button[(contains(@class,'tw-font-semibold') or @bitlink)]"
                )

            try:
                btn.click()
            except Exception:
                self._dismiss_backdrops(0.2)
                self.driver.execute_script("arguments[0].click();", btn)

        self._retry(click_name, timeout=6.0, pause=0.2)
        return ItemPage(self.driver)

    # ---------- open ⋮ options menu on a row ----------
    def open_item_options_for(self, item_name: str) -> ItemPage:
        self._dismiss_backdrops(0.2)
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//table|//button[contains(.,'New item')]"))
        )

        row = self._row_by_name(item_name)

        def click_options():
            try:
                btn = row.find_element(
                    By.XPATH, ".//button[@aria-label='Options' or @title='Options']"
                )
            except Exception:
                fresh_row = self._row_by_name(item_name)
                try:
                    btn = fresh_row.find_element(
                        By.XPATH, ".//button[@aria-label='Options' or @title='Options']"
                    )
                except Exception:
                    btn = fresh_row.find_element(
                        By.XPATH,
                        ".//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'options')]",
                    )

            try:
                btn.click()
            except ElementClickInterceptedException:
                self._dismiss_backdrops(0.2)
                self.driver.execute_script("arguments[0].click();", btn)

        self._retry(click_options, timeout=6.0, pause=0.2)
        return ItemPage(self.driver)

    # ---------- left sidebar navigation ----------
    def go_to_trash(self):
        """Click the 'Trash' filter in the left sidebar."""
        self._dismiss_backdrops(0.2)
        # your inspected selector first
        try:
            self.click_element(By.CSS_SELECTOR, "button.filter-button[title='Filter: Trash']")
        except Exception:
            self.click_element(
                By.XPATH,
                "//button[contains(@class,'filter-button')][contains(normalize-space(.),'Trash')]",
            )

        # wait for trash view & allow a short repaint settle to avoid stale nodes
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[@placeholder='Search trash' or contains(@placeholder,'trash')]",
                    )
                )
            )
        except TimeoutException:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table|//div[contains(.,'There are no items to list.')]")
                )
            )

        self._tiny_sleep(200)
        return self

    def go_to_all_items(self):
        """Click the 'All items' filter in the left sidebar."""
        self._dismiss_backdrops(0.2)
        try:
            self.click_element(By.CSS_SELECTOR, "button.filter-button[title='Filter: All items']")
        except Exception:
            self.click_element(
                By.XPATH,
                "//button[contains(@class,'filter-button')][contains(normalize-space(.),'All items')]",
            )

        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//table|//button[contains(.,'New item')]"))
        )
        self._tiny_sleep(150)
        return self

    # ---------- assertions ----------
    def assert_row_present(self, item_name: str):
        _ = self._row_by_name(item_name)
        return self

    def assert_row_absent(self, item_name: str, timeout: int = 5):
        xpath = self._row_by_name_xpath(item_name)
        try:
            from selenium.webdriver.support.ui import WebDriverWait

            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return self
        except TimeoutException:
            raise AssertionError(f"Row with name '{item_name}' still present after {timeout}s.")

    # ---------- restore action from ⋮ menu (works in Trash) ----------
    def restore_item_from_trash(self, item_name: str):
        """In Trash view, open ⋮ on the row and click 'Restore'."""
        self._dismiss_backdrops(0.2)
        self.assert_row_present(item_name)
        self.open_item_options_for(item_name)

        def click_restore():
            items = self.driver.find_elements(By.CSS_SELECTOR, "button[role='menuitem']")
            for b in items:
                txt = (b.text or "").strip().lower()
                if "restore" in txt:
                    try:
                        b.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", b)
                    return True
            raise StaleElementReferenceException("Restore not found yet")

        self._retry(click_restore, timeout=6.0, pause=0.2)
        return ItemPage(self.driver)
