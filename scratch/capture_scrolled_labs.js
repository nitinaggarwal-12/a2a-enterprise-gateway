const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function main() {
  const rootDir = '/Users/nitinagga/Documents/a2a-enterprise-gateway';
  const taskDir = path.join(rootDir, 'scratch', 'screenshots_google_labs');
  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const executablePath = fs.existsSync(macChromePath) ? macChromePath : undefined;

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    defaultViewport: { width: 1600, height: 1000 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:8090', { waitUntil: 'networkidle0' });
  await sleep(1500);

  // Navigate to Dose Titration
  await page.evaluate(() => {
    const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Dose Titration'));
    if (tabBtn) tabBtn.click();
  });
  await sleep(1000);

  // Scroll to AlphaFold 3D card
  await page.evaluate(() => {
    const el = document.getElementById('alphafold-3d-viewport');
    if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
  });
  await sleep(800);
  await page.screenshot({ path: path.join(taskDir, '02b_alphafold3_full_viewport.png') });

  // Scroll to PV Radar card and trigger run
  await page.evaluate(() => {
    const btn = document.getElementById('btn-run-pv-eval');
    if (btn) {
      btn.scrollIntoView({ behavior: 'instant', block: 'center' });
      btn.click();
    }
  });
  await sleep(1200);
  await page.screenshot({ path: path.join(taskDir, '03b_gemini_flash_pv_radar_full.png') });

  await browser.close();
  console.log('Captured scrolled screenshots successfully!');
}
main().catch(console.error);
