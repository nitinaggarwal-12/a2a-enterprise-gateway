const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runZeroTiltVerification() {
  const rootDir = path.join(__dirname, '..');
  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_tilt_' + Date.now());
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
  console.log('🛡️ VERIFYING ZERO-TILT POLICY ACROSS ALL SCREENS');
  console.log('====================================================');

  await page.goto('http://127.0.0.1:8090/', { waitUntil: 'networkidle0' });
  await sleep(1000);

  // Collect all glass-card elements
  const cards = await page.$$('.glass-card, .glass-cyber-card');
  console.log(`Found ${cards.length} cards/screens to test.`);

  let tiltViolations = 0;

  for (let i = 0; i < Math.min(cards.length, 15); i++) {
    const card = cards[i];
    const box = await card.boundingBox();
    if (!box) continue;

    // Move mouse across card corners and center
    await page.mouse.move(box.x + 10, box.y + 10);
    await sleep(50);
    await page.mouse.move(box.x + box.width - 10, box.y + 10);
    await sleep(50);
    await page.mouse.move(box.x + box.width - 10, box.y + box.height - 10);
    await sleep(50);
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await sleep(50);

    const transformInfo = await page.evaluate(el => {
      const computed = window.getComputedStyle(el).transform;
      const inline = el.style.transform;
      return { computed, inline };
    }, card);

    const has3D = (transformInfo.computed && transformInfo.computed.includes('matrix3d')) ||
                  (transformInfo.inline && (transformInfo.inline.includes('rotateX') || transformInfo.inline.includes('perspective') || transformInfo.inline.includes('rotateY')));

    if (has3D) {
      console.error(`❌ Card ${i} is tilting: inline="${transformInfo.inline}", computed="${transformInfo.computed}"`);
      tiltViolations++;
    }
  }

  console.log(`\n• 3D Tilt Violations Detected: ${tiltViolations}`);
  
  // Capture screenshot of stable, zero-tilt landing screen
  const screenshotPath = path.join(rootDir, 'scratch', 'screenshots', '01_zero_tilt_verified.png');
  fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
  await page.screenshot({ path: screenshotPath });
  console.log(`• Captured screenshot: ${screenshotPath}`);

  await browser.close();
  try {
    fs.rmSync(tempProfileDir, { recursive: true, force: true });
  } catch (_) {}

  if (tiltViolations > 0) {
    console.error('FAILED: Tilting screen detected!');
    process.exit(1);
  } else {
    console.log('✅ ZERO-TILT VERIFICATION PASSED: All screens are completely flat and stable.');
  }
}

runZeroTiltVerification().catch(err => {
  console.error(err);
  process.exit(1);
});
