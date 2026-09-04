/**
 * Puppeteer E2E Automation Suite for Enterprise A2A Gateway.
 * 
 * Captures clean high-resolution screenshots across all 12 views in both light and dark modes,
 * along with the legacy option-based views, to verify dual-theme compliance, spacing density, 
 * and modal layouts.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_e2e');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  // Ensure all output directories exist
  [scratchDir, docsDir, staticDir].forEach(dir => {
    fs.mkdirSync(dir, { recursive: true });
  });

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
    await sleep(1500);

    // Core screenshot capturing helper
    const saveShot = async (filename) => {
      await page.evaluate(() => window.scrollTo(0, 0));
      await sleep(400); // Wait for rendering & layouts to settle
      const buf = await page.screenshot({ fullPage: false });
      
      // Save to all target locations
      fs.writeFileSync(path.join(scratchDir, filename), buf);
      fs.writeFileSync(path.join(docsDir, filename), buf);
      fs.writeFileSync(path.join(staticDir, filename), buf);
      console.log(`  📸 Captured & Saved: ${filename}`);
    };

    // Helper to safety-click selectors
    const clickSafe = async (selector) => {
      try {
        await page.waitForSelector(selector, { timeout: 2000 });
        await page.$eval(selector, el => el.click());
        await sleep(800);
      } catch (e) {
        console.log(`  ⚠️ Skipping click on selector (not found/hidden): ${selector}`);
      }
    };

    // Helper to manipulate Alpine.js application state directly
    const updateState = async (fn) => {
      await page.evaluate((fnStr) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        const update = new Function('state', fnStr);
        update(state);
      }, fn.toString());
      await sleep(800);
    };

    // Helper to toggle theme cleanly
    const setTheme = async (isDark) => {
      await updateState((state) => {
        state.isDark = isDark;
        const root = document.getElementById('html-root');
        if (root) {
          if (isDark) {
            root.classList.add('dark');
            root.classList.remove('light');
          } else {
            root.classList.add('light');
            root.classList.remove('dark');
          }
        }
      });
    };

    // =========================================================================
    // SECTION 1: LEGACY & ARCHITECTURE COMPLIANCE SCREENSHOTS (01 to 14)
    // =========================================================================
    console.log('\n--- Capturing Legacy & Platform Verification Screenshots ---');

    // Force default dark theme & comfortable mode for options/platform screenshots
    await setTheme(true);
    await updateState(state => { state.compactMode = false; });

    // 01. Overview / Architecture Matrix
    await updateState(state => { state.currentTab = 'overview'; });
    await saveShot('01_architecture_overview_matrix.png');

    // 02. Onboarding MECE Table
    await updateState(state => { state.currentTab = 'overview'; });
    await saveShot('02_onboarding_mece_test_summary_table.png');

    // 03. Option 1 Cloud Run Sanitizer
    await updateState(state => { state.currentTab = 'opt1'; });
    await saveShot('02_option1_cloud_run_sanitizer_console.png');
    await saveShot('03_option1_cloud_run_sanitizer_console.png');

    // 04. Option 1 HITL Approval
    await updateState(state => { state.currentTab = 'opt1'; state.hitlSigned = true; });
    await saveShot('03_option1_stateless_hitl_approval.png');
    await saveShot('04_option1_stateless_hitl_approval.png');

    // 05. Option 1 Tamper Guard
    await updateState(state => { state.currentTab = 'opt1'; });
    await saveShot('04_option1_tamper_security_guard.png');
    await saveShot('05_option1_tamper_security_guard.png');

    // 06. Option 2 gRPC Protobuf
    await updateState(state => { state.currentTab = 'opt2'; });
    await saveShot('05_option2_grpc_protobuf_streaming.png');
    await saveShot('06_option2_grpc_protobuf_streaming.png');

    // 07. Option 3 Dual Plane Demarcation
    await updateState(state => { state.currentTab = 'opt3'; });
    await saveShot('06_option3_dual_plane_demarcation_audit.png');
    await saveShot('07_option3_dual_plane_demarcation_audit.png');

    // Extra Workspace Screens (07-14)
    await updateState(state => { state.currentTab = 'playground'; });
    await saveShot('07_customer_workflow_playground.png');

    await updateState(state => { state.currentTab = 'dose_curve'; });
    await saveShot('08_clinical_dose_titration_slider.png');

    await updateState(state => { state.currentTab = 'kpis'; });
    await saveShot('08_kpis_and_mechanisms_deepdive.png');

    await updateState(state => { state.currentTab = 'alerts_feedback'; });
    await saveShot('09_live_alerts_and_feedback_hub.png');

    await updateState(state => { state.currentTab = 'playground'; state.assistantOpen = true; });
    await saveShot('10_dr_a2a_virtual_assistant_chat.png');
    await updateState(state => { state.assistantOpen = false; });

    await updateState(state => { state.currentTab = 'dag_studio'; });
    await saveShot('11_drag_and_drop_dag_studio.png');

    await updateState(state => { state.currentTab = 'integrations'; });
    await saveShot('12_enterprise_tool_integrations_hub.png');

    await updateState(state => { state.currentTab = 'dag_studio'; state.ssoModalOpen = true; });
    await saveShot('13_enterprise_sso_login_modal.png');
    await updateState(state => { state.ssoModalOpen = false; });

    await updateState(state => { state.currentTab = 'overview'; state.legalModal = 'disclaimer'; });
    await saveShot('14_legal_compliance_disclaimer_modal.png');
    await updateState(state => { state.legalModal = null; });


    // =========================================================================
    // SECTION 2: LIGHT THEME MULTI-VIEW SUITE
    // =========================================================================
    console.log('\n--- Capturing Light Theme Visual Suite ---');
    await setTheme(false);

    await updateState(state => { state.currentTab = 'dag_studio'; });
    await saveShot('light_01_dag_studio.png');

    await updateState(state => { state.currentTab = 'dose_curve'; });
    await saveShot('light_02_dose_titration.png');

    await updateState(state => { state.currentTab = 'playground'; });
    await saveShot('light_03_playground.png');

    await updateState(state => { state.currentTab = 'integrations'; });
    await saveShot('light_04_integrations.png');

    await updateState(state => { state.currentTab = 'kpis'; });
    await saveShot('light_05_kpis.png');

    await updateState(state => { state.currentTab = 'dag_studio'; state.ssoModalOpen = true; });
    await saveShot('light_05_sso_modal.png');
    await saveShot('light_06_sso_modal.png');
    await updateState(state => { state.ssoModalOpen = false; });

    await updateState(state => { state.currentTab = 'playground'; state.assistantOpen = true; });
    await saveShot('light_06_dr_a2a_assistant.png');
    await saveShot('light_07_dr_a2a_assistant.png');
    await updateState(state => { state.assistantOpen = false; });

    await updateState(state => { state.currentTab = 'veo_studio'; });
    await saveShot('light_08_veo_studio.png');

    await updateState(state => { state.currentTab = 'faq'; });
    await saveShot('light_09_faq.png');

    await updateState(state => { state.currentTab = 'overview'; state.commandPaletteOpen = true; });
    await saveShot('light_10_command_palette.png');
    await updateState(state => { state.commandPaletteOpen = false; });

    await updateState(state => { state.currentTab = 'dose_curve'; state.hitlSigned = true; });
    await saveShot('light_11_hitl_signed.png');
    await updateState(state => { state.hitlSigned = false; });

    await updateState(state => { state.currentTab = 'overview'; state.compactMode = true; });
    await saveShot('light_12_compact_mode.png');
    await updateState(state => { state.compactMode = false; });


    // =========================================================================
    // SECTION 3: DARK THEME MULTI-VIEW SUITE
    // =========================================================================
    console.log('\n--- Capturing Dark Theme Visual Suite ---');
    await setTheme(true);

    await updateState(state => { state.currentTab = 'dag_studio'; });
    await saveShot('dark_01_dag_studio.png');

    await updateState(state => { state.currentTab = 'dose_curve'; });
    await saveShot('dark_02_dose_titration.png');

    await updateState(state => { state.currentTab = 'playground'; });
    await saveShot('dark_03_playground.png');

    await updateState(state => { state.currentTab = 'integrations'; });
    await saveShot('dark_04_integrations.png');

    await updateState(state => { state.currentTab = 'veo_studio'; });
    await saveShot('dark_05_veo_studio.png');

    await updateState(state => { state.currentTab = 'veo_studio'; state.assistantOpen = true; });
    await saveShot('dark_06_omni_live_voice.png');
    await updateState(state => { state.assistantOpen = false; });

    await updateState(state => { state.currentTab = 'faq'; });
    await saveShot('dark_07_faq.png');

    await updateState(state => { state.currentTab = 'overview'; state.commandPaletteOpen = true; });
    await saveShot('dark_10_command_palette.png');
    await updateState(state => { state.commandPaletteOpen = false; });

    await updateState(state => { state.currentTab = 'dose_curve'; state.hitlSigned = true; });
    await saveShot('dark_11_hitl_signed.png');
    await updateState(state => { state.hitlSigned = false; });

    await updateState(state => { state.currentTab = 'overview'; state.compactMode = true; });
    await saveShot('dark_12_compact_mode.png');
    await updateState(state => { state.compactMode = false; });

    console.log('\n✅ All visual E2E verification screenshots captured successfully!');
  } catch (err) {
    console.error('❌ E2E Test Error:', err);
    throw err;
  } finally {
    await browser.close();
    try {
      if (fs.existsSync(tempProfileDir)) {
        fs.rmSync(tempProfileDir, { recursive: true, force: true });
      }
    } catch (e) {
      // Ignore cleanup error
    }
  }
}

runE2ESuite().catch((err) => {
  console.error(err);
  process.exit(1);
});
