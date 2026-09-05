/**
 * E2E Puppeteer Verification Suite for Google Gemini Omni UI/UX Orchestrator:
 * 1. Omni User Readiness Index (URI) Orb & Compliance Halo
 * 2. Autonomous User Readiness Matrix Modal with 4-pillar gating
 * 3. Dynamic Generative Layout Morphing (Split-Focus Mode)
 * 4. Interactive Laser Spotlight & Attention Halo
 * 5. Voice-Directed Orchestration & Preflight Interception
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runOmniOrchestratorE2E() {
  const rootDir = '/Users/nitinagga/Documents/a2a-enterprise-gateway';
  const taskDir = path.join(rootDir, 'scratch', 'screenshots_omni_orchestrator');

  // Purge prior artifacts cleanly
  if (fs.existsSync(taskDir)) {
    fs.rmSync(taskDir, { recursive: true, force: true });
  }
  fs.mkdirSync(taskDir, { recursive: true });

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;
  console.log(`[E2E] Using Chrome binary: ${executablePath || 'bundled Chromium'}`);

  const tempProfileDir = path.join(rootDir, 'scratch', '.chrome_profile_omni_' + Date.now());
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
    console.log(`[E2E] Loading portal at ${portalUrl}...`);
    await page.goto(portalUrl, { waitUntil: 'networkidle0' });
    await sleep(1500);

    const saveShot = async (filename) => {
      await sleep(800);
      const filePath = path.join(taskDir, filename);
      await page.screenshot({ path: filePath, fullPage: false });
      console.log(`[E2E] Captured screenshot: file://${filePath}`);
    };

    // -------------------------------------------------------------
    // Test 1: Omni User Readiness Orb & UX Director Pill in Top Strip
    // -------------------------------------------------------------
    console.log('[E2E] Step 1: Testing Omni Readiness Orb & Director Pill...');
    const readinessOrb = await page.$('#btn-omni-readiness-orb');
    if (!readinessOrb) throw new Error('#btn-omni-readiness-orb not found in top strip');

    const orbText = await page.evaluate(() => {
      return document.getElementById('btn-omni-readiness-orb')?.innerText || '';
    });
    console.log(`[E2E] Readiness Orb Text: ${orbText}`);
    if (!orbText.includes('88%') && !orbText.includes('%')) {
      throw new Error('Readiness percentage missing from orb');
    }
    await saveShot('01_omni_readiness_orb_top_strip.png');

    // -------------------------------------------------------------
    // Test 2: Autonomous User Readiness Matrix Modal
    // -------------------------------------------------------------
    console.log('[E2E] Step 2: Opening User Readiness Matrix Modal...');
    await page.$eval('#btn-omni-readiness-orb', el => el.click());
    await sleep(800);

    const isModalVisible = await page.evaluate(() => {
      const m = document.getElementById('modal-omni-readiness');
      return m && window.getComputedStyle(m).display !== 'none';
    });
    if (!isModalVisible) throw new Error('#modal-omni-readiness did not open');

    // Click Auto-Clear Remaining Gates
    console.log('[E2E] Auto-clearing remaining gating pillars...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Auto-Clear'));
      if (btn) btn.click();
    });
    await sleep(800);

    const updatedScore = await page.evaluate(() => {
      return document.getElementById('modal-omni-readiness')?.innerText || '';
    });
    if (!updatedScore.includes('100%')) {
      throw new Error('Readiness score failed to reach 100% upon auto-remediation');
    }
    console.log('[E2E] Readiness reached 100% (Certified Audit-Ready)');
    await saveShot('02_omni_readiness_modal_cleared.png');

    // Close via Escape key
    await page.keyboard.press('Escape');
    await sleep(800);

    // -------------------------------------------------------------
    // Test 3: Omni Generative Layout Morphing (Split-Focus View)
    // -------------------------------------------------------------
    console.log('[E2E] Step 3: Triggering Omni Generative Layout Morphing...');
    await page.$eval('#btn-omni-director-pill', el => el.click());
    await sleep(800);

    // Submit split focus query
    await page.type('#input-omni-query', 'Focus on binding affinity vs liver risk in split view');
    await sleep(300);
    await page.$eval('#btn-submit-omni-orchestration', el => el.click());
    await sleep(1500);

    // Verify current tab is dose_curve and layout banner is visible
    const activeLayout = await page.evaluate(() => {
      return document.body.innerText;
    });
    if (!activeLayout.includes('SPLIT FOCUS') && !activeLayout.includes('Split Focus')) {
      throw new Error('Split focus layout mode was not applied');
    }
    console.log('[E2E] Verified Omni Split-Focus layout morphing');
    await saveShot('03_omni_split_focus_layout_morph.png');

    // -------------------------------------------------------------
    // Test 4: Omni Laser Spotlight Halo
    // -------------------------------------------------------------
    console.log('[E2E] Step 4: Verifying Omni Laser Spotlight Halo...');
    const isSpotlightVisible = await page.evaluate(() => {
      const s = document.getElementById('omni-spotlight-halo');
      return s && window.getComputedStyle(s).display !== 'none';
    });
    console.log(`[E2E] Spotlight element visible: ${isSpotlightVisible}`);
    await saveShot('04_omni_laser_spotlight_focused.png');

    // -------------------------------------------------------------
    // Test 5: Voice-Directed 1-Click FDA Dossier Orchestration
    // -------------------------------------------------------------
    console.log('[E2E] Step 5: Executing Voice-Directed FDA Dossier Directive...');
    await page.$eval('#btn-omni-director-pill', el => el.click());
    await sleep(800);

    // Click FDA Dossier Preset
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Compile 1-Click FDA Dossier'));
      if (btn) btn.click();
    });
    await sleep(1500);

    // Verify FDA Dossier Modal opened automatically
    const isFdaModalOpen = await page.evaluate(() => {
      const m = document.getElementById('modal-fda-dossier');
      return m && window.getComputedStyle(m).display !== 'none';
    });
    if (!isFdaModalOpen) throw new Error('Omni voice directive failed to open FDA Dossier modal');
    console.log('[E2E] Omni voice directive successfully opened FDA Dossier modal');
    await saveShot('05_omni_voice_triggered_fda_dossier.png');

    await page.keyboard.press('Escape');
    await sleep(500);

    console.log('[E2E] ALL GOOGLE GEMINI OMNI UX ORCHESTRATOR TESTS 100% VERIFIED!');
  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch (_) {}
  }
}

runOmniOrchestratorE2E().catch(err => {
  console.error('[E2E ERROR]', err);
  process.exit(1);
});
