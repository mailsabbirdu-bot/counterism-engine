import asyncio
from playwright.async_api import async_playwright
import os

async def capture_frames():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # Base URL for the composition
        url = "http://localhost:3000/compositions/MAIN-SEQUENCE"

        frames_to_capture = [0, 120, 240, 360, 480, 600]
        os.makedirs("verification/final", exist_ok=True)

        print(f"Navigating to {url}...")
        await page.goto(url)
        # Wait for the studio to load
        await page.wait_for_selector("canvas", timeout=30000) # Procedural background uses canvas

        for frame in frames_to_capture:
            # Remotion Studio URL for a specific frame: ?frame=X
            frame_url = f"{url}?frame={frame}"
            print(f"Capturing frame {frame} at {frame_url}...")
            await page.goto(frame_url)
            # Give it a moment to render the frame
            await asyncio.sleep(3)
            await page.screenshot(path=f"verification/final/frame_{frame}.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_frames())
