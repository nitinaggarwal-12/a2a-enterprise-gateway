/**
 * Quality Gate: DOM Element ID Coverage & Uniqueness Gate
 * Validates WCAG 4.1.1 and W3C HTML5 semantic addressability.
 */

const fs = require('fs');
const path = require('path');

function runDomIdAudit() {
  const htmlPath = path.join(__dirname, '..', 'portal', 'static', 'portal.html');
  const html = fs.readFileSync(htmlPath, 'utf8');

  console.log('====================================================');
  console.log('🛡️ QUALITY GATE: DOM ID COVERAGE & UNIQUENESS AUDIT');
  console.log('====================================================');

  // 1. Check ID Uniqueness
  const idRegex = /\bid=["']([^"']+)["']/gi;
  let match;
  const counts = {};
  while ((match = idRegex.exec(html)) !== null) {
    const id = match[1];
    counts[id] = (counts[id] || 0) + 1;
  }

  const duplicates = Object.entries(counts).filter(([id, count]) => count > 1);
  const totalUniqueIds = Object.keys(counts).length;

  console.log(`• Total Unique IDs Defined: ${totalUniqueIds}`);
  console.log(`• Duplicate IDs Found: ${duplicates.length}`);

  if (duplicates.length > 0) {
    console.error('❌ FAILED: Duplicate IDs detected:', duplicates);
    process.exit(1);
  }

  // 2. Check 100% Button ID Coverage
  const buttonRegex = /<button\b([^>]*)>/gi;
  let totalButtons = 0;
  let buttonsWithId = 0;
  const missingIdButtons = [];

  while ((match = buttonRegex.exec(html)) !== null) {
    totalButtons++;
    const attrs = match[1];
    const idMatch = attrs.match(/\bid=["']([^"']+)["']/i);
    if (idMatch) {
      buttonsWithId++;
    } else {
      const line = html.substring(0, match.index).split('\n').length;
      missingIdButtons.push({ line, attrs: attrs.trim().substring(0, 50) });
    }
  }

  const buttonCoveragePct = ((buttonsWithId / totalButtons) * 100).toFixed(1);
  console.log(`• Total Buttons: ${totalButtons}`);
  console.log(`• Buttons with Unique ID: ${buttonsWithId} (${buttonCoveragePct}%)`);

  if (buttonsWithId < totalButtons) {
    console.error(`❌ FAILED: ${missingIdButtons.length} buttons lack unique ID attributes:`, missingIdButtons);
    process.exit(1);
  }

  // 3. Check Modal & Drawer IDs
  const requiredModalIds = [
    'modal-command-palette',
    'modal-sso-login',
    'modal-justification',
    'modal-fda-dossier',
    'modal-omni-readiness',
    'drawer-omni-director',
    'drawer-dr-a2a-copilot',
    'drawer-byok-settings'
  ];

  console.log('\n• Checking Required Modal & Drawer IDs:');
  for (const reqId of requiredModalIds) {
    const exists = counts[reqId] === 1;
    console.log(`  - #${reqId}: ${exists ? '✅ PRESENT & UNIQUE' : '❌ MISSING'}`);
    if (!exists) {
      console.error(`❌ FAILED: Required modal/drawer #${reqId} is missing!`);
      process.exit(1);
    }
  }

  console.log('\n====================================================');
  console.log('✅ DOM ID COVERAGE & UNIQUENESS GATE: 100% PASSED');
  console.log('====================================================');
}

runDomIdAudit();
