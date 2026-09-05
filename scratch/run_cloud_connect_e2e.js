/**
 * Puppeteer E2E Automation Suite for Cloud Connect & Enterprise Onboarding Hub.
 * 
 * Verifies and captures high-resolution screenshots across Cloud Connect Hub
 * and the User Training Carousel in both Dark and Light modes using Google Signed Chrome
 * with mandatory 800ms settling delays.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runCloudConnectE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_cloud_connect');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  // Ensure output directories exist
  [scratchDir, docsDir, staticDir].forEach(dir => {
    fs.mkdirSync(dir, { recursive: true });
  });

  // Purge target run folder before execution
  [scratchDir, docsDir, staticDir].forEach(dir => {
    const files = fs.readdirSync(dir);
    files.forEach(f => {
      if (f.includes('training_09_')) {
        try { fs.unlinkSync(path.join(dir, f)); } catch (e) {}
      }
    });
  });
  console.log('🧹 Purged stale training_09 screenshots across all output directories.');

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
      console.log(`🎨 TESTING ${theme.name.toUpperCase()} ACROSS CLOUD CONNECT HUB`);
      console.log(`======================================================`);

      // Set Theme
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
      }, theme.isDark);
      await sleep(800);

      // 1. Navigate to Cloud Connect Tab
      console.log('1. Navigating to Cloud Connect & Onboarding Hub...');
      await page.$eval('#tab-cloud-connect', el => el.click());
      await sleep(800);

      // Verify DOM Text
      await verifyDomText('#view-cloud-connect', 'Enterprise Cloud Connect & Sovereign Onboarding Hub');
      await verifyDomText('#view-cloud-connect', 'Self-Service Architecture Matchmaker');
      await verifyDomText('#view-cloud-connect', 'Infrastructure-as-Code');

      // 2. Trigger Matchmaker & IaC Generation
      console.log('2. Computing Optimal Architecture & Generating IaC...');
      await page.$eval('#btn-run-matchmaker', el => el.click());
      await sleep(800);
      await page.$eval('#btn-copy-iac', el => el.click());
      await sleep(400);

      // Capture Top Section (Hero, Matchmaker, IaC)
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await sleep(500);
      await captureView(`${theme.prefix}cloud_connect_01_onboarding.png`, { fullPage: false });

      // 3. Trigger Real-Time Diagnostics & CDISC Preflight & Webhook
      console.log('3. Running Live Diagnostics & CDISC Preflight...');
      await page.$eval('#btn-run-diag-inner', el => el.click());
      await sleep(1000);

      await page.$eval('#btn-run-cdisc-preflight', el => el.click());
      await sleep(800);
      await verifyDomText('#view-cloud-connect', 'Preflight Certificate Issued');

      console.log('4. Dispatching In-Situ Webhook & Approving Card...');
      await page.$eval('#btn-dispatch-webhook', el => el.click());
      await sleep(800);
      await page.$eval('#btn-approve-webhook-card', el => el.click());
      await sleep(500);
      await verifyDomText('#view-cloud-connect', 'Signed & Validated');

      // Scroll to Diagnostics & Preflight & Webhook Section
      await page.evaluate(() => window.scrollTo({ top: 680, behavior: 'instant' }));
      await sleep(800);
      await captureView(`${theme.prefix}cloud_connect_02_diagnostics.png`, { fullPage: false });

      // 4. Navigate to Gemini Training Hub and View the New Onboarding Slide
      console.log('5. Navigating to Gemini Training Hub Carousel...');
      await page.$eval('#tab-training', el => el.click());
      await sleep(800);

      // Switch to Gallery mode to reveal the screenshot carousel
      console.log('6. Switching Training view mode to Gallery...');
      await page.$eval('#btn-mode-gallery', el => el.click());
      await sleep(800);

      // Scroll to Training Carousel
      await page.evaluate(() => {
        const carousel = document.getElementById('training-gallery-carousel');
        if (carousel) carousel.scrollIntoView({ behavior: 'instant', block: 'start' });
      });
      // Ensure image is loaded cleanly without stale cache
      await page.evaluate(() => {
        const img = document.querySelector('#training-gallery-carousel img');
        if (img) {
          const base = img.src.split('?')[0];
          img.src = base + '?t=' + Date.now();
        }
      });
      await sleep(1500);

      // Verify DOM Text in Training Carousel
      await verifyDomText('#training-gallery-carousel', 'Start-to-Finish Lifecycle Screenshot Carousel');

      // Capture Training Hub with new onboarding slide displayed
      await captureView(`${theme.prefix}training_09_cloud_connect.png`, { fullPage: false });
    }

    console.log('\n🎉 ALL CLOUD CONNECT & ONBOARDING HUB SCREENSHOTS CAPTURED & VERIFIED SUCCESSFULLY!');
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

runCloudConnectE2ESuite();
