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
    if (msg.type() === 'error' && !msg.text().includes('WebGL')) {
      errors.push({ type: 'console.error', text: msg.text() });
      console.error('[CONSOLE ERROR]', msg.text());
    }
  });

  const portalUrl = 'http://127.0.0.1:8090';
  console.log(`Loading portal at ${portalUrl}...`);
  await page.goto(portalUrl, { waitUntil: 'networkidle0' });
  await sleep(1500);

  // Get all visible tab buttons in sidebar
  const tabs = [
    'landing', 'dag_studio', 'dose_curve', 'playground',
    'a2ui_studio', 'veo_studio', 'overview', 'opt1', 'opt2', 'opt3',
    'integrations', 'kpis', 'alerts_feedback', 'faq',
    'advanced_a2a_lab', 'cloud_connect', 'ectd_studio', 'insilico_twin',
    'promptcanvas_studio', 'training'
  ];

  console.log(`\nTesting ${tabs.length} tabs and clicking interactive buttons...`);
  for (const tab of tabs) {
    console.log(`\n--- TAB: ${tab} ---`);
    await page.evaluate((t) => {
      Alpine.$data(document.querySelector('[x-data]')).currentTab = t;
    }, tab);
    await sleep(500);

    // Find all buttons inside current visible tab container
    const clickedCount = await page.evaluate(() => {
      let count = 0;
      const visibleButtons = Array.from(document.querySelectorAll('div[x-show*="currentTab"] button'));
      for (const btn of visibleButtons) {
        if (btn.offsetParent !== null && !btn.disabled) {
          // Check if button has a click handler
          const clickAttr = btn.getAttribute('@click') || btn.getAttribute('x-on:click');
          if (clickAttr && !clickAttr.includes('history.back') && !clickAttr.includes('delete') && !clickAttr.includes('reset')) {
            try {
              btn.click();
              count++;
            } catch (e) {
              console.error('Error clicking button:', btn.innerText, e);
            }
          }
        }
      }
      return count;
    });
    console.log(`Clicked ${clickedCount} active buttons on tab ${tab}. Errors so far: ${errors.length}`);
    await sleep(300);
  }

  console.log('\n==================================================');
  console.log(`TOTAL BUTTONS TESTED: ${tabs.length} tabs`);
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
