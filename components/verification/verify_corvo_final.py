from playwright.sync_api import sync_playwright, expect

def verify_corvo_noir_full(page):
    # 1. Navigate to the dashboard
    page.goto("http://localhost:5173")

    # Wait for the main UI to load
    expect(page.get_by_text("Arkhe-PNT")).to_be_visible(timeout=10000)

    # 2. Click the 'Wetware' tab in the Command Center
    # Based on the screenshot error_v9.png, the Command Center tabs are at the bottom right.
    wetware_tab = page.get_by_role("button", name="WETWARE")
    wetware_tab.click()

    # 3. Open the Corvo Noir Dashboard
    # It has text "CORVO NOIR OS (Dashboard)"
    corvo_btn = page.get_by_role("button", name="CORVO NOIR OS (Dashboard)")
    corvo_btn.click()

    # 4. Verify Corvo Noir is visible
    expect(page.get_by_text("CORVO NOIR OS")).to_be_visible(timeout=5000)

    # 5. Take screenshot of the Coherence tab (default)
    page.screenshot(path="/home/jules/verification/corvo_coherence.png")

    # 6. Switch to Governance tab
    page.get_by_role("button", name="GOVERNANCE").click()
    # Apply pulse
    page.get_by_role("button", name="APPLY PULSE").click()
    page.wait_for_timeout(1000) # Wait for state update
    page.screenshot(path="/home/jules/verification/corvo_governance.png")

    # 7. Switch to Bio-Link tab
    page.get_by_role("button", name="BIOLINK").click()
    page.screenshot(path="/home/jules/verification/corvo_biolink.png")

    # 8. Switch to Security tab
    page.get_by_role("button", name="SECURITY").click()
    page.screenshot(path="/home/jules/verification/corvo_security.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Set viewport to capture the whole dashboard
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        try:
            verify_corvo_noir_full(page)
            print("Verification successful")
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/failure_debug.png")
        finally:
            browser.close()
