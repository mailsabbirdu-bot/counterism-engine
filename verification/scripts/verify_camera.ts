import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';

async function verify() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const screenshotDir = path.join(process.cwd(), 'verification/screenshots');
  if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

  console.log("Navigating to NAV-TEST...");

  // Helper to take screenshot at specific frame using URL seek
  const captureFrame = async (frame: number, name: string) => {
    console.log(`Capturing frame ${frame} as ${name}...`);
    await page.goto(`http://localhost:3000/compositions/NAV-TEST?frame=${frame}`, { waitUntil: 'networkidle' });
    // Wait for cinematic animations to settle if any (though frame=N should be static)
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(screenshotDir, `${name}.png`) });
  };

  try {
    // 0: Initial state
    await captureFrame(0, 'nav_0');

    // 90: Stabilized on Bottom-Left
    // Keyframe 60-120 is the hold period
    await captureFrame(90, 'nav_bottom_left');

    // 210: Stabilized on Top-Right
    // Keyframe 180-240 is the hold period
    await captureFrame(210, 'nav_top_right');

    // 299: Back to center
    await captureFrame(299, 'nav_end');

    console.log("Verification screenshots saved to /verification/screenshots/");
  } catch (e) {
    console.error("Verification failed:", e);
  } finally {
    await browser.close();
  }
}

verify();
