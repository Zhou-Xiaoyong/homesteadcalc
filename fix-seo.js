const fs = require('fs');
const path = require('path');

// Title fixes: remove " | Homestead Calculators" suffix, shorten if still >60 chars
const titleFixes = [
  { file: 'calculators/chicken-feed.html',
    old: 'Chicken Feed Calculator — Free Feed Cost & Quantity Tool (2026) | Homestead Calculators',
    new: 'Chicken Feed Calculator — Feed Cost & Daily Rate (2026)' },
  { file: 'calculators/compost-mix.html',
    old: 'Compost Mix Ratio Calculator — Free Online Tool (2026) | Homestead Calculators',
    new: 'Compost Mix Ratio Calculator — C:N Ratio Tool (2026)' },
  { file: 'calculators/fertilizer.html',
    old: 'Fertilizer Calculator — NPK Ratio & Application Rate Tool (2026) | Homestead Calculators',
    new: 'Fertilizer Calculator — NPK Ratio & Application Rate (2026)' },
  { file: 'calculators/frost-date.html',
    old: 'Frost Date Calculator — Free Online Tool (2026) | Homestead Calculators',
    new: 'Frost Date Calculator — First & Last Frost Dates (2026)' },
  { file: 'calculators/garden-yield.html',
    old: 'Garden Yield Planner — Estimate Your Vegetable Harvest (2026) | Homestead Calculators',
    new: 'Garden Yield Planner — Estimate Harvest (2026)' },
  { file: 'calculators/plant-spacing.html',
    old: 'Plant Spacing Calculator — How Many Plants Fit in Your Garden (2026) | Homestead Calculators',
    new: 'Plant Spacing Calculator — Garden Plant Spacing (2026)' },
  { file: 'calculators/rainwater-harvest.html',
    old: 'Rainwater Harvest Calculator — Tank Size & Collection Estimate (2026) | Homestead Calculators',
    new: 'Rainwater Harvest Calculator — Collection & Tank Size (2026)' },
  { file: 'calculators/seed-starting.html',
    old: 'Seed Starting Date Calculator — Free Online Tool (2026) | Homestead Calculators',
    new: 'Seed Starting Date Calculator — Indoor Sow Dates (2026)' },
  { file: 'calculators/solar-power.html',
    old: 'Solar Power System Calculator — Free Online Tool (2026) | Homestead Calculators',
    new: 'Solar Power System Calculator — Off-Grid Sizing (2026)' },
  { file: 'calculators/square-foot-gardening.html',
    old: 'Square Foot Gardening Planner — Free Online Tool (2026) | Homestead Calculators',
    new: 'Square Foot Gardening Planner — Plant Spacing (2026)' },
  { file: 'calculators/calculators/index.html',
    old: 'All Homestead Calculators — Free Tools for Self-Sufficient Living (2026)',
    new: 'All Homestead Calculators — 19 Free Tools (2026)' },
];

const dir = '.';
titleFixes.forEach(fix => {
  const filepath = path.join(dir, fix.file);
  if (!fs.existsSync(filepath)) { console.log('NOT FOUND: ' + fix.file); return; }
  let content = fs.readFileSync(filepath, 'utf8');
  const oldTitle = '<title>' + fix.old + '</title>';
  const newTitle = '<title>' + fix.new + '</title>';
  if (content.includes(oldTitle)) {
    content = content.replace(oldTitle, newTitle);
    fs.writeFileSync(filepath, content, 'utf8');
    console.log('FIXED: ' + fix.file + ' (' + fix.new.length + ' chars)');
  } else {
    console.log('NOT FOUND in ' + fix.file + ': ' + fix.old.substring(0, 40) + '...');
  }
});

// Also fix meta descriptions that are too short (<120 chars)
const metaFixes = [
  { file: 'privacy-policy.html',
    old: 'Privacy Policy for Homestead Calculators website. Effective Date: March 15, 2026.',
    new: 'Privacy Policy for Homestead Calculators website. Learn how we collect, use, and protect your information. Effective Date: March 15, 2026.' },
  { file: 'terms.html',
    old: 'Terms of Use for Homestead Calculators website. Effective Date: March 15, 2026.',
    new: 'Terms of Use for Homestead Calculators website. Read our terms and conditions for using our free homesteading calculator tools. Effective Date: March 15, 2026.' },
];

metaFixes.forEach(fix => {
  const filepath = path.join(dir, fix.file);
  if (!fs.existsSync(filepath)) { console.log('NOT FOUND: ' + fix.file); return; }
  let content = fs.readFileSync(filepath, 'utf8');
  const oldMeta = 'content="' + fix.old + '"';
  const newMeta = 'content="' + fix.new + '"';
  if (content.includes(oldMeta)) {
    content = content.replace(oldMeta, newMeta);
    fs.writeFileSync(filepath, content, 'utf8');
    console.log('META FIXED: ' + fix.file + ' (' + fix.new.length + ' chars)');
  } else {
    console.log('META NOT FOUND in ' + fix.file);
  }
});

console.log('\nDone.');
