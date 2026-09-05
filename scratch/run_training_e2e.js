/**
 * Puppeteer E2E Automation Suite for Gemini Enterprise User Training & Onboarding.
 * 
 * Captures clean high-resolution screenshots across all 5 training steps in both
 * dark and light modes, along with the interactive 21 CFR Part 11 electronic seal
 * and the visual carousel gallery.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runTrainingE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_e2e');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  // Ensure output directories exist
  [scratchDir, docsDir, staticDir].forEach(dir => {
    fs.mkdirSync(dir, { recursive: true });
  });

  // Programmatically purge stale training screenshots
  [scratchDir, docsDir, staticDir].forEach(dir => {
    const files = fs.readdirSync(dir);
    files.forEach(f => {
      if (f.includes('training')) {
        try { fs.unlinkSync(path.join(dir, f)); } catch (e) {}
      }
    });
  });
  console.log('🧹 Purged stale training screenshots across all output directories.');

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
    const saveShot = async (filename) => {
      await page.evaluate(() => window.scrollTo(0, 0));
      await sleep(800); // 800ms settling delay per protocol
      const buf = await page.screenshot({ fullPage: false });
      
      fs.writeFileSync(path.join(scratchDir, filename), buf);
      fs.writeFileSync(path.join(docsDir, filename), buf);
      fs.writeFileSync(path.join(staticDir, filename), buf);
      console.log(`  📸 Captured & Saved: ${filename}`);
    };

    // Helper to toggle theme cleanly
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

    // Step navigation helper
    const setStep = async (step) => {
      await page.evaluate((s) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.currentTab = 'training';
        state.trainingViewMode = 'interactive';
        state.setTrainingStep(s);
      }, step);
      await sleep(800);
    };

    // Set view mode helper
    const setViewMode = async (mode) => {
      await page.evaluate((m) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.currentTab = 'training';
        state.trainingViewMode = m;
      }, mode);
      await sleep(800);
    };

    // Set registration console mode helper
    const setRegistrationMode = async (mode) => {
      await page.evaluate((m) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.trainingRegistrationMode = m;
      }, mode);
      await sleep(800);
    };

    // Set GCP Console sub-tab helper
    const setGcpTab = async (tab) => {
      await page.evaluate((t) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.trainingGcpConsoleTab = t;
      }, tab);
      await sleep(800);
    };

    // Register extension helper
    const registerExt = async () => {
      await page.evaluate(() => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.registerExtension();
      });
      await sleep(800);
    };

    // Approve chat helper
    const approveChat = async () => {
      await page.evaluate(() => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.approveTrainingChat();
      });
      await sleep(800);
    };

    // Reset chat helper
    const resetChat = async (dose = 300) => {
      await page.evaluate((d) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.resetTrainingChat();
        state.trainingSliderDose = d;
      }, dose);
      await sleep(800);
    };

    // Helper to verify DOM text including inputs
    const verifyDomText = async (text, label) => {
      const found = await page.evaluate((t) => {
        if (document.body.innerText.includes(t)) return true;
        const inputs = Array.from(document.querySelectorAll('input, textarea'));
        return inputs.some(el => (el.value || '').includes(t));
      }, text);
      if (found) {
        console.log(`  ✅ DOM Verification passed: "${text}" [${label}]`);
      } else {
        console.error(`  ❌ DOM Verification failed: "${text}" not found! [${label}]`);
        throw new Error(`DOM string missing: ${text}`);
      }
    };

    // Navigate to Training Hub via DOM click
    console.log('\n--- Switching to Gemini Training Hub Tab ---');
    await page.$eval('#tab-training', el => el.click());
    await sleep(1000);

    // =========================================================================
    // SECTION 1: DARK THEME CAPTURES (Steps 1 to 5 + Approved + Carousel)
    // =========================================================================
    console.log('\n--- Capturing Dark Mode Gemini Enterprise Training Screenshots ---');
    await setTheme(true);

    // Step 1: Protocol Discovery & Capabilities
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(1);
    await verifyDomText('Step 1: Protocol Discovery & Capabilities', 'Dark Step 1 Title');
    await verifyDomText('Universal A2A v1.0.0 Protocol', 'Dark Step 1 Checklist');
    await verifyDomText('dr-a2a-clinical-gateway', 'Dark Step 1 AgentId');
    await saveShot('dark_training_01_protocol_discovery.png');

    // Step 2: Google Cloud IAM & Service Account OIDC
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(2);
    await verifyDomText('gemini-enterprise-a2a-invoker@gcp-biopharma-prod.iam.gserviceaccount.com', 'Dark Step 2 SA');
    await verifyDomText('roles/run.invoker', 'Dark Step 2 Role');
    await saveShot('dark_training_02_iam_oidc.png');

    // Step 3a: Google Cloud Console - Register External Agent Wizard
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(3);
    await setRegistrationMode('gcp');
    await setGcpTab('wizard');
    await verifyDomText('console.cloud.google.com/vertex-ai/agent-builder', 'Dark Step 3 GCP URL');
    await verifyDomText('Register External Agent (Google A2A Protocol v1.0.0)', 'Dark Step 3 GCP Wizard Title');
    await verifyDomText('gcp-biopharma-prod', 'Dark Step 3 GCP Project');
    await saveShot('dark_training_03a_gcp_console_wizard.png');

    // Step 3b: Google Cloud Console - External A2A Agent Swarms Catalog
    await setGcpTab('catalog');
    await verifyDomText('External A2A Agent Swarms', 'Dark Step 3 GCP Catalog Title');
    await verifyDomText('2.42 µs AST', 'Dark Step 3 GCP Latency');
    await saveShot('dark_training_03b_gcp_console_catalog.png');

    // Step 3c: Google Cloud Console - Cloud Run Security & IAM
    await setGcpTab('iam');
    await verifyDomText('Target Service: a2a-gateway-prod', 'Dark Step 3 GCP Cloud Run');
    await verifyDomText('roles/run.invoker', 'Dark Step 3 GCP Invoker Role');
    await saveShot('dark_training_03c_gcp_console_iam.png');

    // Step 3d: Gemini Enterprise Workspace Admin Registration
    await setRegistrationMode('workspace');
    await registerExt();
    await verifyDomText('@clinical-gateway', 'Dark Step 3 Mention');
    await verifyDomText('Dr. A2A Sovereign Biopharma Gateway', 'Dark Step 3 Agent Name');
    await saveShot('dark_training_03_gemini_registry.png');

    // Step 4: Enterprise RBAC & Department OU Scoping
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(4);
    await verifyDomText('Clinical Operations & Trial Sites', 'Dark Step 4 ClinOps');
    await verifyDomText('Medical Reviewers & Safety Board', 'Dark Step 4 Safety Board');
    await saveShot('dark_training_04_rbac_ou_scoping.png');

    // Step 5: Live Chat Console & Interactive A2UI Card
    await setStep(5);
    await resetChat(300);
    await page.$eval('#training-step-5', el => el.scrollIntoView({ behavior: 'instant', block: 'start' }));
    await sleep(800);
    await verifyDomText('CLINICAL DOSE TITRATION RECOMMENDATION', 'Dark Step 5 Card Title');
    await verifyDomText('1-Click Approve & Sign (FDA 21 CFR Part 11)', 'Dark Step 5 Button');
    await saveShot('dark_training_05_chat_card.png');

    // Step 5 (Approved): 1-Click 21 CFR Part 11 Electronic Signature Seal
    await approveChat();
    await page.$eval('#training-seal-stamp', el => el.scrollIntoView({ behavior: 'instant', block: 'center' }));
    await sleep(800);
    await verifyDomText('21 CFR PART 11 VALIDATED ELECTRONIC SEAL', 'Dark Step 5 Seal');
    await verifyDomText('Dr. Evelyn Reed, MD', 'Dark Step 5 Signer');
    await saveShot('dark_training_06_hitl_approved_seal.png');

    // Step 6: Universal A2UI Authoring & Omnichannel Transpilation
    await setStep(6);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await sleep(800);
    await verifyDomText('Step 6: Universal A2UI Authoring & Transpilation', 'Dark Step 6 Title');
    await verifyDomText('Omnichannel Transpiler & JTI Guard', 'Dark Step 6 Badge');
    await verifyDomText('Dose Titration Surface: MK-3475-087', 'Dark Step 6 Surface');
    await saveShot('dark_training_07_a2ui_studio.png');

    // Carousel Gallery View in Dark Mode
    await setViewMode('gallery');
    await page.$eval('#training-gallery-carousel', el => el.scrollIntoView({ behavior: 'instant', block: 'start' }));
    await sleep(800);
    await verifyDomText('Start-to-Finish Lifecycle Screenshot Carousel', 'Dark Carousel Header');
    await saveShot('dark_training_08_carousel_gallery.png');

    // =========================================================================
    // SECTION 2: LIGHT THEME CAPTURES (Steps 1 to 6 + Approved + Carousel)
    // =========================================================================
    console.log('\n--- Capturing Light Mode Gemini Enterprise Training Screenshots ---');
    await setTheme(false);

    // Step 1: Protocol Discovery & Capabilities
    await setViewMode('interactive');
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(1);
    await verifyDomText('Step 1: Protocol Discovery & Capabilities', 'Light Step 1 Title');
    await saveShot('light_training_01_protocol_discovery.png');

    // Step 2: Google Cloud IAM & Service Account OIDC
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(2);
    await verifyDomText('roles/run.invoker', 'Light Step 2 Role');
    await saveShot('light_training_02_iam_oidc.png');

    // Step 3a: Google Cloud Console - Register External Agent Wizard
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(3);
    await setRegistrationMode('gcp');
    await setGcpTab('wizard');
    await verifyDomText('console.cloud.google.com/vertex-ai/agent-builder', 'Light Step 3 GCP URL');
    await verifyDomText('Register External Agent (Google A2A Protocol v1.0.0)', 'Light Step 3 GCP Wizard Title');
    await saveShot('light_training_03a_gcp_console_wizard.png');

    // Step 3b: Google Cloud Console - External A2A Agent Swarms Catalog
    await setGcpTab('catalog');
    await verifyDomText('External A2A Agent Swarms', 'Light Step 3 GCP Catalog Title');
    await saveShot('light_training_03b_gcp_console_catalog.png');

    // Step 3c: Google Cloud Console - Cloud Run Security & IAM
    await setGcpTab('iam');
    await verifyDomText('Target Service: a2a-gateway-prod', 'Light Step 3 GCP Cloud Run');
    await saveShot('light_training_03c_gcp_console_iam.png');

    // Step 3d: Gemini Enterprise Workspace Admin Registration
    await setRegistrationMode('workspace');
    await registerExt();
    await verifyDomText('@clinical-gateway', 'Light Step 3 Mention');
    await saveShot('light_training_03_gemini_registry.png');

    // Step 4: Enterprise RBAC & Department OU Scoping
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await setStep(4);
    await verifyDomText('Clinical Operations & Trial Sites', 'Light Step 4 ClinOps');
    await saveShot('light_training_04_rbac_ou_scoping.png');

    // Step 5: Live Chat Console & Interactive A2UI Card
    await setStep(5);
    await resetChat(300);
    await page.$eval('#training-step-5', el => el.scrollIntoView({ behavior: 'instant', block: 'start' }));
    await sleep(800);
    await verifyDomText('CLINICAL DOSE TITRATION RECOMMENDATION', 'Light Step 5 Card Title');
    await saveShot('light_training_05_chat_card.png');

    // Step 5 (Approved): 1-Click 21 CFR Part 11 Electronic Signature Seal
    await approveChat();
    await page.$eval('#training-seal-stamp', el => el.scrollIntoView({ behavior: 'instant', block: 'center' }));
    await sleep(800);
    await verifyDomText('21 CFR PART 11 VALIDATED ELECTRONIC SEAL', 'Light Step 5 Seal');
    await saveShot('light_training_06_hitl_approved_seal.png');

    // Step 6: Universal A2UI Authoring & Omnichannel Transpilation
    await setStep(6);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await sleep(800);
    await verifyDomText('Step 6: Universal A2UI Authoring & Transpilation', 'Light Step 6 Title');
    await saveShot('light_training_07_a2ui_studio.png');

    // Carousel Gallery View in Light Mode
    await setViewMode('gallery');
    await page.$eval('#training-gallery-carousel', el => el.scrollIntoView({ behavior: 'instant', block: 'start' }));
    await sleep(800);
    await verifyDomText('Start-to-Finish Lifecycle Screenshot Carousel', 'Light Carousel Header');
    await saveShot('light_training_08_carousel_gallery.png');

    console.log('\n🎉 ALL 22 GEMINI ENTERPRISE & GCP CONSOLE TRAINING SCREENSHOTS CAPTURED & VERIFIED SUCCESSFULLY!');
  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch (e) {
      // Profile cleanup error ignored
    }
  }
}

runTrainingE2ESuite().catch((err) => {
  console.error('❌ E2E Automation Error:', err);
  process.exit(1);
});
