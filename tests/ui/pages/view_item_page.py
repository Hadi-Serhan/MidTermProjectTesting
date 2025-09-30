# tests/ui/pages/view_item_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage
from .item_page import ItemPage


class ViewItemPage(BasePage):
    def assert_view_open_for(self, item_name: str):
        candidates = [
            (By.CSS_SELECTOR, ".item-header h2, .item-header h3, .item-header .title"),
            (By.XPATH, "//div[contains(@class,'item-header')]//*[self::h2 or self::h3 or self::strong]"),
            (By.XPATH, "//div[contains(@class,'item-view') or contains(@class,'dialog')]//*[self::h2 or self::h3 or self::strong]"),
        ]
        title_text = ""
        for by, sel in candidates:
            try:
                el = self.wait.until(EC.presence_of_element_located((by, sel)))
                title_text = (el.text or "").strip()
                if title_text:
                    break
            except Exception:
                continue
        if title_text and item_name.lower() not in title_text.lower():
            raise AssertionError(f"Expected view of '{item_name}', saw title '{title_text}'")
        return self

    def _ensure_edit_mode(self):
        """
        After clicking Edit, wait until the edit UI is present:
        - Save button is visible (it exists but starts hidden), OR
        - any edit field (e.g., formcontrolname='name') is interactable.
        """
        # 1) Save button becomes visible (it exists but starts hidden)
        try:
            save_btn = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button[form='cipherForm'][type='submit']")
            ))
            self.wait.until(lambda d: save_btn.is_displayed())
            return
        except Exception:
            pass

        # 2) Fallback: a known edit input is present and enabled
        try:
            name_input = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[formcontrolname='name']")
            ))
            self.wait.until(lambda d: name_input.is_enabled())
            return
        except Exception:
            pass

        raise AssertionError("Edit mode did not appear (Save button/input not visible).")

    def _js_click_edit_in_dialog(self) -> bool:
        """
        Use JS to find and click the Edit button inside the ACTIVE cdk-dialog-container.
        Returns True if it believes it clicked something.
        """
        script = r"""
        try {
          // Find the top-most visible dialog container
          const dialogs = Array.from(document.querySelectorAll('cdk-dialog-container'));
          const vis = dialogs.filter(d => {
            const r = d.getBoundingClientRect();
            const style = window.getComputedStyle(d);
            return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
          });
          if (vis.length === 0) return false;

          // Prefer the last one (usually the top-most)
          const dlg = vis[vis.length - 1];

          // Look in footer for an Edit button
          const footer = dlg.querySelector('app-vault-item-dialog bit-dialog section footer') || dlg.querySelector('section footer');
          if (!footer) return false;

          // Candidates: any button in footer
          let buttons = Array.from(footer.querySelectorAll('button'));
          // Filter visible
          buttons = buttons.filter(b => {
            const r = b.getBoundingClientRect();
            const cs = window.getComputedStyle(b);
            return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
          });
          if (buttons.length === 0) return false;

          // Try to find one whose text includes 'Edit'
          const byText = buttons.find(b => (b.innerText || '').trim().toLowerCase().includes('edit'));
          const target = byText || buttons[0];

          // Scroll into view
          try { target.scrollIntoView({block: 'center'}); } catch (e) {}

          // Try normal click
          try { target.click(); } catch (e) {}

          // If it didn't change focus, synthesize a mouse click (more "real")
          try {
            const ev = new MouseEvent('click', {view: window, bubbles: true, cancelable: true});
            target.dispatchEvent(ev);
          } catch (e) {}

          return true;
        } catch(e) {
          return false;
        }
        """
        try:
            return bool(self.driver.execute_script(script))
        except Exception:
            return False

    def click_edit(self) -> ItemPage:
        """
        Click the 'Edit' button inside the active CDK dialog using several strategies:
          1) Strict relative lookup within the dialog footer (text='Edit').
          2) Absolute XPath fallback (from your inspected DOM).
          3) JS-driven click that finds and dispatches a synthetic click.
        Then wait for edit mode (Save visible or inputs enabled).
        """
        self._kill_blockers()

        # Ensure dialog is up
        dialog = self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "cdk-dialog-container app-vault-item-dialog bit-dialog")
        ))

        # Strategy 1: strict within-dialog locator
        edit_btn = None
        for loc in [
            (By.XPATH, ".//section//footer//button[.//span[normalize-space()='Edit'] or normalize-space()='Edit']"),
            (By.CSS_SELECTOR, "section footer button[buttontype='primary'][type='button']"),
        ]:
            try:
                candidates = dialog.find_elements(*loc)
                candidates = [c for c in candidates if c.is_displayed()]
                if candidates:
                    edit_btn = candidates[0]
                    break
            except Exception:
                continue

        if edit_btn:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", edit_btn)
            except Exception:
                pass
            self._kill_blockers()
            try:
                self.wait.until(EC.element_to_be_clickable(edit_btn))
            except Exception:
                pass
            try:
                edit_btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", edit_btn)
        else:
            # Strategy 2: your absolute XPath as a fallback
            try:
                abs_btn = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/cdk-dialog-container/app-vault-item-dialog/bit-dialog/section/footer/button[1]")
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", abs_btn)
                except Exception:
                    pass
                self._kill_blockers()
                try:
                    abs_btn.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", abs_btn)
            except Exception:
                # Strategy 3: pure JS click in dialog footer
                if not self._js_click_edit_in_dialog():
                    raise AssertionError("Edit button not found/clickable in dialog")

        # Wait for edit UI
        self._ensure_edit_mode()
        return ItemPage(self.driver)
