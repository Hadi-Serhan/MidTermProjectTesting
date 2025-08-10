from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 300)

    def wait_for_element(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click_element(self, by, value):
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        element.click()
        return self

    def enter_text(self, by, value, text):
        element = self.wait_for_element(by, value)
        element.send_keys(text)
        return self

    def assert_toast_message(self, expected_text, timeout=5):
        try:
            toast_locator = (By.CSS_SELECTOR, '[data-testid="toast-message"]')

            # Wait until the toast has non-empty text
            def toast_text_is_present(driver):
                try:
                    el = driver.find_element(*toast_locator)
                    return el if el.text.strip() else False
                except:
                    return False

            toast = WebDriverWait(self.driver, timeout).until(toast_text_is_present)
            actual_text = toast.text.strip()

            assert expected_text.lower() in actual_text.lower(), \
                f"Expected toast '{expected_text}', got '{actual_text}'"
            return self
        except TimeoutException:
            raise AssertionError(f"Toast with text '{expected_text}' not found within {timeout} seconds.")

