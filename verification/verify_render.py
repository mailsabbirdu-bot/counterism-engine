from playwright.sync_api import sync_playwright
import time

def run_cuj(page):
    # Navigate to the Remotion preview
    page.goto("http://localhost:3000")
    page.wait_for_timeout(5000) # Increased wait for load

    # In Remotion preview, we want to see the main stage
    # page.wait_for_selector("canvas", timeout=30000)

    # Check if we are on the Root composition or if we need to select one
    # If there are multiple compositions, they show up in the sidebar.

    # Take a screenshot of the initial state
    page.screenshot(path="verification/screenshots/initial_load.png")
    print("Initial screenshot taken")

    # Try to play the video for a bit to see animations
    page.keyboard.press(" ")
    page.wait_for_timeout(5000)

    # Take another screenshot during playback
    page.screenshot(path="verification/screenshots/playback.png")
    print("Playback screenshot taken")

    # Take the final verification screenshot
    page.screenshot(path="verification/screenshots/verification.png")
    print("Final verification screenshot taken")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="verification/videos",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
