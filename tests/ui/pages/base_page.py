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

    # ---------- backdrops only ----------
    def _dismiss_backdrops(self, timeout=0.5):
        """Close ONLY Angular CDK backdrops; do not touch toasts/snackbars."""
        try:
            backdrops = self.driver.find_elements(
                By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-backdrop-showing"
            )
            for bd in backdrops:
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

    # ---------- ngx-toastr helpers ----------
    def _ngx_toast_nodes(self):
        """
        Return list of dicts for each visible ngx-toastr toast:
        { 'container': element, 'toast': element, 'message_el': element_or_None, 'text': str }
        """
        nodes = []
        try:
            # <div toastcontainer><div id="toast-container" class="toast-container">...</div></div>
            containers = []
            containers += self.driver.find_elements(By.CSS_SELECTOR, "[toastcontainer] #toast-container.toast-container")
            containers += self.driver.find_elements(By.CSS_SELECTOR, "#toast-container.toast-container")
            for cont in containers:
                if not getattr(cont, "is_displayed", lambda: False)():
                    continue
                # individual toasts
                toasts = cont.find_elements(By.CSS_SELECTOR, ".ngx-toastr, .toast")
                for t in toasts:
                    if not getattr(t, "is_displayed", lambda: False)():
                        continue
                    msg_el = None
                    text = ""
                    try:
                        els = t.find_elements(By.CSS_SELECTOR, ".toast-message, .message")
                        if els:
                            msg_el = els[-1]
                            text = (msg_el.text or "").strip()
                            if not text:
                                text = (self.driver.execute_script("return arguments[0].innerText || '';", msg_el) or "").strip()
                        if not text:
                            text = (t.text or "").strip()
                            if not text:
                                text = (self.driver.execute_script("return arguments[0].innerText || '';", t) or "").strip()
                    except Exception:
                        pass
                    nodes.append({"container": cont, "toast": t, "message_el": msg_el, "text": text})
        except Exception:
            pass
        return nodes

    def _tap_or_close_ngx_toast(self, toast_el, polite_timeout=0.8):
        """Dismiss a single ngx-toastr: prefer close button; otherwise tap the toast (tapToDismiss)."""
        if toast_el is None:
            return
        closed = False
        for sel in [".toast-close-button", "button[aria-label='Close']", "button[title='Close']", "[data-dismiss]"]:
            try:
                for btn in toast_el.find_elements(By.CSS_SELECTOR, sel):
                    if btn.is_displayed():
                        try:
                            btn.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", btn)
                        closed = True
                        break
                if closed:
                    break
            except Exception:
                continue

        if not closed:
            # tap the toast itself (default ngx-toastr behavior)
            try:
                toast_el.click()
                closed = True
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", toast_el)
                    closed = True
                except Exception:
                    pass

        if not closed:
            # last resort: ESC
            try:
                self.driver.switch_to.active_element.send_keys("\ue00c")
            except Exception:
                pass

        if polite_timeout:
            try:
                WebDriverWait(self.driver, polite_timeout).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ngx-toastr, .toast"))
                )
            except Exception:
                pass

    def close_all_toasts(self):
        """Utility you can call to clear any lingering toasts explicitly."""
        try:
            for node in self._ngx_toast_nodes():
                self._tap_or_close_ngx_toast(node.get("toast"), polite_timeout=0.2)
        except Exception:
            pass

    # ---------- fallback (aria-live / MDC) ----------
    def _collect_live_region_nodes(self):
        js = """
            (function(){
              const sels = [
                '.cdk-global-overlay-container .mat-mdc-snack-bar-container .mat-mdc-snack-bar-label',
                '.cdk-global-overlay-container .mat-mdc-snack-bar-container .mdc-snackbar__label',
                '.cdk-global-overlay-container .mat-snack-bar-container',
                '.cdk-global-overlay-container .simple-snack-bar',
                '.cdk-live-announcer-element',
                '[role="status"]',
                '[aria-live="polite"]',
                '[aria-live="assertive"]',
                '[aria-live]'
              ];
              const seen = new Set();
              const nodes = [];
              for (const sel of sels) {
                const found = document.querySelectorAll(sel);
                for (const n of found) {
                  if (seen.has(n)) continue;
                  seen.add(n);
                  let txt = '';
                  try { txt = (n.innerText || '').trim(); } catch(e) {}
                  if (!txt) { try { txt = (n.textContent || '').trim(); } catch(e) {} }
                  const vis = !!(n.offsetParent || getComputedStyle(n).position === 'fixed');
                  nodes.push({sel, text: txt, visible: vis});
                }
              }
              return nodes;
            })();
        """
        try:
            nodes = self.driver.execute_script(js)
            return nodes if isinstance(nodes, list) else []
        except Exception:
            return []

    # ---------- public API ----------
    def wait_for_element(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click_element(self, by, value):
        el = self.wait.until(EC.presence_of_element_located((by, value)))
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

    def assert_toast_message(self, expected_text: str = None, timeout: int = 12, any_of: list[str] | None = None):
        """
        Wait for a non-empty toast (ngx-toastr preferred; aria-live/MDC as fallback),
        assert it contains expected_text (or any_of), then DISMISS that toast.
        """
        wanted = [expected_text] if expected_text else []
        if any_of:
            wanted.extend([w for w in any_of if w])
        wanted = [w for w in wanted if w]

        end_ms = self._now_ms() + timeout * 1000
        last_txt = ""
        last_dbg = ""

        while self._now_ms() < end_ms:
            # 1) ngx-toastr first
            ngx_nodes = self._ngx_toast_nodes()
            nonempty = [n for n in ngx_nodes if (n.get("text") or "").strip()]
            if nonempty:
                latest = nonempty[-1]
                txt = latest["text"].strip()
                last_txt, last_dbg = txt, f"ngx-toastr: {txt!r}"
                if not wanted or any(w.lower() in txt.lower() for w in wanted):
                    self._tap_or_close_ngx_toast(latest.get("toast"))
                    return self

            # 2) fallback to aria-live/MDC
            live_nodes = self._collect_live_region_nodes()
            live_nonempty = [n for n in live_nodes if (n.get("text") or "").strip()]
            if live_nonempty:
                txt = live_nonempty[-1]["text"].strip()
                last_txt = txt
                last_dbg = "aria-live/MDC candidates:\n" + "\n".join(
                    f"[{n.get('sel')}] vis={n.get('visible')} text={n.get('text')!r}"
                    for n in live_nonempty[-5:]
                )
                if not wanted or any(w.lower() in txt.lower() for w in wanted):
                    # Best effort: also clear any visible ngx toast if present
                    if ngx_nodes:
                        self._tap_or_close_ngx_toast(ngx_nodes[-1].get("toast"))
                    return self

            self._sleep_ms(120)

        if last_txt:
            raise AssertionError(
                f"Toast text did not match within {timeout}s. Saw: {last_txt!r}\n\nLast seen:\n{last_dbg}"
            )
        raise AssertionError(
            f"Toast text stayed empty within {timeout}s. No ngx-toastr or aria-live text detected."
        )

    # --- tiny utils ---
    def _now_ms(self):
        return self.driver.execute_script("return Date.now();")

    def _sleep_ms(self, ms: int):
        self.driver.execute_script("return new Promise(r => setTimeout(r, arguments[0]));", ms)
