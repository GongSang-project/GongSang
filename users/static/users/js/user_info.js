// ✅ /users/user_info/ 전용: 진입 경로 기록
(() => {
  if (!location.pathname.startsWith('/users/user_info/')) return;

  const ENTRY_KEY = 'userInfoEntry';
  const BLOCK_PATHS = new Set([
    '/users/senior-living-type/', '/users/senior-living-type',
    '/users/youth-region/',       '/users/youth-region',
  ]);

  try {
    const ref = document.referrer;
    if (!ref) {
      if (!sessionStorage.getItem(ENTRY_KEY)) sessionStorage.setItem(ENTRY_KEY, 'other');
      return;
    }

    const u = new URL(ref, location.origin);
    if (u.origin !== location.origin) {
      if (!sessionStorage.getItem(ENTRY_KEY)) sessionStorage.setItem(ENTRY_KEY, 'other');
      return;
    }

    const refPath = u.pathname;

    // 1) 차단 경로에서 온 경우: 기존 값 유지(덮지 않음)
    if (BLOCK_PATHS.has(refPath)) return;

    // 2) 마이페이지에서 온 경우만 저장
    if (refPath === '/users/youth/mypage/' || refPath === '/users/senior/mypage/') {
      sessionStorage.setItem(ENTRY_KEY, refPath);
      return;
    }

    // 3) 그 외: 값이 없을 때만 초기화
    if (!sessionStorage.getItem(ENTRY_KEY)) {
      sessionStorage.setItem(ENTRY_KEY, 'other');
    }
  } catch {
    if (!sessionStorage.getItem(ENTRY_KEY)) {
      sessionStorage.setItem(ENTRY_KEY, 'other');
    }
  }
})();


(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

    const backLink = document.querySelector('.header a');
  if (backLink) {
    backLink.addEventListener('click', (e) => {
      const entry = sessionStorage.getItem('userInfoEntry');
      if (entry && entry !== 'other') {
        e.preventDefault();
        location.assign(entry); // history.back() 금지
      }
      // 없으면 <a>의 기본 href(/users/select_user/)로 이동
    });
  }

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
