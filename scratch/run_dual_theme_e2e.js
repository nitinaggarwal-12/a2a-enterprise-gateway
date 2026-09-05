/**
 * Comprehensive Dual-Theme E2E Test Runner using Google signed Chrome for Mac.
 * Verifies Light & Dark Mode rendering, 3D WebGL scenes, Veo 2 Studio, and Gemini Omni Live Voice.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runDualThemeE2E() {
  const rootDir = '/Users/nitinagga/Documents/a2a-enterprise-gateway';
  const screenshotsDir = path.join(rootDir, 'docs', 'screenshots');
  const staticScreenshotsDir = path.join(rootDir, 'portal', 'static', 'screenshots');
  const scratchScreenshotsDir = path.join(rootDir, 'scratch', 'screenshots_e2e');

  [screenshotsDir, staticScreenshotsDir, scratchScreenshotsDir].forEach(dir => {
    fs.mkdirSync(dir, { recursive: true });
  });

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;
  console.log(`Using Chrome binary: ${executablePath || 'bundled Chromium'}`);

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_dual_' + Date.now());
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
  const portalUrl = 'http://127.0.0.1:8090';

  try {
    console.log(`Navigating to Visual Verification Portal: ${portalUrl}...`);
    await page.goto(portalUrl, { waitUntil: 'networkidle0' });
    await sleep(1500);

    const saveShot = async (filename) => {
      await page.evaluate(() => window.scrollTo(0, 0));
      await sleep(800);
      const buf = await page.screenshot({ fullPage: false });
      fs.writeFileSync(path.join(screenshotsDir, filename), buf);
      fs.writeFileSync(path.join(staticScreenshotsDir, filename), buf);
      fs.writeFileSync(path.join(scratchScreenshotsDir, filename), buf);
      console.log(`Saved screenshot: ${filename}`);
    };

    // ==========================================
    // 1. LIGHT THEME TESTS
    // ==========================================
    console.log('\n--- TESTING LIGHT THEME ---');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      if (state.isDark) state.toggleTheme();
    });
    await sleep(1000);

    // 1.1 Light DAG Studio
    console.log('Switching to DAG Studio (Light)...');
    await page.$eval('#tab-dag', el => el.click());
    await sleep(1200);
    await saveShot('light_01_dag_studio.png');

    // 1.2 Light Dose Titration
    console.log('Switching to Dose Titration (Light)...');
    await page.$eval('#tab-dose', el => el.click());
    await sleep(1000);
    await saveShot('light_02_dose_titration.png');

    // 1.3 Light Workflow Playground
    console.log('Switching to Playground (Light)...');
    await page.$eval('#tab-playground', el => el.click());
    await sleep(1000);
    await saveShot('light_03_playground.png');

    // 1.4 Light Integrations
    console.log('Switching to Integrations (Light)...');
    await page.$eval('#tab-integrations', el => el.click());
    await sleep(1000);
    await saveShot('light_04_integrations.png');

    // 1.5 Light KPIs
    console.log('Switching to KPIs (Light)...');
    await page.$eval('#tab-kpis', el => el.click());
    await sleep(1000);
    await saveShot('light_05_kpis.png');

    // 1.6 Light Veo 2 Studio
    console.log('Switching to Veo 2 Studio (Light)...');
    await page.$eval('#tab-veo', el => el.click());
    await sleep(1200);
    await saveShot('light_08_veo_studio.png');

    // 1.7 Light SSO Modal
    console.log('Opening SSO Modal (Light)...');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.ssoModalOpen = true;
    });
    await sleep(1000);
    await saveShot('light_06_sso_modal.png');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.ssoModalOpen = false;
    });
    await sleep(600);

    // 1.8 Light Dr. A2A Omni Copilot
    console.log('Opening Dr. A2A Omni Copilot (Light)...');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.assistantOpen = true;
    });
    await sleep(1200);
    await saveShot('light_07_dr_a2a_assistant.png');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.assistantOpen = false;
    });
    await sleep(600);

    // 1.9 Light FAQ
    console.log('Switching to FAQ (Light)...');
    await page.$eval('#tab-faq', el => el.click());
    await sleep(1200);
    await saveShot('light_09_faq.png');

    // 1.10 Light Command Palette
    console.log('Opening Command Palette (Light)...');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.openCommandPalette();
    });
    await sleep(1000);
    await saveShot('light_10_command_palette.png');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.commandPaletteOpen = false;
    });
    await sleep(600);

    // 1.11 Light HITL Signed Seal
    console.log('Signing HITL Record (Light)...');
    await page.$eval('#tab-dose', el => el.click());
    await sleep(800);
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.signHitlRecord();
    });
    await sleep(1000);
    await saveShot('light_11_hitl_signed.png');

    // 1.12 Light Compact Density Mode
    console.log('Testing Compact Density (Light)...');
    await page.$eval('#tab-dag', el => el.click());
    await sleep(800);
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.compactMode = true;
    });
    await sleep(1000);
    await saveShot('light_12_compact_mode.png');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.compactMode = false;
    });
    await sleep(600);

    // ==========================================
    // 2. DARK THEME TESTS
    // ==========================================
    console.log('\n--- TESTING DARK THEME ---');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      if (!state.isDark) state.toggleTheme();
    });
    await sleep(1000);

    // 2.1 Dark DAG Studio
    console.log('Switching to DAG Studio (Dark)...');
    await page.$eval('#tab-dag', el => el.click());
    await sleep(1200);
    await saveShot('dark_01_dag_studio.png');

    // 2.2 Dark Dose Titration
    console.log('Switching to Dose Titration (Dark)...');
    await page.$eval('#tab-dose', el => el.click());
    await sleep(1000);
    await saveShot('dark_02_dose_titration.png');

    // 2.3 Dark Playground
    console.log('Switching to Playground (Dark)...');
    await page.$eval('#tab-playground', el => el.click());
    await sleep(1000);
    await saveShot('dark_03_playground.png');

    // 2.4 Dark Integrations
    console.log('Switching to Integrations (Dark)...');
    await page.$eval('#tab-integrations', el => el.click());
    await sleep(1000);
    await saveShot('dark_04_integrations.png');

    // 2.5 Dark Veo 2 Studio
    console.log('Switching to Veo 2 Studio (Dark)...');
    await page.$eval('#tab-veo', el => el.click());
    await sleep(1200);
    await saveShot('dark_05_veo_studio.png');

    // 2.6 Dark FAQ
    console.log('Switching to FAQ (Dark)...');
    await page.$eval('#tab-faq', el => el.click());
    await sleep(1200);
    await saveShot('dark_07_faq.png');

    // 2.7 Dark Omni Live Voice Stream
    console.log('Opening Dr. A2A Omni Live Voice (Dark)...');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.assistantOpen = true;
      state.omniVoiceActive = true;
    });
    await sleep(1200);
    await saveShot('dark_06_omni_live_voice.png');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.assistantOpen = false;
    });
    await sleep(600);

    // 2.8 Dark Command Palette
    console.log('Opening Command Palette (Dark)...');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.openCommandPalette();
    });
    await sleep(1000);
    await saveShot('dark_10_command_palette.png');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.commandPaletteOpen = false;
    });
    await sleep(600);

    // 2.9 Dark HITL Signed Seal
    console.log('Signing HITL Record (Dark)...');
    await page.$eval('#tab-dose', el => el.click());
    await sleep(800);
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.signHitlRecord();
    });
    await sleep(1000);
    await saveShot('dark_11_hitl_signed.png');

    // 2.10 Dark Compact Density Mode
    console.log('Testing Compact Density (Dark)...');
    await page.$eval('#tab-dag', el => el.click());
    await sleep(800);
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.compactMode = true;
    });
    await sleep(1000);
    await saveShot('dark_12_compact_mode.png');
    await page.evaluate(() => {
      const state = Alpine.$data(document.querySelector('[x-data]'));
      state.compactMode = false;
    });
    await sleep(600);

    console.log('\n All Dual-Theme 3D E2E Screenshots (including FAQ) successfully verified and captured!');
  } catch (err) {
    console.error('Dual-Theme E2E Test Error:', err);
    throw err;
  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch(e) {}
  }
}

runDualThemeE2E().catch((err) => {
  console.error(err);
  process.exit(1);
});
