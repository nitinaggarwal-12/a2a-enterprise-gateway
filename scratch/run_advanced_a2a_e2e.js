/**
 * Puppeteer E2E Automation Suite for Next-Gen A2A Standards Lab & Advanced Swarm Studio.
 * 
 * Verifies and captures high-resolution screenshots across all 6 advanced modules
 * in both Dark and Light modes using Google Signed Chrome with 800ms settling delays.
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runAdvancedA2AE2ESuite() {
  const scratchDir = path.join(__dirname, 'screenshots_e2e');
  const docsDir = path.join(__dirname, '..', 'docs', 'screenshots');
  const staticDir = path.join(__dirname, '..', 'portal', 'static', 'screenshots');

  // Ensure output directories exist
  [scratchDir, docsDir, staticDir].forEach(dir => {
    fs.mkdirSync(dir, { recursive: true });
  });

  // Programmatically purge stale advanced screenshots
  [scratchDir, docsDir, staticDir].forEach(dir => {
    const files = fs.readdirSync(dir);
    files.forEach(f => {
      if (f.includes('advanced_')) {
        try { fs.unlinkSync(path.join(dir, f)); } catch (e) {}
      }
    });
  });
  console.log('🧹 Purged stale advanced lab screenshots across all output directories.');

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

    // Set Advanced Lab sub-tab helper
    const setLabTab = async (tab) => {
      await page.evaluate((t) => {
        const state = Alpine.$data(document.querySelector('[x-data]'));
        state.currentTab = 'advanced_a2a_lab';
        state.advancedLabTab = t;
      }, tab);
      await sleep(800);
    };

    // DOM Verification helper (handles CSS uppercase safely)
    const verifyDomText = async (text, label) => {
      const found = await page.evaluate((t) => {
        const lowerT = t.toLowerCase();
        if (document.body.innerText.toLowerCase().includes(lowerT)) return true;
        const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
        return inputs.some(el => (el.value || '').toLowerCase().includes(lowerT));
      }, text);
      if (found) {
        console.log(`  ✅ DOM Verification passed: "${text}" [${label}]`);
      } else {
        console.error(`  ❌ DOM Verification failed: "${text}" not found! [${label}]`);
        throw new Error(`DOM string missing: ${text}`);
      }
    };

    // Navigate to Advanced A2A Lab via DOM click
    console.log('\n--- Switching to Advanced A2A Protocol Lab Tab ---');
    await page.$eval('#tab-advanced-lab', el => el.click());
    await sleep(1000);

    // =========================================================================
    // SECTION 1: DARK THEME CAPTURES (Modules 1 to 6)
    // =========================================================================
    console.log('\n--- Capturing Dark Mode Advanced A2A Lab Screenshots ---');
    await setTheme(true);

    // Module 1: A2A <-> MCP Bridge
    await setLabTab('mcp_bridge');
    await page.$eval('#btn-mcp-execute', el => el.click());
    await sleep(800);
    await verifyDomText('Bi-Directional A2A ⟷ MCP Protocol Converter', 'Dark Module 1 Title');
    await verifyDomText('Standard MCP Response Delivered to Client', 'Dark Module 1 Response');
    await saveShot('dark_advanced_01_mcp_bridge.png');

    // Module 2: Quorum Voting & Red-Team Debate
    await setLabTab('quorum_debate');
    await page.$eval('#btn-quorum-vote', el => el.click());
    await sleep(800);
    await verifyDomText('Byzantine Quorum Voting & Red-Team Adversarial Debate', 'Dark Module 2 Title');
    await verifyDomText('SWARM QUORUM CONSENSUS REACHED', 'Dark Module 2 Verdict');
    await verifyDomText('Arbiter Agent (Gemini 3.5 Flash Consensus Synthesizer)', 'Dark Module 2 Arbiter');
    await saveShot('dark_advanced_02_quorum_debate.png');

    // Module 3: 3-Tier 21 CFR Part 11 Multi-Sig Chain
    await setLabTab('multisig_chain');
    await page.$eval('#btn-sign-tier-1', el => el.click());
    await sleep(400);
    await page.$eval('#btn-sign-tier-2', el => el.click());
    await sleep(400);
    await page.$eval('#btn-sign-tier-3', el => el.click());
    await sleep(800);
    await verifyDomText('21 CFR PART 11 VALIDATED MULTI-SIG CERTIFICATE', 'Dark Module 3 Cert');
    await verifyDomText('Dr. Marcus Vance, MD', 'Dark Module 3 PI');
    await verifyDomText('Dr. Sarah Chen, PhD', 'Dark Module 3 Biostat');
    await verifyDomText('Dr. Evelyn Reed, MD', 'Dark Module 3 MedDirector');
    await saveShot('dark_advanced_03_multisig_chain.png');

    // Module 4: In-Flight Steering & AIP-127 Checkpoint
    await setLabTab('steering_lro');
    await page.$eval('#chip-steer-dose', el => el.click());
    await sleep(300);
    await page.$eval('#btn-steer-inject', el => el.click());
    await sleep(400);
    await page.$eval('#btn-checkpoint-pause', el => el.click());
    await sleep(800);
    await verifyDomText('In-Flight Agent Steering & AIP-127 Durable Checkpoint', 'Dark Module 4 Title');
    await verifyDomText('A2A-STEER', 'Dark Module 4 Steer Tag');
    await verifyDomText('chkpt-aip127', 'Dark Module 4 Snapshot');
    await saveShot('dark_advanced_04_steering_lro.png');

    // Module 5: AMD SEV-SNP Enclave & Zero-Knowledge Proof
    await setLabTab('enclave_zkp');
    await page.$eval('#btn-fetch-enclave', el => el.click());
    await sleep(400);
    await page.$eval('#btn-verify-zkp', el => el.click());
    await sleep(800);
    await verifyDomText('AMD SEV-SNP Enclave Attestation & Zero-Knowledge Verification', 'Dark Module 5 Title');
    await verifyDomText('AMD EPYC 9654 Genoa', 'Dark Module 5 CPU');
    await verifyDomText('0 records (100% PHI Blind)', 'Dark Module 5 ZKP');
    await saveShot('dark_advanced_05_enclave_zkp.png');

    // Module 6: W3C Trace Waterfall & Chaos Resilience
    await setLabTab('trace_chaos');
    await page.$eval('#btn-chaos-inject', el => el.click());
    await sleep(800);
    await verifyDomText('Distributed W3C Trace Waterfall & Chaos Circuit Breaker', 'Dark Module 6 Title');
    await verifyDomText('Gemini Enterprise Ingress Webhook', 'Dark Module 6 Trace');
    await verifyDomText('In-Memory AST Filter', 'Dark Module 6 AST');
    await saveShot('dark_advanced_06_trace_chaos.png');

    // =========================================================================
    // SECTION 2: LIGHT THEME CAPTURES (Modules 1 to 6)
    // =========================================================================
    console.log('\n--- Capturing Light Mode Advanced A2A Lab Screenshots ---');
    await setTheme(false);

    // Module 1: A2A <-> MCP Bridge (Light)
    await setLabTab('mcp_bridge');
    await page.$eval('#btn-mcp-execute', el => el.click());
    await sleep(800);
    await verifyDomText('Bi-Directional A2A ⟷ MCP Protocol Converter', 'Light Module 1 Title');
    await saveShot('light_advanced_01_mcp_bridge.png');

    // Module 2: Quorum Voting & Red-Team Debate (Light)
    await setLabTab('quorum_debate');
    await page.$eval('#btn-quorum-vote', el => el.click());
    await sleep(800);
    await verifyDomText('Byzantine Quorum Voting & Red-Team Adversarial Debate', 'Light Module 2 Title');
    await saveShot('light_advanced_02_quorum_debate.png');

    // Module 3: 3-Tier 21 CFR Part 11 Multi-Sig Chain (Light)
    await setLabTab('multisig_chain');
    await page.$eval('#btn-sign-tier-1', el => el.click());
    await sleep(400);
    await page.$eval('#btn-sign-tier-2', el => el.click());
    await sleep(400);
    await page.$eval('#btn-sign-tier-3', el => el.click());
    await sleep(800);
    await verifyDomText('21 CFR PART 11 VALIDATED MULTI-SIG CERTIFICATE', 'Light Module 3 Cert');
    await saveShot('light_advanced_03_multisig_chain.png');

    // Module 4: In-Flight Steering & AIP-127 Checkpoint (Light)
    await setLabTab('steering_lro');
    await page.$eval('#chip-steer-dose', el => el.click());
    await sleep(300);
    await page.$eval('#btn-steer-inject', el => el.click());
    await sleep(800);
    await verifyDomText('In-Flight Agent Steering & AIP-127 Durable Checkpoint', 'Light Module 4 Title');
    await saveShot('light_advanced_04_steering_lro.png');

    // Module 5: AMD SEV-SNP Enclave & Zero-Knowledge Proof (Light)
    await setLabTab('enclave_zkp');
    await page.$eval('#btn-fetch-enclave', el => el.click());
    await sleep(400);
    await page.$eval('#btn-verify-zkp', el => el.click());
    await sleep(800);
    await verifyDomText('AMD SEV-SNP Enclave Attestation & Zero-Knowledge Verification', 'Light Module 5 Title');
    await saveShot('light_advanced_05_enclave_zkp.png');

    // Module 6: W3C Trace Waterfall & Chaos Resilience (Light)
    await setLabTab('trace_chaos');
    await page.$eval('#btn-chaos-inject', el => el.click());
    await sleep(800);
    await verifyDomText('Distributed W3C Trace Waterfall & Chaos Circuit Breaker', 'Light Module 6 Title');
    await saveShot('light_advanced_06_trace_chaos.png');

    console.log('\n🎉 ALL 12 ADVANCED A2A PROTOCOL LAB SCREENSHOTS CAPTURED & VERIFIED SUCCESSFULLY!');
  } finally {
    await browser.close();
    try {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    } catch (e) {
      // Cleanup ignored
    }
  }
}

runAdvancedA2AE2ESuite().catch((err) => {
  console.error('❌ E2E Automation Error:', err);
  process.exit(1);
});
