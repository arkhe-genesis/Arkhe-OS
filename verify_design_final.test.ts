
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { test, expect } from '@playwright/test';

test('verify corvo noir dashboard design', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Wait for the app to load
  await page.waitForSelector('text=Command Center');

  // Click Wetware tab
  await page.click('button:has-text("Wetware")');

  // Wait for the Corvo Noir button to be visible
  const corvoBtn = page.locator('button:has-text("CORVO NOIR OS (Dashboard)")');
  await expect(corvoBtn).toBeVisible();

  // Use JS click to bypass animation blocks
  await page.evaluate((el) => (el as HTMLElement).click(), await corvoBtn.elementHandle());

  // Wait for modal
  await page.waitForSelector('text=AQUIFER COHERENCE REAL-TIME ANALYTICS');

  // Capture screenshot
  await page.screenshot({ path: 'verification/corvo_noir_final_check.png', fullPage: true });

  // Check for specific design elements in the DOM if possible
  const dashboard = page.locator('div:has-text("CORVO NOIR OS")').first();
  const bgColor = await dashboard.evaluate((el) => window.getComputedStyle(el).backgroundColor);
  console.log('Dashboard BG Color:', bgColor);

  // Expect Emerald Signal Green somewhere (e.g. Activity icon)
  const activityIcon = page.locator('.text-emerald-signal').first();
  await expect(activityIcon).toBeVisible();
});
