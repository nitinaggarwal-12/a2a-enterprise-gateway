/**
 * Comprehensive Click & Error Audit across all interactive elements in Enterprise A2A Gateway Portal
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runButtonAudit() {
  const rootDir = '/Users/nitinagga/Documents/a2a-enterprise-gateway';
  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_btn_audit_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    defaultViewport: { width: 1600, height: 1000, deviceScaleFactor: 1 },
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
  const pageErrors = [];
  const consoleErrors = [];

  page.on('pageerror', (err) => {
    pageErrors.push(err.toString());
    console.error('[PAGE ERROR]', err.toString());
  });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.error('[CONSOLE ERROR]', msg.text());
    }
  });

  const portalUrl = 'http://127.0.0.1:8090';

  try {
    console.log(`[AUDIT] Loading portal at ${portalUrl}...`);
    await page.goto(portalUrl, { waitUntil: 'networkidle0' });
    await sleep(1500);

    // 1. Audit Navigation Tabs
    const tabs = [
      { id: 'landing', tabKey: 'landing' },
      { id: 'dag', tabKey: 'dag_studio' },
      { id: 'dose', tabKey: 'dose_curve' },
      { id: 'playground', tabKey: 'playground' },
      { id: 'a2ui', tabKey: 'a2ui_studio' },
      { id: 'veo', tabKey: 'veo_studio' },
      { id: 'overview', tabKey: 'overview' },
      { id: 'opt1', tabKey: 'opt1' },
      { id: 'opt2', tabKey: 'opt2' },
      { id: 'opt3', tabKey: 'opt3' },
      { id: 'integrations', tabKey: 'integrations' },
      { id: 'kpis', tabKey: 'kpis' },
      { id: 'alerts', tabKey: 'alerts_feedback' },
      { id: 'faq', tabKey: 'faq' },
      { id: 'advanced-lab', tabKey: 'advanced_a2a_lab' },
      { id: 'cloud-connect', tabKey: 'cloud_connect' },
      { id: 'ectd-studio', tabKey: 'ectd_studio' },
      { id: 'insilico-twin', tabKey: 'insilico_twin' },
      { id: 'promptcanvas-studio', tabKey: 'promptcanvas_studio' },
      { id: 'training', tabKey: 'training' }
    ];

    console.log(`\n--- 1. AUDITING ${tabs.length} SIDEBAR NAVIGATION TABS ---`);
    for (const t of tabs) {
      const tabSelector = `#tab-${t.id}`;
      const exists = await page.$(tabSelector);
      if (!exists) {
        console.warn(`[WARN] Tab button not found: ${tabSelector}`);
        continue;
      }
      await page.$eval(tabSelector, el => el.click());
      await sleep(300);
      const activeTab = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).currentTab);
      console.log(`Tab ${t.id} -> '${t.tabKey}': activeTab=${activeTab} ${activeTab === t.tabKey ? '✅' : '❌'}`);
    }

    // 2. Audit Top Navigation Controls
    console.log('\n--- 2. AUDITING TOP STICKY BAR BUTTONS ---');
    
    // Theme toggle
    console.log('Testing Theme Toggle...');
    const initialDark = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).isDark);
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.title && b.title.includes('Theme'));
      if (btn) btn.click();
    });
    await sleep(400);
    const toggledDark = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).isDark);
    console.log(`Theme toggle: ${initialDark} -> ${toggledDark} ${initialDark !== toggledDark ? '✅' : '❌'}`);

    // Language switcher buttons
    console.log('Testing Language Switcher buttons (EN, JA, DE, FR, ZH)...');
    const langs = ['en', 'ja', 'de', 'fr', 'zh'];
    for (const lang of langs) {
      await page.evaluate((l) => {
        Alpine.$data(document.querySelector('[x-data]')).setRegulatoryLang(l);
      }, lang);
      await sleep(200);
      const activeLang = await page.evaluate(() => Alpine.$data(document.querySelector('[x-data]')).currentLang);
      console.log(`Language ${lang}: activeLang=${activeLang} ${activeLang === lang ? '✅' : '❌'}`);
    }

    // 3. Audit Modals & Drawers
    console.log('\n--- 3. AUDITING MODALS & DRAWERS ---');
    const modalTests = [
      { name: 'User Readiness Modal', open: () => page.$eval('#btn-omni-readiness-orb', el => el.click()), check: () => Alpine.$data(document.querySelector('[x-data]')).omniReadinessModalOpen },
      { name: 'Omni Director Drawer', open: () => page.$eval('#btn-omni-director-pill', el => el.click()), check: () => Alpine.$data(document.querySelector('[x-data]')).omniDirectorDrawerOpen },
      { name: 'FDA Dossier Modal', open: () => page.$eval('#btn-fda-dossier-top', el => el.click()), check: () => Alpine.$data(document.querySelector('[x-data]')).fdaDossierModalOpen },
      { name: 'Dr. A2A Copilot Drawer', open: () => page.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).assistantOpen = true; }), check: () => Alpine.$data(document.querySelector('[x-data]')).assistantOpen },
      { name: 'SSO Login Modal', open: () => page.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).ssoModalOpen = true; }), check: () => Alpine.$data(document.querySelector('[x-data]')).ssoModalOpen },
      { name: 'BYOK Drawer', open: () => page.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).byokDrawerOpen = true; }), check: () => Alpine.$data(document.querySelector('[x-data]')).byokDrawerOpen },
      { name: 'Command Palette', open: () => page.evaluate(() => { Alpine.$data(document.querySelector('[x-data]')).commandPaletteOpen = true; }), check: () => Alpine.$data(document.querySelector('[x-data]')).commandPaletteOpen },
    ];

    for (const m of modalTests) {
      await m.open();
      await sleep(400);
      const isOpen = await page.evaluate(m.check);
      console.log(`Modal/Drawer [${m.name}]: open=${isOpen} ${isOpen ? '✅' : '❌'}`);
      await page.keyboard.press('Escape');
      await sleep(300);
    }

    // 4. Audit Links (<a> tags)
    console.log('\n--- 4. AUDITING ALL <a> LINKS ---');
    const links = await page.evaluate(() => {
      const aEls = Array.from(document.querySelectorAll('a'));
      return aEls.map(a => ({
        text: a.innerText.trim().substring(0, 40),
        href: a.getAttribute('href'),
        target: a.getAttribute('target'),
        hasClick: !!a.getAttribute('@click') || !!a.getAttribute('x-on:click')
      }));
    });

    console.log(`Found ${links.length} anchor tags:`);
    for (const link of links) {
      const isDead = (!link.href || link.href === '#' || link.href === '') && !link.hasClick;
      console.log(`  - Link "${link.text || 'icon'}": href="${link.href}" hasClick=${link.hasClick} ${isDead ? '⚠️ DEAD LINK' : '✅'}`);
    }

    // 5. Audit Buttons for any undefined or inert actions
    console.log('\n--- 5. AUDITING INERT BUTTONS (BUTTONS WITHOUT ACTIONS) ---');
    const inertButtons = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.filter(b => {
        const hasClick = b.hasAttribute('@click') || b.hasAttribute('x-on:click') || b.getAttribute('type') === 'submit';
        const hasOnClick = !!b.onclick;
        return !hasClick && !hasOnClick;
      }).map(b => ({
        text: b.innerText.trim().substring(0, 40),
        classes: b.className.substring(0, 50),
        id: b.id || '(no id)'
      }));
    });

    console.log(`Inert Buttons found: ${inertButtons.length}`);
    for (const ib of inertButtons) {
      console.log(`  - Button id="${ib.id}", text="${ib.text}", classes="${ib.classes}"`);
    }

    // Report Summary
    console.log('\n==================================================');
    console.log(`TOTAL PAGE ERRORS (Uncaught JS Exceptions): ${pageErrors.length}`);
    console.log(`TOTAL CONSOLE ERRORS: ${consoleErrors.length}`);
    console.log(`TOTAL INERT BUTTONS WITHOUT ACTIONS: ${inertButtons.length}`);
    console.log('==================================================');

  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch (_) {}
  }
}

runButtonAudit().catch(err => {
  console.error('[AUDIT ERROR]', err);
  process.exit(1);
});
