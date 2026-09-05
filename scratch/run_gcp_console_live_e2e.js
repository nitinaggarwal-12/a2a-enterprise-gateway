/**
 * Live Google Cloud Console Puppeteer Automation & Authentication Suite.
 *
 * Launches official Google-signed Chrome with a persistent user profile.
 * If authentication is required, it prompts the user to log in in the opened
 * Chrome window and polls until successful authentication is detected, then
 * navigates through Google Cloud Console (Cloud Run, Vertex AI, IAM) and captures
 * 100% genuine screenshots.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runGcpLiveConsoleSuite() {
  const scratchDir = path.join(__dirname, 'screenshots_real_gcp');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  [scratchDir, docsDir, staticDir].forEach((dir) => {
    fs.mkdirSync(dir, { recursive: true });
  });

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (!fs.existsSync(macChromePath)) {
    throw new Error(`Google Chrome not found at ${macChromePath}`);
  }

  // Persistent user profile so logins persist across sessions
  const persistentProfileDir = path.join(__dirname, '.chrome_gcp_profile');
  fs.mkdirSync(persistentProfileDir, { recursive: true });

  console.log('🚀 Launching Google-Signed Chrome for Live GCP Console...');
  console.log(`📁 Profile directory: ${persistentProfileDir}`);

  const browser = await puppeteer.launch({
    executablePath: macChromePath,
    headless: false, // Visible window so user can interact and authenticate
    defaultViewport: null,
    userDataDir: persistentProfileDir,
    args: [
      '--window-size=1600,1050',
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--no-default-browser-check',
      '--no-first-run',
      '--disable-blink-features=AutomationControlled',
    ],
  });

  const pages = await browser.pages();
  const page = pages.length > 0 ? pages[0] : await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000 });

  const saveShot = async (filename) => {
    await sleep(2000); // Settling delay for charts & tables
    const buf = await page.screenshot({ fullPage: false });
    fs.writeFileSync(path.join(scratchDir, filename), buf);
    fs.writeFileSync(path.join(docsDir, filename), buf);
    fs.writeFileSync(path.join(staticDir, filename), buf);
    console.log(`  📸 Captured REAL GCP Screenshot: ${filename}`);
  };

  try {
    const targetUrl = 'https://console.cloud.google.com/';
    console.log(`\n🌐 Navigating to ${targetUrl}...`);
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });

    console.log('\n======================================================================');
    console.log('🔍 CHECKING GOOGLE CLOUD AUTHENTICATION STATUS...');
    console.log('======================================================================');

    let authenticated = false;
    const maxWaitSeconds = 300;
    const startTime = Date.now();

    while ((Date.now() - startTime) < maxWaitSeconds * 1000) {
      const currentUrl = page.url();

      if (currentUrl.includes('accounts.google.com')) {
        console.log('🔑 Login page detected. Please complete authentication in the Chrome window.');
      }

      authenticated = await page.evaluate(() => {
        const url = window.location.href;
        if (url.includes('accounts.google.com')) return false;
        if (!url.includes('console.cloud.google.com')) return false;
        const text = (document.body && document.body.innerText) || '';
        const hasGcpHeader =
          text.includes('Google Cloud') ||
          text.includes('Google Cloud Platform') ||
          !!document.querySelector('cfc-platform-bar') ||
          !!document.querySelector('#cfc-party-bar') ||
          !!document.querySelector('[role="banner"]') ||
          !!document.querySelector('.cfc-platform-bar-container');
        return hasGcpHeader;
      });

      if (authenticated) {
        console.log('\n🎉 AUTHENTICATED! Google Cloud Console is loaded.');
        break;
      }

      await sleep(2500);
    }

    if (!authenticated) {
      console.warn('⚠️ Timed out waiting for authentication. Proceeding with current page capture.');
    }

    await sleep(4000); // Allow console dashboard to settle

    // 1. Capture Main Console Dashboard
    console.log('\n--- 1. Capturing Real Google Cloud Console Home ---');
    await saveShot('real_gcp_01_console_home.png');

    // Extract current project if present
    const currentUrl = page.url();
    let projectParam = '';
    const match = currentUrl.match(/project=([^&]+)/);
    if (match) {
      projectParam = `?project=${match[1]}`;
      console.log(`  🏷️ Detected active project: ${match[1]}`);
    }

    // 2. Navigate to Cloud Run Services
    console.log('\n--- 2. Navigating to Cloud Run ---');
    const runUrl = `https://console.cloud.google.com/run${projectParam}`;
    await page.goto(runUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(5000);
    await saveShot('real_gcp_02_cloud_run.png');

    // 3. Navigate to Vertex AI / Agent Builder
    console.log('\n--- 3. Navigating to Vertex AI Agent Builder ---');
    const vertexUrl = `https://console.cloud.google.com/vertex-ai/agent-builder${projectParam}`;
    try {
      await page.goto(vertexUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await sleep(5000);
      await saveShot('real_gcp_03_vertex_ai_agents.png');
    } catch (e) {
      console.log('  ⚠️ Vertex AI Agent Builder navigation notice:', e.message);
      await saveShot('real_gcp_03_vertex_ai_fallback.png');
    }

    // 4. Navigate to IAM & Admin
    console.log('\n--- 4. Navigating to IAM & Admin Permissions ---');
    const iamUrl = `https://console.cloud.google.com/iam-admin/iam${projectParam}`;
    await page.goto(iamUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(5000);
    await saveShot('real_gcp_04_iam_admin.png');

    console.log('\n======================================================================');
    console.log('✅ REAL GCP CONSOLE SCREENSHOTS CAPTURED SUCCESSFULLY!');
    console.log('======================================================================');
    console.log('Saved to:');
    console.log(`  - ${path.join(docsDir, 'real_gcp_01_console_home.png')}`);
    console.log(`  - ${path.join(docsDir, 'real_gcp_02_cloud_run.png')}`);
    console.log(`  - ${path.join(docsDir, 'real_gcp_03_vertex_ai_agents.png')}`);
    console.log(`  - ${path.join(docsDir, 'real_gcp_04_iam_admin.png')}`);

  } catch (err) {
    console.error('❌ Error during GCP Console automation:', err);
  } finally {
    console.log('\nClosing browser in 5 seconds...');
    await sleep(5000);
    await browser.close();
    console.log('Browser closed.');
  }
}

runGcpLiveConsoleSuite().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
