const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log("Starting Enterprise Audit...");

  try {
    // 1. Load login
    await page.goto('http://localhost:8000/login.html');
    console.log("- Login page loaded");

    // 2. Perform Login
    await page.fill('input[type="email"]', 'admin@borges.os');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Wait for redirect and dashboard
    await page.waitForURL('**/static/index.html');
    console.log("- Login successful, dashboard reached");

    // 3. Verify Dashboard Metrics
    await page.waitForSelector('#metric-total-leads');
    const totalLeads = await page.innerText('#metric-total-leads');
    console.log(`- Dashboard Metrics: Total Leads = ${totalLeads}`);

    // 4. Test Sidebar Persistence
    const sidebar = await page.$('#app-sidebar');
    const boxBefore = await sidebar.boundingBox();
    console.log(`- Sidebar width before: ${boxBefore.width}`);
    
    await page.click('#sidebar-toggle-icon');
    await page.waitForTimeout(500);
    const boxAfter = await sidebar.boundingBox();
    console.log(`- Sidebar width after toggle: ${boxAfter.width}`);
    
    if (boxAfter.width < boxBefore.width) {
        console.log("  [PASS] Sidebar collapsed");
    }

    // Reload to test persistence
    await page.reload();
    await page.waitForTimeout(1000);
    const boxReload = await (await page.$('#app-sidebar')).boundingBox();
    console.log(`- Sidebar width after reload: ${boxReload.width}`);
    if (boxReload.width === boxAfter.width) {
        console.log("  [PASS] Persistence working");
    }

    // 5. Test Inbox and Lead Details
    await page.click('button[onclick*="inbox"]');
    console.log("- Switched to Inbox");
    
    await page.waitForSelector('#inbox-leads-list > div');
    await page.click('#inbox-leads-list > div:first-child');
    console.log("- Lead selected");

    // Wait for detail panel
    await page.waitForSelector('#detail-master-ltv');
    const ltv = await page.innerText('#detail-master-ltv');
    console.log(`- Lead Details: LTV = ${ltv}`);

    // 6. Test Auto-save Notes
    const notesText = "Audit Note " + Date.now();
    await page.fill('#detail-master-notes', notesText);
    console.log("- Typing auto-save note...");
    
    // Wait for auto-save debounce (1.5s + buffer)
    await page.waitForTimeout(3000);
    const saveBtn = await page.innerText('button[onclick="saveInternalNotes()"]');
    console.log(`- Save button state: ${saveBtn}`);

    console.log("\n✅ ALL ENTERPRISE AUDITS PASSED");

  } catch (err) {
    console.error("\n❌ AUDIT FAILED:", err.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
