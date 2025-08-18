(function () {
  const app = document.getElementById('app-wrapper');
  const progress = document.getElementById('progressBar');
  const nextBtn = document.getElementById('nextBtn');
  const selectUserLink = document.getElementById('selectUserLink');


  const step  = parseInt(app?.dataset.step  || '1', 10);
  const total = parseInt(app?.dataset.total || '10', 10);


  const targetPercent   = Math.round((step / total) * 100);
  const baselinePercent = Math.round(((step - 1) / total) * 100);


  const form = document.getElementById('surveyForm');
  const radios = form.querySelectorAll('input[type="radio"]');
  const checks = form.querySelectorAll('input[type="checkbox"]');
  const textarea = form.querySelector('textarea');
  const checkHint = document.getElementById('checkHint');


  progress.style.width = baselinePercent + '%';

  if (selectUserLink) {
    selectUserLink.hidden = step !== 1; 
  }

  function evaluate() {
    let ready = false;

    if (radios.length) {
      ready = Array.from(radios).some(r => r.checked);
    } else if (checks.length) {
      const count = Array.from(checks).filter(c => c.checked).length;
      ready = count >= 1 && count <= 2;
      if (checkHint) {
        checkHint.classList.toggle('error', count > 2 || count === 0);
        checkHint.textContent = count > 2
          ? '최대 2개까지만 선택할 수 있어요.'
          : '최대 2개까지 선택할 수 있어요.';
      }
    } else if (textarea) {

        ready = true;
    } else {
      ready = true;
    }

    nextBtn.disabled = !ready;

    progress.style.width = (ready ? targetPercent : baselinePercent) + '%';
  }

  radios.forEach(r => r.addEventListener('change', evaluate));
  checks.forEach(c => c.addEventListener('change', evaluate));
  if (textarea) textarea.addEventListener('input', evaluate);

  evaluate();
})();
