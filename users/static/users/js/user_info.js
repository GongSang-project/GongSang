// users/static/users/js/user_info.js
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  const bar = document.getElementById('progressBar');
  const submitBtn = document.getElementById('submitBtn') || form.querySelector('button[type="submit"]');
  const done = document.getElementById('doneSection');
  const errorsBox = document.getElementById('formErrors');

  const username = document.getElementById('id_username') || form.querySelector('[name="username"]');
  const age = document.getElementById('id_age') || form.querySelector('[name="age"]');
  const phone = document.getElementById('id_phone_number') || form.querySelector('[name="phone_number"]');
  const genderRadios = form.querySelectorAll('input[name="gender"]');
  const genderSelect = form.querySelector('select[name="gender"]');


  // 진행바 계산을 위한 각 요소가 채워졌는지 확인하는 함수
  // 성별
  function genderFilled() {
    if (genderRadios && genderRadios.length) {
      return Array.from(genderRadios).some(r => r.checked);
    }
    if (genderSelect) return genderSelect.value !== '' && genderSelect.value !== null;
    return false;
  }
  // 나이
  function ageValid() {
    if (!age) return false;
    const n = Number(String(age.value).replace(/[^\d]/g, ''));
    if (!Number.isFinite(n)) return false;
    return n >= 1 && n <= 120;
  }
  // 번호
  function phoneFilled() {
    return !!phone && String(phone.value || '').trim().length > 0;
  }

  // 상단 진행바
  function updateProgress() {
    const checks = [
      () => !!username && username.value.trim().length > 0,
      () => ageValid(),
      () => genderFilled(),
      () => phoneFilled(), 
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
  if (username) inputs.push(username);
  if (age) inputs.push(age);
  if (genderSelect) inputs.push(genderSelect);
  if (genderRadios && genderRadios.length) genderRadios.forEach(r => inputs.push(r));
  if (phone) inputs.push(phone); 
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
