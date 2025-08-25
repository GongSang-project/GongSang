// static/users/js/senior_living_type.js
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  const submitBtn = document.getElementById('submitBtn') || form.querySelector('button[type="submit"]');
  const bar = document.getElementById('progressBar');

  // 1) user_info에서 저장해 둔 진입 경로 읽기
  const ENTRY_KEY = 'userInfoEntry';
  const entry = sessionStorage.getItem(ENTRY_KEY);
  const isFromMypage = entry === '/users/senior/mypage/' || entry === '/users/youth/mypage/';

  // 2) 버튼 라벨 변경 (마이페이지에서 온 경우만)
  if (isFromMypage && submitBtn) {
    submitBtn.textContent = '마이페이지로 가기';
  }

  // --- (선택) 진행바 업데이트: 네 기존 규칙 유지 ---
  const username = document.getElementById('id_username') || form.querySelector('[name="username"]');
  const age      = document.getElementById('id_age') || form.querySelector('[name="age"]');
  const phone    = document.getElementById('id_phone_number') || form.querySelector('[name="phone_number"]');
  const genderRadios = form.querySelectorAll('input[name="gender"]');
  const genderSelect = form.querySelector('select[name="gender"]');

  function genderFilled() {
    if (genderRadios && genderRadios.length) return Array.from(genderRadios).some(r => r.checked);
    if (genderSelect) return genderSelect.value !== '' && genderSelect.value !== null;
    return false;
  }
  function ageValid() {
    if (!age) return false;
    const n = Number(String(age.value).replace(/[^\d]/g, ''));
    return Number.isFinite(n) && n >= 1 && n <= 120;
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
    const passed  = checks.reduce((acc, fn) => acc + (fn() ? 1 : 0), 0);
    const percent = Math.round((passed / checks.length) * 100);
    if (bar) {
      bar.style.width = percent + '%';
      bar.setAttribute('aria-valuenow', String(percent));
    }
    if (submitBtn) submitBtn.disabled = percent < 100;
  }
  [username, age, phone, genderSelect, ...(genderRadios || [])]
    .filter(Boolean)
    .forEach(el => {
      el.addEventListener('input', updateProgress);
      el.addEventListener('change', updateProgress);
    });
  updateProgress();

  // 3) CSRF 토큰
  function getCsrfToken() {
    const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  // 4) 제출 동작
  form.addEventListener('submit', (e) => {
    // 마이페이지 진입일 때만: AJAX로 저장 -> 마이페이지로 이동
    if (!isFromMypage) return; // 백엔드 기본 리디렉션 유지

    e.preventDefault();

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.dataset.loading = '1';
    }

    const actionUrl = form.getAttribute('action') || location.pathname;
    const fd = new FormData(form);

    fetch(actionUrl, {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        // Django는 FormData면 Content-Type 자동 설정됨. 별도 지정 불필요.
      },
      redirect: 'follow', // 서버 리다이렉트가 있어도 OK (우린 어차피 아래에서 마이페이지로 이동)
    })
    .then(() => {
      // 저장 성공 가정 → 시니어/청년 마이페이지로 이동
      if (entry && entry !== 'other') {
        location.assign(entry);
      } else {
        // entry가 비어있을 일은 거의 없지만, 안전장치
        location.assign('/users/senior/mypage/');
      }
    })
    .catch((err) => {
      console.error('Submit failed, fallback to native submit.', err);
      // 실패 시 폴백: 기존 폼 제출로 처리(백엔드 리디렉션)
      form.submit();
    });
  });
})();
