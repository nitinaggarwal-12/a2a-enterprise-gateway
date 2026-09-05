/**
 * Quality Gate: Deep-Link URL State Addressability E2E Test
 * Validates W3C Principle of Addressability and Shareable URL Navigation.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runDeepLinkAudit() {
  const rootDir = path.join(__dirname, '..');
  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_deeplink_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    protocolTimeout: 60000,
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

  page.on('pageerror', err => errors.push(err.toString()));
  page.on('console', msg => {
    if (msg.type() === 'error' && !msg.text().includes('WebGL')) {
      errors.push(msg.text());
    }
  });

  const baseUrl = 'http://127.0.0.1:8090';

  console.log('====================================================');
  console.log('🔗 QUALITY GATE: DEEP-LINK URL ADDRESSABILITY AUDIT');
  console.log('====================================================');

  const testCases = [
    {
      name: 'FDA Dossier Inspection Modal',
      url: `${baseUrl}/#modal-fda-dossier`,
      check: () => Alpine.$data(document.querySelector('[x-data]')).fdaDossierModalOpen === true,
      domSelector: '#modal-fda-dossier',
    },
    {
      name: 'Omni Director Drawer',
      url: `${baseUrl}/#drawer-director`,
      check: () => Alpine.$data(document.querySelector('[x-data]')).omniDirectorDrawerOpen === true,
      domSelector: '#drawer-omni-director',
    },
    {
      name: 'Dr. A2A Multimodal Copilot Drawer',
      url: `${baseUrl}/#drawer-copilot`,
      check: () => Alpine.$data(document.querySelector('[x-data]')).assistantOpen === true,
      domSelector: '#drawer-dr-a2a-copilot',
    },
    {
      name: 'BYOK Key Management Drawer',
      url: `${baseUrl}/#drawer-byok`,
      check: () => Alpine.$data(document.querySelector('[x-data]')).byokDrawerOpen === true,
      domSelector: '#drawer-byok-settings',
    },
    {
      name: 'Enterprise SSO Login Modal',
      url: `${baseUrl}/#modal-sso`,
      check: () => Alpine.$data(document.querySelector('[x-data]')).ssoModalOpen === true,
      domSelector: '#modal-sso-login',
    },
    {
      name: 'Omni User Readiness Modal',
      url: `${baseUrl}/#modal-readiness`,
      check: () => Alpine.$data(document.querySelector('[x-data]')).omniReadinessModalOpen === true,
      domSelector: '#modal-omni-readiness',
    },
    {
      name: 'Sub-View: Veo 2 Studio Act 3 Direct Keyframe',
      url: `${baseUrl}/#tab-veo/act-3`,
      check: () => {
        const data = Alpine.$data(document.querySelector('[x-data]'));
        return data.currentTab === 'veo_studio' && data.veoActiveAct === 3;
      },
      domSelector: '#veo-stage-container',
    },
    {
      name: 'Tab Direct Addressability: Visual DAG Studio',
      url: `${baseUrl}/#tab-dag`,
      check: () => Alpine.$data(document.querySelector('[x-data]')).currentTab === 'dag_studio',
      domSelector: '#tab-dag',
    },
  ];

  let passed = 0;
  for (const tc of testCases) {
    console.log(`\n• Testing Direct Deep Link: ${tc.name}`);
    console.log(`  Target URL: ${tc.url}`);
    await page.goto(tc.url, { waitUntil: 'networkidle0' });
    await sleep(900); // 800ms+ settling delay

    const stateOk = await page.evaluate(tc.check);
    const domOk = await page.$(tc.domSelector) !== null;

    if (stateOk && domOk) {
      console.log(`  Result: ✅ PASSED (State Addressable & DOM Mounted)`);
      passed++;
    } else {
      console.error(`  Result: ❌ FAILED (State=${stateOk}, DOM=${domOk})`);
      errors.push(`Deep link failed for ${tc.name}`);
    }
  }

  // Test Escape Key restores clean URL hash
  console.log('\n• Testing Modal Escape Key restores tab URL hash...');
  await page.goto(`${baseUrl}/#modal-fda-dossier`, { waitUntil: 'networkidle0' });
  await sleep(800);
  await page.keyboard.press('Escape');
  await sleep(600);
  const finalHash = await page.evaluate(() => window.location.hash);
  const fdaClosed = await page.evaluate(() => !Alpine.$data(document.querySelector('[x-data]')).fdaDossierModalOpen);
  console.log(`  Escape pressed: fdaClosed=${fdaClosed}, finalHash="${finalHash}"`);
  const escapeOk = fdaClosed && (finalHash.startsWith('#tab-') || finalHash === '');
  if (escapeOk) {
    console.log(`  Result: ✅ PASSED (Hash clean on dismissal)`);
    passed++;
  } else {
    console.error(`  Result: ❌ FAILED dismissal hash cleanup`);
    errors.push('Dismissal hash cleanup failed');
  }

  console.log('\n====================================================');
  console.log(`DEEP-LINK RESULTS: ${passed}/${testCases.length + 1} PASSED`);
  console.log(`TOTAL CONSOLE / PAGE ERRORS: ${errors.length}`);
  console.log('====================================================');

  await browser.close();
  try {
    fs.rmSync(tempProfileDir, { recursive: true, force: true });
  } catch (_) {}

  if (errors.length > 0) {
    process.exit(1);
  }
}

runDeepLinkAudit().catch(err => {
  console.error('[DEEPLINK TEST ERROR]', err);
  process.exit(1);
});
