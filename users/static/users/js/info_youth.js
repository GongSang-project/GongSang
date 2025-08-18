// users/static/users/js/user_info.js
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  const bar = document.getElementById('progressBar');
  const submitBtn = document.getElementById('submitBtn') || form.querySelector('button[type="submit"]');
  const done = document.getElementById('doneSection');

  const province = document.getElementById('id_interested_province') || form.querySelector('[name="interested_province"]');
  const city = document.getElementById('id_interested_city') || form.querySelector('[name="interested_city"]');
  const district = document.getElementById('id_interested_district') || form.querySelector('[name="interested_district"]');

  function provinceFilled() {
    return !!province && String(province.value || '').trim().length > 0;
  }
  function cityFilled() {
    return !!city && String(city.value || '').trim().length > 0;
  }
  function districtFilled() {
    return !!district && String(district.value || '').trim().length > 0;
  }

  function updateProgress() {
    const checks = [
      () => provinceFilled(),
      () => cityFilled(), 
      () => districtFilled(), 
    ];

    const passed = checks.reduce((acc, fn) => acc + (fn() ? 1 : 0), 0);
    const total = checks.length;
    const percent = Math.round((passed / total) * 100);

    if (bar) {
      bar.style.width = percent + '%';
      bar.setAttribute('aria-valuenow', String(percent));
    }
    if (submitBtn) submitBtn.disabled = percent < 100;
  }

  // 이벤트 바인딩
  const inputs = [];
  if (province) inputs.push(province);
  if (city) inputs.push(city);
  if (district) inputs.push(district); 
  inputs.forEach(el => {
    el.addEventListener('input', updateProgress);
    el.addEventListener('change', updateProgress);
  });
  updateProgress();

  // CSRF 토큰 추출
  function getCsrfToken() {
    const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  const doneClose = document.getElementById('doneClose');
  if (doneClose) {
    doneClose.addEventListener('click',()=>{
      if (done) done.hidden =true;
      if (form) form.hidden =false;

      if (typeof updateProgress === 'function') updateProgress();

      form.querySelector('input,select,textarea')?.focus();
      window.scrollTo({top:0, behavior:'smooth'});
    });
  }


})();
