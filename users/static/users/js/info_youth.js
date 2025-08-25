// static/users/js/youth_region.js
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  const bar = document.getElementById('progressBar');
  const submitBtn =
    document.getElementById('submitBtn') || form.querySelector('button[type="submit"]');

  // ─────────────────────────────────────────────────────────
  // 1) user_info에서 저장해 둔 진입 경로 읽기
  //    - 마이페이지에서 들어온 경우만 특별 처리
  // ─────────────────────────────────────────────────────────
  const ENTRY_KEY = 'userInfoEntry';
  const entry = sessionStorage.getItem(ENTRY_KEY);
  const isFromMypage =
    entry === '/users/youth/mypage/' || entry === '/users/senior/mypage/';

  // 버튼 라벨 변경 (마이페이지에서 온 경우만)
  if (isFromMypage && submitBtn) {
    submitBtn.textContent = '마이페이지로 가기';
  }

  // ─────────────────────────────────────────────────────────
  // 2) 진행바 & 버튼 활성화 (기존 기능 유지)
  // ─────────────────────────────────────────────────────────
  const province =
    document.getElementById('id_interested_province') ||
    form.querySelector('[name="interested_province"]');
  const city =
    document.getElementById('id_interested_city') ||
    form.querySelector('[name="interested_city"]');
  const district =
    document.getElementById('id_interested_district') ||
    form.querySelector('[name="interested_district"]');

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
    const checks = [provinceFilled, cityFilled, districtFilled];
    const passed = checks.reduce((acc, fn) => acc + (fn() ? 1 : 0), 0);
    const percent = Math.round((passed / checks.length) * 100);

    if (bar) {
      bar.style.width = percent + '%';
      bar.setAttribute('aria-valuenow', String(percent));
    }
    if (submitBtn) submitBtn.disabled = percent < 100;
  }

  [province, city, district].filter(Boolean).forEach((el) => {
    el.addEventListener('input', updateProgress);
    el.addEventListener('change', updateProgress);
  });
  updateProgress();

  // ─────────────────────────────────────────────────────────
  // 3) CSRF 토큰
  // ─────────────────────────────────────────────────────────
  function getCsrfToken() {
    const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  // ─────────────────────────────────────────────────────────
  // 4) 제출 동작
  //    - 마이페이지에서 온 경우만: AJAX로 저장 후 마이페이지로 이동
  //    - 그 외: 백엔드 기본 리디렉션(네이티브 submit)
  // ─────────────────────────────────────────────────────────
  form.addEventListener('submit', (e) => {
    if (!isFromMypage) return; // 평소대로 서버 리디렉션

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
      },
      redirect: 'follow',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Bad response: ' + res.status);
        // 저장 성공 → 저장한 마이페이지 경로로 이동
        if (entry && entry !== 'other') {
          location.assign(entry);
        } else {
          location.assign('/users/youth/mypage/');
        }
      })
      .catch((err) => {
        console.error('AJAX submit failed, fallback to native submit.', err);
        // 실패 시 폴백: 기존 폼 제출로 처리(백엔드 리디렉션)
        form.submit();
      });
  });
})();
