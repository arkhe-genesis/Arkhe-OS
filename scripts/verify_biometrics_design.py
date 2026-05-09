from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:3000")

        # Wait for app
        page.wait_for_selector("text=Command Center", timeout=60000)

        # Click Wetware
        page.click('button:has-text("Wetware")')

        # Locate Corvo Noir button
        corvo_btn = page.locator('button:has-text("CORVO NOIR OS (Dashboard)")')
        corvo_btn.wait_for(state="visible")

        # JS Click to avoid animation issues
        page.evaluate("(el) => el.click()", corvo_btn.element_handle())

        # Wait for dashboard modal
        page.wait_for_selector("text=AQUIFER COHERENCE REAL-TIME ANALYTICS", timeout=60000)

        # Take screenshot
        page.screenshot(path="verification/corvo_noir_biometrics_check.png", full_page=True)

        # Close
        browser.close()

if __name__ == "__main__":
    run()
