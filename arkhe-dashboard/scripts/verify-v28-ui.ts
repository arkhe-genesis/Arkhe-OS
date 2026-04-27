import { chromium } from 'playwright';

async function verify() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    console.log('Navigating to Arkhe OS Dashboard...');
    await page.goto('http://localhost:3001/dashboard');
    await page.waitForTimeout(5000); // Wait for animations and initial fetches

    // Take screenshot
    await page.setViewportSize({ width: 1280, height: 1600 });
    await page.screenshot({ path: '/home/jules/verification/dashboard_v28_final.png', fullPage: true });
    console.log('Screenshot saved to /home/jules/verification/dashboard_v28_final.png');

    // Check for key components
    const content = await page.content();
    const hasSafeCore = content.includes('SAFE CORE');
    const hasRetrocausal = content.includes('RETROCAUSAL WISDOM');
    const hasMarketplace = content.includes('QUANTUM TALENT MARKETPLACE');

    console.log('Verification Results:');
    console.log(`- Safe Core Panel: ${hasSafeCore ? 'PRESENT' : 'MISSING'}`);
    console.log(`- Retrocausal Panel: ${hasRetrocausal ? 'PRESENT' : 'MISSING'}`);
    console.log(`- Marketplace Panel: ${hasMarketplace ? 'PRESENT' : 'MISSING'}`);

  } catch (error) {
    console.error('UI Verification failed:', error);
  } finally {
    await browser.close();
  }
}

verify();
