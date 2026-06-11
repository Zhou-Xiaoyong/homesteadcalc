/* ============================================
   Homestead Calculators — Common JavaScript
   ============================================ */

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
  const menuBtn = document.querySelector('.mobile-menu-btn');
  const nav = document.querySelector('.header-nav');

  if (menuBtn && nav) {
    menuBtn.addEventListener('click', function() {
      nav.classList.toggle('open');
      const expanded = nav.classList.contains('open');
      menuBtn.setAttribute('aria-expanded', expanded);
    });

    // Close menu on outside click
    document.addEventListener('click', function(e) {
      if (!nav.contains(e.target) && !menuBtn.contains(e.target)) {
        nav.classList.remove('open');
        menuBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const tabGroup = this.closest('.tabs');
      const tabContainer = tabGroup ? tabGroup.parentElement : null;

      if (tabContainer) {
        // Deactivate all tabs
        tabGroup.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        tabContainer.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Activate clicked tab
        this.classList.add('active');
        const target = tabContainer.querySelector(this.dataset.target);
        if (target) target.classList.add('active');
      }
    });
  });
});

// Format number with commas
function formatNumber(num) {
  return num.toLocaleString('en-US', { maximumFractionDigits: 2 });
}

// Format as currency
function formatCurrency(num) {
  return num.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 });
}

// Format percentage
function formatPercent(num) {
  return num.toFixed(1) + '%';
}

// Convert lbs to kg
function lbsToKg(lbs) {
  return lbs * 0.453592;
}

// Convert kg to lbs
function kgToLbs(kg) {
  return kg / 0.453592;
}

// Convert sq ft to sq m
function sqftToSqM(sqft) {
  return sqft * 0.092903;
}

// Convert acres to hectares
function acresToHectares(acres) {
  return acres * 0.404686;
}

// Convert gallons to liters
function galToL(gallons) {
  return gallons * 3.78541;
}

// Get query parameter
function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}
