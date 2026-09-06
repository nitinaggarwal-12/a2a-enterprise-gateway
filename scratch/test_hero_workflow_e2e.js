const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runHeroWorkflowE2E() {
  const rootDir = path.join(__dirname, '..');
  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_hero_' + Date.now());
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
  console.log('====================================================');
  console.log('🚀 TESTING INTERACTIVE 5-STEP HERO WORKFLOW');
  console.log('====================================================');

  await page.goto('http://127.0.0.1:8090/', { waitUntil: 'networkidle0' });
  await sleep(1000);

  const screenshotDir = path.join(rootDir, 'scratch', 'screenshots_hero');
  fs.mkdirSync(screenshotDir, { recursive: true });

  // 1. Verify Step 1: Agent Request
  console.log('• Verifying Step 1: Agent Request');
  let step = await page.evaluate(() => Alpine.$data(document.querySelector('body')).heroWorkflowStep);
  if (step !== 1) throw new Error(`Expected Step 1, got ${step}`);
  await page.screenshot({ path: path.join(screenshotDir, '01_hero_step1_agent_req.png') });

  // 2. Click to Step 2: AST Sanitizer
  console.log('• Advancing to Step 2: AST Sanitizer');
  await page.click('#btn-hero-action-step1');
  await sleep(600);
  step = await page.evaluate(() => Alpine.$data(document.querySelector('body')).heroWorkflowStep);
  if (step !== 2) throw new Error(`Expected Step 2, got ${step}`);
  await page.screenshot({ path: path.join(screenshotDir, '02_hero_step2_sanitizer.png') });

  // 3. Click to Step 3: Doctor A2UI Card
  console.log('• Advancing to Step 3: Doctor Review Card');
  await page.click('#btn-hero-action-step2');
  await sleep(600);
  step = await page.evaluate(() => Alpine.$data(document.querySelector('body')).heroWorkflowStep);
  if (step !== 3) throw new Error(`Expected Step 3, got ${step}`);
  await page.screenshot({ path: path.join(screenshotDir, '03_hero_step3_doctor_card.png') });

  // 4. Click to Step 4: Electronic Signature
  console.log('• Advancing to Step 4: 21 CFR Part 11 Signature');
  await page.click('#btn-hero-action-step3');
  await sleep(600);
  step = await page.evaluate(() => Alpine.$data(document.querySelector('body')).heroWorkflowStep);
  if (step !== 4) throw new Error(`Expected Step 4, got ${step}`);
  await page.screenshot({ path: path.join(screenshotDir, '04_hero_step4_signature_pad.png') });

  // 5. Click Sign Button & Verify Step 5: Dispense
  console.log('• Clicking Doctor Electronic Signature');
  await page.click('#btn-hero-sign');
  await sleep(1000);
  step = await page.evaluate(() => Alpine.$data(document.querySelector('body')).heroWorkflowStep);
  if (step !== 5) throw new Error(`Expected Step 5, got ${step}`);
  await page.screenshot({ path: path.join(screenshotDir, '05_hero_step5_dispense_complete.png') });

  // 6. Test Reset
  console.log('• Testing Reset Workflow');
  await page.click('#btn-hero-restart');
  await sleep(500);
  step = await page.evaluate(() => Alpine.$data(document.querySelector('body')).heroWorkflowStep);
  if (step !== 1) throw new Error(`Expected Step 1 after reset, got ${step}`);

  console.log('====================================================');
  console.log('✅ HERO WORKFLOW E2E TESTS: ALL 5 STEPS PASSED');
  console.log('====================================================');

  await browser.close();
  try {
    fs.rmSync(tempProfileDir, { recursive: true, force: true });
  } catch (_) {}
}

runHeroWorkflowE2E().catch((err) => {
  console.error('❌ FAILED:', err);
  process.exit(1);
});
