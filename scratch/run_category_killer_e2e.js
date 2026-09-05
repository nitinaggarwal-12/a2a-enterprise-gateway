/**
 * Puppeteer E2E Automation Suite for Category-Defining Flagship Capabilities:
 * 1. 1-Click FDA eCTD 3.2.2 Automated Regulatory Dossier Compiler
 * 2. In-Silico 10,000 Digital Twin Patient Trial Simulator
 * 
 * Verifies and captures high-resolution screenshots across both flagship workspaces
 * and the User Training Carousel in both Dark and Light modes using Google Signed Chrome
 * with mandatory 800ms settling delays.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runCategoryKillerE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_category_killers');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  // Ensure output directories exist
  [scratchDir, docsDir, staticDir].forEach(dir => {
    fs.mkdirSync(dir, { recursive: true });
  });

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(__dirname, '.chrome_profile_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  console.log('🚀 Launching Puppeteer Headless Chrome (Google Signed)...');
  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    defaultViewport: { width: 1600, height: 1000 },
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
    await page.goto(portalUrl, { waitUntil: 'domcontentloaded' });
    await sleep(1500);

    // Screenshot capturing helper
    const captureView = async (filename, options = {}) => {
      const scratchPath = path.join(scratchDir, filename);
      const docsPath = path.join(docsDir, filename);
      const staticPath = path.join(staticDir, filename);

      await page.screenshot({ path: scratchPath, ...options });
      fs.copyFileSync(scratchPath, docsPath);
      fs.copyFileSync(scratchPath, staticPath);

      // Copy to agent artifacts directory if present
      const brainArtifactDir = '/Users/nitinagga/.gemini/jetski/brain/c2e35343-68c8-4b8c-b663-e40ccf567b66';
      if (fs.existsSync(brainArtifactDir)) {
        try { fs.copyFileSync(scratchPath, path.join(brainArtifactDir, filename)); } catch (e) {}
      }

      console.log(`  📸 Saved screenshot: ${filename}`);
    };

    // DOM text verification helper
    const verifyDomText = async (selector, expectedSubstring) => {
      const text = await page.$eval(selector, el => el.innerText || el.textContent);
      if (!text.toLowerCase().includes(expectedSubstring.toLowerCase())) {
        throw new Error(`DOM verification failed on ${selector}: Expected "${expectedSubstring}" but found "${text.slice(0, 80)}..."`);
      }
      console.log(`  ✓ DOM Verified [${selector}]: "${expectedSubstring}"`);
    };

    const themes = [
      { name: 'Dark Mode', isDark: true, prefix: 'dark_' },
      { name: 'Light Mode', isDark: false, prefix: 'light_' },
    ];

    for (const theme of themes) {
      console.log(`\n======================================================`);
      console.log(`🎨 TESTING ${theme.name.toUpperCase()} ACROSS FLAGSHIP WORKSPACES`);
      console.log(`======================================================`);

      // Set Theme in DOM and Alpine
      await page.evaluate((isDark) => {
        const root = document.documentElement;
        if (isDark) {
          root.classList.remove('light');
          root.classList.add('dark');
        } else {
          root.classList.remove('dark');
          root.classList.add('light');
        }
        window.__THEME__ = isDark ? 'dark' : 'light';

        // Sync with Alpine component
        const alpineEl = document.querySelector('[x-data]');
        if (alpineEl && alpineEl._x_dataStack) {
          alpineEl._x_dataStack[0].isDark = isDark;
        }
      }, theme.isDark);
      await sleep(800);

      // ==========================================
      // 1. FDA eCTD 3.2.2 REGULATORY COMPILER
      // ==========================================
      console.log('1. Navigating to FDA eCTD 3.2.2 Regulatory Compiler Studio...');
      await page.$eval('#tab-ectd-studio', el => el.click());
      await sleep(800);

      // Verify Initial DOM Text
      await verifyDomText('#view-ectd-studio', '1-Click FDA eCTD 3.2.2 Automated Regulatory Compiler');
      await verifyDomText('#view-ectd-studio', 'Form FDA 1571');
      await verifyDomText('#view-ectd-studio', '21 CFR § 11.70 Merkle Signature Ledger');

      // Trigger 1-Click Compilation
      console.log('2. Triggering 1-Click eCTD Compilation via Backend Router...');
      await page.$eval('#btn-compile-ectd', el => el.click());
      await sleep(1200);

      // Verify Compiled State
      await verifyDomText('#view-ectd-studio', 'FDA ESG Checksum Valid');
      await verifyDomText('#view-ectd-studio', '100% PASS');

      // Trigger Download & Copy Actions
      await page.$eval('#btn-download-ectd-bundle', el => el.click());
      await sleep(400);

      // Capture eCTD Compiler Studio
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await sleep(500);
      await captureView(`${theme.prefix}ectd_01_compiler.png`, { fullPage: false });

      // ==========================================
      // 2. IN-SILICO 10,000 DIGITAL TWIN SIMULATOR
      // ==========================================
      console.log('3. Navigating to In-Silico 10,000 Digital Twin Simulator...');
      await page.$eval('#tab-insilico-twin', el => el.click());
      await sleep(800);

      // Verify DOM Text
      await verifyDomText('#view-insilico-twin', 'In-Silico 10,000 Digital Twin Patient Trial Simulator');
      await verifyDomText('#view-insilico-twin', 'In-Silico Simulation Controls');
      await verifyDomText('#view-insilico-twin', 'Kaplan-Meier Curve');

      // Trigger In-Silico Swarm Simulation
      console.log('4. Executing 10,000 Agent Swarm Simulation with Vectorized PK/PD...');
      await page.$eval('#btn-run-insilico-sim', el => el.click());
      await sleep(1200);

      // Verify Simulation Results
      await verifyDomText('#view-insilico-twin', 'MTD_APPROVED');
      await verifyDomText('#view-insilico-twin', '24-Week Progression-Free Survival');

      // Capture In-Silico Simulation View
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await sleep(500);
      await captureView(`${theme.prefix}insilico_01_simulation.png`, { fullPage: false });

      // ==========================================
      // 3. USER TRAINING GALLERY CAROUSEL (Slide 1: eCTD)
      // ==========================================
      console.log('5. Navigating to Gemini Training Hub Carousel...');
      await page.$eval('#tab-training', el => el.click());
      await sleep(800);

      // Switch to Gallery mode
      console.log('6. Switching Training view mode to Gallery...');
      await page.$eval('#btn-mode-gallery', el => el.click());
      await sleep(800);

      // Set carousel index to 0 (FDA eCTD)
      await page.evaluate(() => {
        const alpineEl = document.querySelector('[x-data]');
        if (alpineEl && alpineEl._x_dataStack) {
          alpineEl._x_dataStack[0].trainingGalleryIndex = 0;
        }
      });
      await sleep(500);

      // Scroll to Training Carousel
      await page.evaluate(() => {
        const carousel = document.getElementById('training-gallery-carousel');
        if (carousel) carousel.scrollIntoView({ behavior: 'instant', block: 'start' });
      });

      // Force image reload
      await page.evaluate(() => {
        const img = document.querySelector('#training-gallery-carousel img');
        if (img) {
          const base = img.src.split('?')[0];
          img.src = base + '?t=' + Date.now();
        }
      });
      await sleep(1000);
      await verifyDomText('#training-gallery-carousel', 'Start-to-Finish Lifecycle Screenshot Carousel');
      await captureView(`${theme.prefix}training_10_flagships.png`, { fullPage: false });

      // ==========================================
      // 4. USER TRAINING GALLERY CAROUSEL (Slide 2: In-Silico 10K Digital Twins)
      // ==========================================
      console.log('7. Advancing Training Carousel to Slide 2 (In-Silico 10K Digital Twins)...');
      await page.evaluate(() => {
        const alpineEl = document.querySelector('[x-data]');
        if (alpineEl && alpineEl._x_dataStack) {
          alpineEl._x_dataStack[0].trainingGalleryIndex = 1;
        }
      });
      await sleep(500);
      await page.evaluate(() => {
        const img = document.querySelector('#training-gallery-carousel img');
        if (img) {
          const base = img.src.split('?')[0];
          img.src = base + '?t=' + Date.now();
        }
      });
      await sleep(1000);
      await verifyDomText('#training-gallery-carousel', 'Flagship: In-Silico 10,000 Digital Twin Patient Trial Simulator');
      await captureView(`${theme.prefix}training_11_insilico_twin.png`, { fullPage: false });
    }

    console.log('\n🎉 ALL FLAGSHIP CATEGORY KILLER SCREENSHOTS CAPTURED & VERIFIED SUCCESSFULLY!');
    process.exit(0);

  } catch (err) {
    console.error('❌ E2E Automation Failure:', err);
    process.exit(1);
  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch (e) {}
  }
}

runCategoryKillerE2ESuite();
