const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function clickAllButtonsTest() {
  const rootDir = '/Users/nitinagga/Documents/a2a-enterprise-gateway';
  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_clickall_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    protocolTimeout: 120000,
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
  const errors = [];

  page.on('pageerror', err => {
    errors.push({ type: 'pageerror', text: err.toString() });
    console.error('[UNCAUGHT PAGE ERROR]', err.toString());
  });

  page.on('console', msg => {
    const text = msg.text();
    // Exclude WebGL headless notices and expected 409 Conflict anti-replay responses
    if (msg.type() === 'error' && !text.includes('WebGL') && !text.includes('409 (Conflict)')) {
      errors.push({ type: 'console.error', text });
      console.error('[CONSOLE ERROR]', text);
    }
  });

  const portalUrl = 'http://127.0.0.1:8090';
  console.log(`Loading portal at ${portalUrl}...`);
  await page.goto(portalUrl, { waitUntil: 'networkidle0' });
  await sleep(1500);

  // 20 Active workspace tabs
  const tabs = [
    'landing', 'dag_studio', 'dose_curve', 'playground',
    'a2ui_studio', 'veo_studio', 'overview', 'opt1', 'opt2', 'opt3',
    'integrations', 'kpis', 'alerts_feedback', 'faq',
    'advanced_a2a_lab', 'cloud_connect', 'ectd_studio', 'insilico_twin',
    'promptcanvas_studio', 'training'
  ];

  console.log(`\nTesting ${tabs.length} tabs and clicking interactive buttons...`);
  let totalButtonsClicked = 0;

  for (const tab of tabs) {
    await page.evaluate((t) => {
      Alpine.$data(document.querySelector('[x-data]')).currentTab = t;
    }, tab);
    await sleep(400);

    // Get count of visible buttons with click handlers on current tab
    const buttonIndices = await page.evaluate(() => {
      const visibleButtons = Array.from(document.querySelectorAll('div[x-show*="currentTab"] button'));
      const indices = [];
      visibleButtons.forEach((btn, idx) => {
        if (btn.offsetParent !== null && !btn.disabled) {
          const clickAttr = btn.getAttribute('@click') || btn.getAttribute('x-on:click');
          if (clickAttr && !clickAttr.includes('history.back') && !clickAttr.includes('delete') && !clickAttr.includes('reset')) {
            indices.push(idx);
          }
        }
      });
      return indices;
    });

    let tabClicked = 0;
    // Click up to 6 representative buttons per tab sequentially with settling delays
    const toClick = buttonIndices.slice(0, 6);
    for (const idx of toClick) {
      try {
        await page.evaluate((i) => {
          const visibleButtons = Array.from(document.querySelectorAll('div[x-show*="currentTab"] button'));
          if (visibleButtons[i]) visibleButtons[i].click();
        }, idx);
        tabClicked++;
        totalButtonsClicked++;
        await sleep(150);
      } catch (e) {
        console.warn(`[WARN] Button click on tab ${tab} index ${idx}:`, e.message);
      }
    }
    console.log(`Tab ${tab}: Clicked ${tabClicked} interactive buttons. Errors so far: ${errors.length}`);
  }

  console.log('\n==================================================');
  console.log(`TOTAL BUTTONS TESTED & CLICKED: ${totalButtonsClicked} across ${tabs.length} tabs`);
  console.log(`TOTAL JAVASCRIPT / CONSOLE ERRORS: ${errors.length}`);
  if (errors.length > 0) {
    console.log('Errors:', errors);
  } else {
    console.log('✅ ZERO UNCAUGHT JAVASCRIPT EXCEPTIONS ACROSS ALL BUTTON CLICKS!');
  }
  console.log('==================================================');

  await browser.close();
  try {
    fs.rmSync(tempProfileDir, { recursive: true, force: true });
  } catch (_) {}
}

clickAllButtonsTest().catch(err => {
  console.error('[TEST ERROR]', err);
  process.exit(1);
});
