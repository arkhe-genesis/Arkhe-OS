from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:3000")

        # Wait for app
        page.wait_for_selector("text=Command Center", timeout=60000)
        page.screenshot(path="verification/debug_step_1_loaded.png")

        # Click Wetware
        page.click('button:has-text("Wetware")')
        time.sleep(2)
        page.screenshot(path="verification/debug_step_2_wetware.png")

        # Locate Corvo Noir button
        corvo_btn = page.locator('button:has-text("CORVO NOIR OS (Dashboard)")')
        if corvo_btn.count() > 0:
            print("Button found")
            # JS Click to avoid animation issues
            page.evaluate("(el) => el.click()", corvo_btn.element_handle())
            time.sleep(5)
            page.screenshot(path="verification/debug_step_3_after_click.png")
        else:
            print("Button NOT found")

        browser.close()

if __name__ == "__main__":
    run()
