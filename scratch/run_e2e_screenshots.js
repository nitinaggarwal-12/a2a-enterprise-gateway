/**
 * Puppeteer E2E Automation Suite for Enterprise A2A Enterprise Gateway.
 * 
 * Captures clean high-resolution screenshots across all views:
 * 1. Architecture Overview Matrix
 * 2. User Onboarding & MECE Test Summary Table + Evidence Gallery
 * 3. Option 1: Cloud Run Interceptor Gateway (Sanitizer & A2UI Artifact)
 * 4. Option 1: Stateless HITL Approval Callback & 21 CFR Part 11 Audit
 * 5. Option 1: Tamper Security Guard Alert
 * 6. Option 2: a2a.v1 gRPC Protobuf Contract & Streaming Thought Traces
 * 7. Option 3: Outside-In Dual-Plane Sovereign Execution & GE Workspace Delivery
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runE2ESuite() {
  const screenshotsDir = path.join(__dirname, 'screenshots_e2e');
  const staticScreenshotsDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  fs.mkdirSync(screenshotsDir, { recursive: true });
  fs.mkdirSync(staticScreenshotsDir, { recursive: true });

  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const tempProfileDir = path.join(__dirname, '.chrome_profile_' + Date.now());
  fs.mkdirSync(tempProfileDir, { recursive: true });

  console.log('🚀 Launching Puppeteer Headless Chrome...');
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
    await sleep(1200);

    // Helper to save to both scratch and static directory
    const saveShot = async (filename) => {
      await page.evaluate(() => window.scrollTo(0, 0));
      await sleep(300);
      const buf = await page.screenshot({ fullPage: false });
      fs.writeFileSync(path.join(screenshotsDir, filename), buf);
      fs.writeFileSync(path.join(staticScreenshotsDir, filename), buf);
    };

    // 1. Overview Matrix
    console.log('📸 Capturing 01_architecture_overview_matrix.png...');
    await sleep(800);
    await saveShot('01_architecture_overview_matrix.png');

    // 2. Onboarding & MECE Test Matrix
    console.log('Navigating to Onboarding & Test Matrix tab...');
    await page.$eval('#tab-onboarding', el => el.click());
    await sleep(1000);
    console.log('📸 Capturing 02_onboarding_mece_test_summary_table.png...');
    await saveShot('02_onboarding_mece_test_summary_table.png');

    // 3. Option 1 Sanitizer & A2UI Card
    console.log('Navigating to Option 1 tab...');
    await page.$eval('#tab-opt1', el => el.click());
    await sleep(800);
    await page.$eval('#btn-run-opt1', el => el.click());
    await sleep(1000);
    console.log('📸 Capturing 03_option1_cloud_run_sanitizer_console.png...');
    await saveShot('03_option1_cloud_run_sanitizer_console.png');

    // 4. Option 1 Approval Sign-off
    console.log('Simulating Medical Director Approval click...');
    await page.$eval('#btn-approve-opt1', el => el.click());
    await sleep(1000);
    console.log('📸 Capturing 04_option1_stateless_hitl_approval.png...');
    await saveShot('04_option1_stateless_hitl_approval.png');

    // 5. Option 1 Tamper Guard
    console.log('Testing Tamper Security Guard...');
    await page.$eval('#btn-tamper-opt1', el => el.click());
    await sleep(1000);
    console.log('📸 Capturing 05_option1_tamper_security_guard.png...');
    await saveShot('05_option1_tamper_security_guard.png');

    // 6. Option 2 gRPC Streaming
    console.log('Navigating to Option 2 tab...');
    await page.$eval('#tab-opt2', el => el.click());
    await sleep(800);
    await page.$eval('#btn-run-opt2', el => el.click());
    await sleep(3500);
    console.log('📸 Capturing 06_option2_grpc_protobuf_streaming.png...');
    await saveShot('06_option2_grpc_protobuf_streaming.png');

    // 7. Option 3 Dual Plane Demarcation
    console.log('Navigating to Option 3 tab...');
    await page.$eval('#tab-opt3', el => el.click());
    await sleep(800);
    await page.$eval('#btn-run-opt3', el => el.click());
    await sleep(1200);
    console.log('📸 Capturing 07_option3_dual_plane_demarcation_audit.png...');
    await saveShot('07_option3_dual_plane_demarcation_audit.png');

    // 8. Dedicated KPIs & Mechanism Deep-Dive
    console.log('Navigating to KPIs & Mechanism Deep-Dive tab...');
    await page.$eval('#tab-kpis', el => el.click());
    await sleep(800);
    console.log('Triggering live empirical socket benchmark...');
    await page.evaluate(() => {
      const btn = document.querySelector('button[x-text*="Benchmark"]') || document.querySelector('#tab-kpis');
      // trigger alpine runLiveBenchmark
      if (window.Alpine && document.querySelector('[x-data]')) {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        if (state && state.runLiveBenchmark) {
          state.runLiveBenchmark();
        }
      }
    });
    await sleep(2200);
    console.log('📸 Capturing 08_kpis_and_mechanisms_deepdive.png...');
    await saveShot('08_kpis_and_mechanisms_deepdive.png');

    console.log(' All 8 high-resolution screenshots successfully captured!');
  } catch (err) {
    console.error('E2E Test Error:', err);
    throw err;
  } finally {
    await browser.close();
  }
}

runE2ESuite().catch((err) => {
  console.error(err);
  process.exit(1);
});
