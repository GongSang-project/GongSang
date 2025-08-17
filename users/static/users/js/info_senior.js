
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  const bar = document.getElementById('progressBar');
  const submitBtn = document.getElementById('submitBtn');

  const livingRadios = form.querySelectorAll('input[name="living_type"]');

  function isSelected() {
    return Array.from(livingRadios).some(r => r.checked);
  }

  function updateUI() {
    const ok = isSelected();
    if (bar) {
      bar.style.width = ok ? '100%' : '0%';
      bar.setAttribute('aria-valuenow', ok ? '100' : '0');
    }
    if (submitBtn) submitBtn.disabled = !ok;
  }

  updateUI();

  livingRadios.forEach(r => {
    r.addEventListener('change', updateUI);
    r.addEventListener('input', updateUI);
  });
})();
