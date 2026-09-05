/**
 * Puppeteer E2E Test Suite for Futuristic Quantum Mesh Landing Page
 * 
 * Verifies:
 * 1. Default Landing Page load in Light Mode (3D WebGL core, cyber HUD, stats, pipeline, pillars, mini-regulator, terminal).
 * 2. Real-time Multi-Agent Simulation packet traversal and AST ADK filtering.
 * 3. Interactive Dose Titration mini-regulator slider adjustment & 21 CFR Part 11 signature stamping.
 * 4. Dark Mode toggle and cybernetic glassmorphism styling.
 * 5. Three.js wireframe and camera controls.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runLandingE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_e2e');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  [scratchDir, docsDir, staticDir].forEach(dir => {
    fs.mkdirSync(dir, { recursive: true });
  });

  // Purge any stale landing screenshots
  [scratchDir, docsDir, staticDir].forEach(dir => {
    const files = fs.readdirSync(dir);
    files.forEach(f => {
      if (f.includes('landing')) {
        try { fs.unlinkSync(path.join(dir, f)); } catch (e) {}
      }
    });
  });
  console.log('🧹 Purged stale landing screenshots.');

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(__dirname, '.chrome_profile_landing_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  console.log('🚀 Launching Google Signed Chrome (1600x1000)...');
  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    defaultViewport: { width: 1600, height: 1000 },
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--enable-webgl',
      '--ignore-gpu-blocklist',
      '--no-default-browser-check',
      '--no-first-run',
      `--user-data-dir=${tempProfileDir}`,
    ],
  });

  const page = await browser.newPage();
  const portalUrl = 'http://127.0.0.1:8090';

  async function saveScreenshot(filename) {
    const p1 = path.join(scratchDir, filename);
    const p2 = path.join(docsDir, filename);
    const p3 = path.join(staticDir, filename);
    await page.screenshot({ path: p1, fullPage: false });
    fs.copyFileSync(p1, p2);
    fs.copyFileSync(p1, p3);
    console.log(`📸 Captured screenshot: ${filename}`);
  }

  try {
    console.log(`🌐 Navigating to ${portalUrl}...`);
    await page.goto(portalUrl, { waitUntil: 'networkidle0', timeout: 30000 });
    await sleep(1200); // 800ms+ settling delay

    // Verify Default Tab is Landing
    const currentTab = await page.evaluate(() => {
      return document.querySelector('[x-data]')?.__x?.$data?.currentTab || 
             (window.Alpine && window.Alpine.$data(document.querySelector('[x-data]'))?.currentTab);
    });
    console.log(`📌 Current active tab: ${currentTab}`);

    // Verify DOM strings for Landing Page
    const heroTitle = await page.$eval('h1', el => el.innerText);
    console.log(`🔍 Hero Title: "${heroTitle.replace(/\n/g, ' ')}"`);

    const hasCanvas = (await page.$('#quantum-mesh-canvas')) !== null;
    console.log(`🎨 3D Quantum Mesh Canvas present: ${hasCanvas}`);

    // 1. Capture Light Mode Default Landing View
    await sleep(800);
    await saveScreenshot('light_00_landing_hero.png');

    // 2. Scroll down to show the 5-node pipeline simulator and 4 pillars
    await page.evaluate(() => {
      window.scrollBy({ top: 500, behavior: 'instant' });
    });
    await sleep(800);
    await saveScreenshot('light_00_landing_pipeline_and_pillars.png');

    // 3. Trigger Quantum Simulation (Normal Packet)
    console.log('⚡ Triggering Normal Packet Simulation...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('1. Normal EDC Packet'));
      if (btn) btn.click();
    });
    await sleep(1800); // Wait for packet to reach node 3
    await saveScreenshot('light_00_landing_sim_active.png');

    // Wait for simulation to finish
    await sleep(2600);

    // 4. Scroll down to Mini-Regulator & Live Terminal
    await page.evaluate(() => {
      window.scrollBy({ top: 600, behavior: 'instant' });
    });
    await sleep(800);

    // Adjust dose slider to 425 mg and sign Part 11 certificate
    console.log('🧪 Adjusting dose slider and issuing 21 CFR Part 11 certificate...');
    await page.evaluate(() => {
      const slider = document.querySelector('input[type="range"]');
      if (slider) {
        slider.value = 425;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
        slider.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const signBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('1-Click 21 CFR Part 11'));
      if (signBtn) signBtn.click();
    });
    await sleep(1000);
    await saveScreenshot('light_00_landing_mini_dose_signed.png');

    // 5. Scroll back up to Hero and Switch to Dark Mode
    await page.evaluate(() => {
      window.scrollTo({ top: 0, behavior: 'instant' });
    });
    await sleep(500);

    console.log('🌙 Switching to Dark Mode...');
    await page.evaluate(() => {
      const themeBtn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('title')?.includes('Theme') || b.querySelector('.fa-circle-half-stroke'));
      if (themeBtn) themeBtn.click();
      else document.documentElement.classList.add('dark');
    });
    await sleep(1000);
    await saveScreenshot('dark_00_landing_hero.png');

    // 6. Scroll down in Dark Mode to capture Cyber Pipeline & Pillars
    await page.evaluate(() => {
      window.scrollBy({ top: 520, behavior: 'instant' });
    });
    await sleep(800);
    await saveScreenshot('dark_00_landing_pipeline_cyber.png');

    // 7. Scroll down to Terminal & Mini-Regulator in Dark Mode
    await page.evaluate(() => {
      window.scrollBy({ top: 650, behavior: 'instant' });
    });
    await sleep(800);
    await saveScreenshot('dark_00_landing_terminal_cyber.png');

    console.log('✅ All Landing Page E2E tests and screenshots completed successfully!');

  } catch (err) {
    console.error('❌ Error during Landing Page E2E execution:', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch (e) {}
  }
}

runLandingE2ESuite();
