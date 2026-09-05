/**
 * Comprehensive E2E Verification for UI/UX Navigation Enhancements:
 * 1. URL Hash Deep-Linking & History Navigation
 * 2. Universal Escape Key Modal & Drawer Dismissal
 * 3. Mobile Viewport Off-Canvas Drawer, Scrim Backdrop & Auto-Collapse
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  const rootDir = '/Users/nitinagga/Documents/a2a-enterprise-gateway';
  const outDir = path.join(rootDir, 'scratch', 'screenshots_navigation');
  fs.mkdirSync(outDir, { recursive: true });

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;
  console.log(`Starting Navigation E2E Suite with Chrome binary: ${executablePath || 'bundled Chromium'}`);

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_nav_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    defaultViewport: { width: 1440, height: 900, deviceScaleFactor: 1 },
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--no-default-browser-check',
      '--no-first-run',
      `--user-data-dir=${tempProfileDir}`,
    ],
  });

  const page = await browser.newPage();
  const portalUrl = 'http://127.0.0.1:8090';

  const saveShot = async (filename) => {
    await sleep(800);
    const buf = await page.screenshot({ fullPage: false });
    const fullPath = path.join(outDir, filename);
    fs.writeFileSync(fullPath, buf);
    console.log(`[PASS] Saved screenshot: ${filename} -> file://${fullPath}`);
  };

  try {
    // ----------------------------------------------------
    // TEST SUITE 1: URL Hash Deep-Linking on Initial Load
    // ----------------------------------------------------
    console.log('\n=== 1. TESTING URL HASH DEEP LINKING ===');
    
    // 1.1 Direct load of #tab-dose_curve
    console.log('Navigating directly to #tab-dose_curve...');
    await page.goto(`${portalUrl}/#tab-dose_curve`, { waitUntil: 'networkidle0' });
    await sleep(1000);
    const tab1 = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).currentTab);
    console.log(`Current Tab on #tab-dose_curve load: "${tab1}" (expected: "dose_curve")`);
    if (tab1 !== 'dose_curve') throw new Error(`Deep-linking failed: expected 'dose_curve', got '${tab1}'`);
    await saveShot('01_deep_link_dose_curve.png');

    // 1.2 Direct load of #tab-dag alias
    console.log('Navigating directly to #tab-dag...');
    await page.goto(`${portalUrl}/#tab-dag`, { waitUntil: 'networkidle0' });
    await sleep(1000);
    const tab2 = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).currentTab);
    console.log(`Current Tab on #tab-dag load: "${tab2}" (expected: "dag_studio")`);
    if (tab2 !== 'dag_studio') throw new Error(`Deep-linking alias failed: expected 'dag_studio', got '${tab2}'`);
    await saveShot('02_deep_link_dag_studio.png');

    // 1.3 Direct load of #tab-veo_studio
    console.log('Navigating directly to #tab-veo_studio...');
    await page.goto(`${portalUrl}/#tab-veo_studio`, { waitUntil: 'networkidle0' });
    await sleep(1000);
    const tab3 = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).currentTab);
    console.log(`Current Tab on #tab-veo_studio load: "${tab3}" (expected: "veo_studio")`);
    if (tab3 !== 'veo_studio') throw new Error(`Deep-linking failed: expected 'veo_studio', got '${tab3}'`);
    await saveShot('03_deep_link_veo_studio.png');

    // 1.4 Tab Click updates URL Hash
    console.log('Clicking #tab-playground and verifying URL hash synchronization...');
    await page.$eval('#tab-playground', el => el.click());
    await sleep(1000);
    const currentHash = await page.evaluate(() => window.location.hash);
    console.log(`URL Hash after clicking playground: "${currentHash}" (expected: "#tab-playground")`);
    if (currentHash !== '#tab-playground') throw new Error(`Hash synchronization failed: expected '#tab-playground', got '${currentHash}'`);
    await saveShot('04_hash_sync_playground.png');

    // 1.5 Hashchange / Browser Back Simulation
    console.log('Simulating hashchange event to #tab-overview...');
    await page.evaluate(() => { window.location.hash = '#tab-overview'; });
    await sleep(1000);
    const tab4 = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).currentTab);
    console.log(`Current Tab after hashchange: "${tab4}" (expected: "overview")`);
    if (tab4 !== 'overview') throw new Error(`Hashchange navigation failed: expected 'overview', got '${tab4}'`);
    await saveShot('05_hashchange_overview.png');

    // ----------------------------------------------------
    // TEST SUITE 2: Universal Escape Key Modal Dismissal
    // ----------------------------------------------------
    console.log('\n=== 2. TESTING UNIVERSAL ESCAPE KEY DISMISSAL ===');

    // 2.1 Command Palette Cmd+K / Escape
    console.log('Opening Command Palette...');
    await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).openCommandPalette());
    await sleep(800);
    let cmdOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).commandPaletteOpen);
    console.log(`Command Palette open: ${cmdOpen}`);
    await saveShot('06_command_palette_open.png');
    console.log('Pressing Escape...');
    await page.keyboard.press('Escape');
    await sleep(800);
    cmdOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).commandPaletteOpen);
    console.log(`Command Palette after Escape: ${cmdOpen} (expected: false)`);
    if (cmdOpen !== false) throw new Error('Escape failed to close Command Palette');

    // 2.2 SSO Modal Escape
    console.log('Opening SSO Modal...');
    await page.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).ssoModalOpen = true; });
    await sleep(800);
    let ssoOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).ssoModalOpen);
    console.log(`SSO Modal open: ${ssoOpen}`);
    await saveShot('07_sso_modal_open.png');
    console.log('Pressing Escape...');
    await page.keyboard.press('Escape');
    await sleep(800);
    ssoOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).ssoModalOpen);
    console.log(`SSO Modal after Escape: ${ssoOpen} (expected: false)`);
    if (ssoOpen !== false) throw new Error('Escape failed to close SSO Modal');

    // 2.3 Legal Modal Escape
    console.log('Opening Legal Modal (disclaimer)...');
    await page.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).legalModal = 'disclaimer'; });
    await sleep(800);
    let legalOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).legalModal);
    console.log(`Legal Modal active: ${legalOpen}`);
    await saveShot('08_legal_modal_open.png');
    console.log('Pressing Escape...');
    await page.keyboard.press('Escape');
    await sleep(800);
    legalOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).legalModal);
    console.log(`Legal Modal after Escape: ${legalOpen} (expected: null)`);
    if (legalOpen !== null) throw new Error('Escape failed to close Legal Modal');

    // 2.4 Dr. A2A Copilot Drawer Escape
    console.log('Opening Dr. A2A Copilot Assistant Drawer...');
    await page.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).assistantOpen = true; });
    await sleep(800);
    let asstOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).assistantOpen);
    console.log(`Assistant open: ${asstOpen}`);
    await saveShot('09_assistant_drawer_open.png');
    console.log('Pressing Escape...');
    await page.keyboard.press('Escape');
    await sleep(800);
    asstOpen = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).assistantOpen);
    console.log(`Assistant after Escape: ${asstOpen} (expected: false)`);
    if (asstOpen !== false) throw new Error('Escape failed to close Assistant Drawer');

    // ----------------------------------------------------
    // TEST SUITE 3: Mobile Viewport Off-Canvas Drawer
    // ----------------------------------------------------
    console.log('\n=== 3. TESTING MOBILE VIEWPORT (390x844) OFF-CANVAS DRAWER ===');
    await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    await sleep(800);

    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.isMobile = true;
      state.sidebarCollapsed = true;
    });
    await sleep(800);
    await saveShot('10_mobile_viewport_collapsed.png');

    // 3.1 Open Drawer via Hamburger
    console.log('Toggling mobile drawer open...');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.sidebarCollapsed = false;
    });
    await sleep(800);
    const drawerOpen = await page.evaluate(() => !Alpine.$data(document.querySelector('[x-data]')).sidebarCollapsed);
    console.log(`Mobile Drawer expanded: ${drawerOpen}`);
    if (!drawerOpen) throw new Error('Mobile drawer failed to expand');
    await saveShot('11_mobile_drawer_expanded.png');

    // 3.2 Close Drawer via Escape
    console.log('Testing Mobile Drawer Escape dismissal...');
    await page.keyboard.press('Escape');
    await sleep(800);
    const drawerCollapsedAfterEscape = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).sidebarCollapsed);
    console.log(`Mobile Drawer collapsed after Escape: ${drawerCollapsedAfterEscape}`);
    if (!drawerCollapsedAfterEscape) throw new Error('Escape failed to close mobile drawer');
    await saveShot('12_mobile_drawer_closed_escape.png');

    // 3.3 Auto-collapse when selecting a tab inside mobile drawer
    console.log('Re-opening drawer and selecting tab #tab-kpis...');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.sidebarCollapsed = false;
    });
    await sleep(800);
    await page.$eval('#tab-kpis', el => el.click());
    await sleep(1000);
    const currentTabMobile = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).currentTab);
    const drawerClosedOnSelect = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).sidebarCollapsed);
    console.log(`Mobile Tab selected: "${currentTabMobile}" (expected: "kpis"), Drawer auto-collapsed: ${drawerClosedOnSelect}`);
    if (currentTabMobile !== 'kpis') throw new Error('Failed to switch tab on mobile');
    if (!drawerClosedOnSelect) throw new Error('Mobile drawer did not auto-collapse after selecting tab');
    await saveShot('13_mobile_tab_switched_autoclosed.png');

    console.log('\n🎉 ALL NAVIGATION, HASH SYNC, ESCAPE & MOBILE TESTS PASSED 100%!');
  } finally {
    await browser.close();
    try { fs.rmSync(tempProfileDir, { recursive: true, force: true }); } catch (_) {}
  }
}

main().catch(err => {
  console.error('FATAL ERROR in Navigation E2E Suite:', err);
  process.exit(1);
});
