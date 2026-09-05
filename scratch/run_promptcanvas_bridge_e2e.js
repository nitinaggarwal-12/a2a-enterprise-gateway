/**
 * Puppeteer E2E Automation Suite for PromptCanvas ⟷ Enterprise A2A Gateway Visual Bridge.
 * 
 * Verifies and captures high-resolution screenshots across PromptCanvas Studio
 * and the User Training Carousel in both Dark and Light modes using Google Signed Chrome
 * with mandatory 800ms settling delays.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runPromptCanvasE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_promptcanvas');
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
    page.on('console', msg => console.log('  [Browser]', msg.text()));
    page.on('pageerror', err => console.log('  [Browser Error]', err.message));

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
      console.log(`🎨 TESTING ${theme.name.toUpperCase()} ACROSS PROMPTCANVAS STUDIO`);
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

        const alpineEl = document.querySelector('[x-data]');
        if (alpineEl && alpineEl._x_dataStack) {
          alpineEl._x_dataStack[0].isDark = isDark;
        }
      }, theme.isDark);
      await sleep(800);

      // 1. Navigate to PromptCanvas Studio Tab
      console.log('1. Navigating to PromptCanvas Visual Architecture Studio...');
      await page.$eval('#tab-promptcanvas-studio', el => el.click());
      await sleep(1000);

      // Verify DOM Text
      await verifyDomText('#view-promptcanvas-studio', 'PromptCanvas Visual Architecture & Draw.io Studio');
      await verifyDomText('#view-promptcanvas-studio', 'Interactive Architecture Topology');
      await verifyDomText('#view-promptcanvas-studio', 'SOVEREIGN BIOPHARMA VPC');

      // 2. Trigger 1-Click DAG Synthesis from Draw.io XML
      console.log('2. Compiling Draw.io Architecture to Live A2A Gateway DAG...');
      await page.$eval('#btn-compile-promptcanvas-dag', el => el.click());
      await sleep(1200);

      // Verify Compiled State
      await verifyDomText('#view-promptcanvas-studio', 'Synthesized A2A DAG Plan');
      await verifyDomText('#view-promptcanvas-studio', 'Compiled');

      // Trigger XML copy & export actions
      await page.$eval('#btn-copy-drawio-xml', el => el.click());
      await sleep(300);

      // Capture Top Section (Hero, SVG Viewport, Inspector)
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await sleep(500);
      await captureView(`${theme.prefix}promptcanvas_01_studio.png`, { fullPage: false });

      // 3. Scroll and capture Lower Section (Execution Plan & Raw Draw.io XML)
      console.log('3. Capturing DAG Plan and Draw.io XML details...');
      await page.evaluate(() => window.scrollTo({ top: 380, behavior: 'instant' }));
      await sleep(500);
      await captureView(`${theme.prefix}promptcanvas_02_compiled_dag.png`, { fullPage: false });

      // 4. Navigate to Gemini Training Hub Carousel
      console.log('4. Navigating to Training Carousel...');
      await page.$eval('#tab-training', el => el.click());
      await sleep(800);

      // Switch to Gallery mode
      console.log('5. Switching Training view mode to Gallery...');
      await page.$eval('#btn-mode-gallery', el => el.click());
      await sleep(800);

      // Set carousel index to 0 (PromptCanvas Slide)
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
      await sleep(1200);

      await verifyDomText('#training-gallery-carousel', 'Visual Architecture Studio: PromptCanvas ⟷ A2A Sovereign Bridge');
      await captureView(`${theme.prefix}training_12_promptcanvas.png`, { fullPage: false });
    }

    console.log('\n🎉 ALL PROMPTCANVAS BRIDGE SCREENSHOTS CAPTURED & VERIFIED SUCCESSFULLY!');
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

runPromptCanvasE2ESuite();
