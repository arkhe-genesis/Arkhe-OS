from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        try:
            page.goto("http://localhost:3000")

            # Wait for app to load
            page.wait_for_selector("text=Command Center", timeout=60000)

            # Click Wetware tab
            page.click('button:has-text("Wetware")')
            time.sleep(2)

            # Use JS to find and click the button directly regardless of visibility or scroll
            clicked = page.evaluate("""() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const corvoBtn = buttons.find(b => b.textContent.includes('CORVO NOIR OS (Dashboard)'));
                if (corvoBtn) {
                    corvoBtn.click();
                    return true;
                }
                return false;
            }""")

            if clicked:
                print("Clicked Corvo button via JS")
                # Wait for modal content specifically
                try:
                    page.wait_for_selector("text=AQUIFER COHERENCE REAL-TIME ANALYTICS", timeout=20000)
                    print("Modal content detected!")
                except Exception as e:
                    print(f"Modal content NOT found: {e}")

                time.sleep(5)
                page.screenshot(path="verification/corvo_noir_full_check.png", full_page=True)
            else:
                print("Corvo button NOT found in DOM")
                page.screenshot(path="verification/corvo_noir_dom_fail.png")

        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="verification/corvo_noir_error.py")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
