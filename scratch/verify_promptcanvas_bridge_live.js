const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const OUT_DIR = path.join(__dirname, 'screenshots_promptcanvas_live_bridge');
if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function main() {
  console.log('🚀 Starting PromptCanvas ⟷ A2A Gateway Live Bridge Verification...');
  
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1600,1050']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1600, height: 1050 });

    console.log('Navigating to http://localhost:3000/gcp...');
    await page.goto('http://localhost:3000/gcp', { waitUntil: 'networkidle2', timeout: 30000 });
    await sleep(2000);

    // Take screenshot of default page with "Run on A2A Swarm" button
    const shot1 = path.join(OUT_DIR, '01_promptcanvas_gcp_page.png');
    await page.screenshot({ path: shot1, fullPage: false });
    console.log('📸 Saved 01_promptcanvas_gcp_page.png');

    // Verify button exists
    const buttonText = await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Run on A2A Swarm'));
      return btn ? btn.textContent.trim() : null;
    });
    console.log('Button found in DOM:', buttonText);

    if (!buttonText) {
      throw new Error('Button "Run on A2A Swarm" not found on page!');
    }

    // Click the button to trigger compilation
    console.log('Clicking "Run on A2A Swarm"...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Run on A2A Swarm'));
      if (btn) btn.click();
    });

    // Mandatory settling delay
    await sleep(2500);

    // Take screenshot of the open modal
    const shot2 = path.join(OUT_DIR, '02_a2a_swarm_modal_compiled.png');
    await page.screenshot({ path: shot2, fullPage: false });
    console.log('📸 Saved 02_a2a_swarm_modal_compiled.png');

    // Verify modal DOM content
    const modalInfo = await page.evaluate(() => {
      const header = document.querySelector('h3');
      const nodesCountEl = Array.from(document.querySelectorAll('.text-2xl')).map(el => el.textContent.trim());
      const stages = Array.from(document.querySelectorAll('.text-xs.font-bold')).map(el => el.textContent.trim());
      return {
        header: header ? header.textContent.trim() : null,
        statCounters: nodesCountEl,
        stagesSample: stages.slice(0, 5)
      };
    });
    console.log('Live Modal Verification:', JSON.stringify(modalInfo, null, 2));

    // Click "Nodes Matrix" tab
    console.log('Clicking "Extracted Nodes" tab...');
    await page.evaluate(() => {
      const tab = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Extracted Nodes'));
      if (tab) tab.click();
    });
    await sleep(1000);

    const shot3 = path.join(OUT_DIR, '03_a2a_swarm_nodes_matrix.png');
    await page.screenshot({ path: shot3, fullPage: false });
    console.log('📸 Saved 03_a2a_swarm_nodes_matrix.png');

    // Click "Raw A2A DAG (JSON)" tab
    console.log('Clicking "Raw A2A DAG (JSON)" tab...');
    await page.evaluate(() => {
      const tab = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Raw A2A DAG'));
      if (tab) tab.click();
    });
    await sleep(1000);

    const shot4 = path.join(OUT_DIR, '04_a2a_swarm_raw_json.png');
    await page.screenshot({ path: shot4, fullPage: false });
    console.log('📸 Saved 04_a2a_swarm_raw_json.png');

    // Close modal
    console.log('Closing modal...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.trim() === 'Close');
      if (btn) btn.click();
    });
    await sleep(800);

    // Switch architecture to Biopharma (gcp-pharma-conceptual)
    console.log('Switching to Biopharma Architecture...');
    await page.evaluate(() => {
      const archBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Life Sciences'));
      if (archBtn) archBtn.click();
    });
    await sleep(1500);

    // Click "Run on A2A Swarm" for Biopharma architecture
    console.log('Clicking "Run on A2A Swarm" on Biopharma architecture...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Run on A2A Swarm'));
      if (btn) btn.click();
    });
    await sleep(2500);

    const shot5 = path.join(OUT_DIR, '05_a2a_biopharma_21cfr11_certified.png');
    await page.screenshot({ path: shot5, fullPage: false });
    console.log('📸 Saved 05_a2a_biopharma_21cfr11_certified.png');

    const biopharmaCert = await page.evaluate(() => {
      const badge = Array.from(document.querySelectorAll('span')).find(s => s.textContent && s.textContent.includes('21 CFR Part 11 Certified'));
      return badge ? badge.textContent.trim() : 'NOT_FOUND';
    });
    console.log('Biopharma Certification Badge in DOM:', biopharmaCert);

    console.log('🎉 Live Bridge Verification Complete! All 5 screenshots captured successfully.');
  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
