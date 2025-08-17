// users/static/users/js/user_info.js
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  const bar = document.getElementById('progressBar');
  const submitBtn = document.getElementById('submitBtn') || form.querySelector('button[type="submit"]');
  const done = document.getElementById('doneSection');
  const errorsBox = document.getElementById('formErrors');

  // Django 기본 렌더링 id/name 모두 대응
  const username = document.getElementById('id_username') || form.querySelector('[name="username"]');
  const age = document.getElementById('id_age') || form.querySelector('[name="age"]');
  const phone = document.getElementById('id_phone_number') || form.querySelector('[name="phone_number"]');
  const genderRadios = form.querySelectorAll('input[name="gender"]');
  const genderSelect = form.querySelector('select[name="gender"]');


  function genderFilled() {
    if (genderRadios && genderRadios.length) {
      return Array.from(genderRadios).some(r => r.checked);
    }
    if (genderSelect) return genderSelect.value !== '' && genderSelect.value !== null;
    return false;
  }
  function ageValid() {
    if (!age) return false;
    const n = Number(String(age.value).replace(/[^\d]/g, ''));
    if (!Number.isFinite(n)) return false;
    return n >= 1 && n <= 120;
  }
  function phoneFilled() {
    return !!phone && String(phone.value || '').trim().length > 0;
  }

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

  // // 폼 제출 → AJAX로 저장하고, 성공 시 동일 페이지에서 완료 화면 표시
  // form.addEventListener('submit', async (e) => {
  //   e.preventDefault();
  //   if (submitBtn && submitBtn.disabled) return;

  //   // 이전 에러 메시지 초기화
  //   if (errorsBox) errorsBox.textContent = '';

  //   try {
  //     const formData = new FormData(form);
  //     const res = await fetch(form.action || window.location.href, {
  //       method: 'POST',
  //       headers: {
  //         'X-Requested-With': 'XMLHttpRequest',
  //         'X-CSRFToken': getCsrfToken(),
  //       },
  //       body: formData,
  //       redirect: 'follow',
  //       credentials: 'same-origin',
  //     });

  //     const contentType = res.headers.get('content-type') || '';
  //     if (!res.ok) {
  //       if (contentType.includes('application/json')) {
  //         const data = await res.json();
  //         if (errorsBox && data && data.errors) {
  //           const msgs = [];
  //           for (const [field, list] of Object.entries(data.errors)) {
  //             msgs.push(`${field}: ${Array.isArray(list) ? list.join(', ') : String(list)}`);
  //           }
  //           errorsBox.textContent = msgs.join(' • ');
  //         } else if (errorsBox) {
  //           errorsBox.textContent = '제출 중 오류가 발생했습니다. 다시 시도해주세요.';
  //         }
  //       } else {
  //         if (errorsBox) errorsBox.textContent = '제출 중 오류가 발생했습니다. 다시 시도해주세요.';
  //       }
  //       return;
  //     }

  //     // 성공 처리
  //     if (done) done.hidden = false;
  //     form.hidden = true;
  //     if (bar) bar.style.width = '100%';
  //     const cta = document.getElementById('ctaSurvey');
  //     if (cta) cta.focus();

  //   } catch (err) {
  //     console.error(err);
  //     if (errorsBox) errorsBox.textContent = '네트워크 오류가 발생했습니다.';
  //   }
  // });
  
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
