const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

(async () => {
  const macChromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const profileDir = path.join(__dirname, '.chrome_gcp_profile');
  
  console.log('Testing launch with profile:', profileDir);
  const browser = await puppeteer.launch({
    executablePath: macChromePath,
    headless: 'new',
    defaultViewport: { width: 1600, height: 1000 },
    userDataDir: profileDir,
    args: [
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--no-default-browser-check',
      '--no-first-run',
      '--disable-blink-features=AutomationControlled',
    ],
  });

  const page = await browser.newPage();
  console.log('Navigating to https://console.cloud.google.com/ ...');
  await page.goto('https://console.cloud.google.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 6000));
  
  const currentUrl = page.url();
  console.log('Current URL:', currentUrl);
  const pageTitle = await page.title();
  console.log('Page Title:', pageTitle);
  
  const bodyTextSnippet = await page.evaluate(() => (document.body ? document.body.innerText.substring(0, 500) : ''));
  console.log('Body Text Snippet:\n', bodyTextSnippet);
  
  const screenshotPath = path.join(__dirname, 'test_current_page.png');
  await page.screenshot({ path: screenshotPath });
  console.log('Screenshot saved to:', screenshotPath);
  
  await browser.close();
})();
