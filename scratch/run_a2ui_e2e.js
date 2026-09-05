/**
 * Puppeteer E2E Automation Suite for Universal A2UI Omnichannel Transpiler Studio
 * and Gemini Enterprise User Training Hub (Step 6).
 *
 * Runs exclusively on Google Signed Chrome with 800ms settling delays per protocol.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runA2UIE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_e2e');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  [scratchDir, docsDir, staticDir].forEach((dir) => {
    fs.mkdirSync(dir, { recursive: true });
  });

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(__dirname, '.chrome_profile_a2ui_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  console.log('🚀 Launching Puppeteer Headless Chrome (Google Signed)...');
  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    defaultViewport: { width: 1600, height: 1050 },
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

  // Listen to browser console logs
  page.on('console', (msg) => {
    const text = msg.text();
    if (msg.type() === 'error') {
      console.error(`  [Browser Console Error] ${text}`);
    }
  });

  page.on('pageerror', (err) => {
    console.error(`  [Browser Page Error] ${err.message}`);
  });

  try {
    console.log(`Navigating to Visual Verification Portal: ${portalUrl}...`);
    await page.goto(portalUrl, { waitUntil: 'domcontentloaded' });
    await sleep(2000);

    const saveShot = async (filename) => {
      await sleep(800); // 800ms mandatory settling delay per protocol
      const buf = await page.screenshot({ fullPage: false });
      fs.writeFileSync(path.join(scratchDir, filename), buf);
      fs.writeFileSync(path.join(docsDir, filename), buf);
      fs.writeFileSync(path.join(staticDir, filename), buf);
      console.log(`  📸 Captured & Saved: ${filename}`);
    };

    const setTheme = async (isDark) => {
      await page.evaluate((dark) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.isDark = dark;
        const root = document.getElementById('html-root');
        if (root) {
          if (dark) {
            root.classList.add('dark');
            root.classList.remove('light');
          } else {
            root.classList.add('light');
            root.classList.remove('dark');
          }
        }
      }, isDark);
      await sleep(800);
    };

    const verifyDomText = async (text, label) => {
      const found = await page.evaluate((t) => {
        if (document.body.innerText.includes(t)) return true;
        const inputs = Array.from(document.querySelectorAll('input, textarea'));
        return inputs.some((el) => (el.value || '').includes(t));
      }, text);
      if (found) {
        console.log(`  ✅ DOM Verification passed: "${text}" [${label}]`);
      } else {
        console.error(`  ❌ DOM Verification failed: "${text}" not found! [${label}]`);
        throw new Error(`DOM string missing: ${text}`);
      }
    };

    // =========================================================================
    // PART 1: UNIVERSAL A2UI STUDIO (LIGHT & DARK THEMES + IDEMPOTENCY)
    // =========================================================================
    console.log('\n======================================================');
    console.log('PART 1: TESTING UNIVERSAL A2UI STUDIO');
    console.log('======================================================');

    // Click A2UI tab in sidebar
    console.log('Navigating to Universal A2UI Studio (#tab-a2ui)...');
    await page.$eval('#tab-a2ui', (el) => el.click());
    await sleep(1200);

    // Verify initial load strings
    await verifyDomText('Universal A2UI Transpiler Engine', 'Studio Header');
    await verifyDomText('a2ui.surface.v1', 'Protocol Spec Code');
    await verifyDomText('Google Workspace Card v2', 'Dialect Google');
    await verifyDomText('Slack Block Kit', 'Dialect Slack');
    await verifyDomText('Teams v1.5', 'Dialect Teams');
    await verifyDomText('Web React Glassmorphic', 'Dialect Web');

    // 1. Light Mode Capture of Universal A2UI Studio
    console.log('\n--- Capturing Light Mode A2UI Studio ---');
    await setTheme(false);
    await page.evaluate(() => window.scrollTo(0, 0));
    await saveShot('light_07_a2ui_studio.png');
    await saveShot('light_a2ui_studio_overview.png');

    // 2. Dark Mode Capture of Universal A2UI Studio
    console.log('\n--- Capturing Dark Mode A2UI Studio ---');
    await setTheme(true);
    await page.evaluate(() => window.scrollTo(0, 0));
    await saveShot('dark_07_a2ui_studio.png');
    await saveShot('dark_a2ui_studio_overview.png');

    // 3. Test Template Preset Switching
    console.log('\n--- Testing A2UI Preset Templates ---');
    await page.$eval('#btn-tpl-pv', (el) => el.click());
    await sleep(800);
    await verifyDomText('FDA / EMA 15-Day Expedited Clock', 'PV Template Clock');

    await page.$eval('#btn-tpl-grid', (el) => el.click());
    await sleep(800);
    await verifyDomText('ALT (U/L)', 'Lab Grid Header');

    await page.$eval('#btn-tpl-dose', (el) => el.click());
    await sleep(800);
    await verifyDomText('Phase III Dose Titration & Toxicity Sign-Off', 'Dose Template');

    // 4. Test Double-Blind Mode Toggle
    console.log('\n--- Testing Double-Blind Unmasking Toggle ---');
    await page.$eval('#btn-toggle-unblind', (el) => el.click());
    await sleep(800);
    await verifyDomText('DSMB Mode (Unblinded)', 'Unblinded Mode Active');

    // Toggle back to blinded
    await page.$eval('#btn-toggle-unblind', (el) => el.click());
    await sleep(800);
    await verifyDomText('Site Monitor (Blinded)', 'Blinded Mode Restored');

    // 5. Test 21 CFR Part 11 JTI Nonce Execution & Replay Attack (HTTP 409 Conflict)
    console.log('\n--- Testing JTI Nonce Execution & Replay Attack Prevention ---');
    // First Execution (Valid)
    await page.$eval('#btn-test-action-first', (el) => el.click());
    await sleep(1000);
    await verifyDomText('VERIFIED (HTTP 200)', 'Action Completed Status');
    await verifyDomText('HTTP 200 OK (Signed & JTI Consumed)', 'History Success Entry');

    // Second Execution (Replay Attack with same JTI state token)
    await page.$eval('#btn-test-action-replay', (el) => el.click());
    await sleep(1000);
    await verifyDomText('BLOCKED (HTTP 409)', 'Replay Blocked 409 Message');
    await verifyDomText('HTTP 409 CONFLICT (Replay Blocked)', 'History 409 Entry');

    // Scroll replay console into view and capture screenshot
    await page.$eval('#view-a2ui-studio', (el) => el.scrollIntoView({ behavior: 'instant', block: 'end' }));
    await sleep(800);
    await saveShot('dark_a2ui_jti_409_replay_blocked.png');

    await setTheme(false);
    await sleep(800);
    await saveShot('light_a2ui_jti_409_replay_blocked.png');

    // Reset lock
    await page.$eval('#btn-a2ui-reset-jti', (el) => el.click());
    await sleep(800);

    // =========================================================================
    // PART 2: USER TRAINING & ONBOARDING HUB (STEP 6 INTEGRATION)
    // =========================================================================
    console.log('\n======================================================');
    console.log('PART 2: TESTING USER TRAINING HUB (STEP 6)');
    console.log('======================================================');

    console.log('Navigating to Training Hub (#tab-training)...');
    await page.$eval('#tab-training', (el) => el.click());
    await sleep(1000);

    // Set interactive mode and Step 6
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.trainingViewMode = 'interactive';
      state.setTrainingStep(6);
    });
    await sleep(1000);

    // Verify Step 6 DOM Strings
    await verifyDomText('Step 6: Universal A2UI Authoring & Transpilation', 'Step 6 Title');
    await verifyDomText('Omnichannel Transpiler & JTI Guard', 'Step 6 Badge');
    await verifyDomText('Dose Titration Surface: MK-3475-087', 'Step 6 Surface Title');
    await verifyDomText('Atomic Check-and-Set', 'Step 6 Atomic Nonce');

    // Capture Step 6 in Light Mode
    console.log('\n--- Capturing Light Mode Step 6 Training Screenshot ---');
    await setTheme(false);
    await page.evaluate(() => window.scrollTo(0, 0));
    await saveShot('light_training_07_a2ui_studio.png');

    // Capture Step 6 in Dark Mode
    console.log('\n--- Capturing Dark Mode Step 6 Training Screenshot ---');
    await setTheme(true);
    await page.evaluate(() => window.scrollTo(0, 0));
    await saveShot('dark_training_07_a2ui_studio.png');

    // Test carousel gallery slide 7 (Step 6)
    console.log('\n--- Capturing Carousel Gallery Slide for Step 6 ---');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.trainingViewMode = 'gallery';
      state.trainingGalleryIndex = 6; // Slide 7 (index 6: Step 6)
    });
    await sleep(1000);
    await verifyDomText('Step 6: Universal A2UI Studio & Omnichannel Transpiler', 'Carousel Slide 7 Title');
    await saveShot('dark_training_08_carousel_gallery.png');

    await setTheme(false);
    await sleep(800);
    await saveShot('light_training_08_carousel_gallery.png');

    console.log('\n🎉 ALL UNIVERSAL A2UI STUDIO & TRAINING SCREENSHOTS CAPTURED & VERIFIED SUCCESSFULLY!');
  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch (e) {}
  }
}

runA2UIE2ESuite().catch((err) => {
  console.error('❌ A2UI E2E Automation Error:', err);
  process.exit(1);
});
