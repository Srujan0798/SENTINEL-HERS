import { test, expect } from "@playwright/test";

const DEMO_EMAIL = "demo@sentinel.io";
const DEMO_PASSWORD = "Sentinel2026!";

test.describe("Sacred Demo Path", () => {
  test("full judge walkthrough under 8 minutes", async ({ page }) => {
    // 1. Landing page → redirected to login
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByText(/sign in|login/i).first()).toBeVisible();

    // 2. Login with demo credentials
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // 3. Dashboard shows metric cards
    await expect(page.getByText(/total incidents|SEV1 active|MTTR|Open SLA/i).first()).toBeVisible({ timeout: 10000 });

    // 4. Navigate to incidents → war room auto-opens for SEV1
    await page.goto("/incidents");
    await expect(page.getByText(/AI Summary|Root Cause|Timeline|Tasks/i).first()).toBeVisible({ timeout: 15000 });

    // 5. AI Summary is visible (not loading, not placeholder)
    const summaryText = await page.getByText(/Click an incident/i).count();
    expect(summaryText).toBe(0);

    // 6. AI Summary panel has content
    await expect(page.getByText(/generating/i)).toHaveCount(0, { timeout: 20000 });

    // 7. RCA button works — click and get hypotheses
    await page.getByText(/Analyze Root Causes|Root Cause Analysis/i).click();
    await expect(page.getByText(/generating|Analyzing/i)).toHaveCount(0, { timeout: 30000 });
    const rcaText = await page.getByText(/Generating|Analyzing/i).count();
    expect(rcaText).toBe(0);

    // 8. Status advance — click Advance button
    const advanceBtn = page.getByText(/Advance to /i);
    if (await advanceBtn.isVisible()) {
      await advanceBtn.click();
      await expect(page.getByText(/advance to /i)).not.toBeVisible({ timeout: 10000 });
    }

    // 9. Assign to me
    const assignBtn = page.getByText(/Assign to me/i);
    if (await assignBtn.isVisible()) {
      await assignBtn.click();
      await expect(page.getByText(/Assigned to you/i)).toBeVisible({ timeout: 10000 });
    }

    // 10. Escalate button opens dialog
    await page.getByText(/Escalate Incident/i).click();
    await expect(page.getByText(/Reason/i).first()).toBeVisible({ timeout: 5000 });
    await page.fill("textarea", "Needs senior review");
    await page.getByText(/Confirm Escalation/i).click();
    await expect(page.getByText(/Escalating/i)).toHaveCount(0, { timeout: 10000 });

    // 11. Create Task dialog
    await page.getByText(/\+ Add Task|Add Task/i).click();
    await expect(page.getByText(/Title/i).first()).toBeVisible({ timeout: 5000 });
    await page.fill("#taskTitle", "Verify payment fix in staging");
    await page.getByText(/Create Task/i).click();
    await expect(page.getByText(/Verify payment/i)).toBeVisible({ timeout: 10000 });

    // 12. Navigate to Analytics
    await page.getByText(/Analytics/i).first().click();
    await expect(page).toHaveURL(/\/analytics/);
    await expect(page.getByText(/total incidents|MTTR|alert|risk/i).first()).toBeVisible({ timeout: 10000 });

    // 13. Navigate to Monitoring
    await page.getByText(/Monitoring|Health/i).first().click();
    await expect(page).toHaveURL(/\/monitoring|\/health/);

    // 14. Deployments page
    await page.getByText(/Deployments/i).first().click();
    await expect(page.getByText(/Service|Version|SHA|Status/i).first()).toBeVisible({ timeout: 10000 });
  });
});
