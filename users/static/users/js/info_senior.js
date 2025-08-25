// static/users/js/senior_living_type.js
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  // ——— DOM refs
  const progressBar = document.getElementById('progressBar');
  const submitBtn   = document.getElementById('submitBtn') || form.querySelector('button[type="submit"]');
  const otherCard   = document.getElementById('otherCard');
  const otherInput  = document.getElementById('id_living_type_other');
  const radios      = form.querySelectorAll('input[name="living_type"]');

  // ——— 진입 경로(마이페이지) 감지
  const ENTRY_KEY = 'userInfoEntry';
  const entry = sessionStorage.getItem(ENTRY_KEY) || '';
  const entryPath = (() => {
    try { return new URL(entry, location.origin).pathname || ''; }
    catch { return entry; }
  })();
  const isFromMypage = /\/users\/(senior|youth)\/mypage\/?$/i.test(entryPath);

  if (isFromMypage && submitBtn) {
    submitBtn.textContent = '마이페이지로 가기';
  }

  // ——— 상태 계산
  const anyRadioChecked = () => Array.from(radios).some(r => r.checked);
  const otherHasValue   = () => !!(otherInput && otherInput.value.trim());

  // ——— 진행바
  const setProgress = (on) => {
    if (!progressBar) return;
    progressBar.style.width = on ? '100%' : '0%';
    progressBar.setAttribute('aria-valuenow', on ? '100' : '0');
  };

  // ——— 제출 버튼
  const setSubmitEnabled = (on) => {
    if (submitBtn) submitBtn.disabled = !on;
  };

  // ——— 입력 상태 ↔ 진행바/버튼 동기화
  const syncSubmitAndProgress = () => {
    const ok = anyRadioChecked() || otherHasValue();
    setProgress(ok);
    setSubmitEnabled(ok);
  };

  // ——— 기타 카드 활성/상호배타 처리
  const activateOtherCardIfNeeded = () => {
    if (!otherCard) return;

    const active = (document.activeElement === otherInput) || otherHasValue();
    otherCard.classList.toggle('active', !!active);

    // 기타에 값이 있으면 라디오 해제
    if (otherHasValue()) radios.forEach(r => (r.checked = false));

    syncSubmitAndProgress();
  };

  // ——— 라디오 변경 시: 기타 입력 비우고 비활성
  const onRadioChange = () => {
    if (otherCard) otherCard.classList.remove('active');
    if (otherInput) otherInput.value = '';
    syncSubmitAndProgress();
  };

  // 이벤트 바인딩
  radios.forEach(r => {
    r.addEventListener('change', onRadioChange);
    r.addEventListener('input',  onRadioChange);
  });
  if (otherInput) {
    otherInput.addEventListener('input', activateOtherCardIfNeeded);
    otherInput.addEventListener('focus', activateOtherCardIfNeeded);
    otherInput.addEventListener('blur',  activateOtherCardIfNeeded);
  }
  if (otherCard && otherInput) {
    otherCard.addEventListener('click', () => otherInput.focus());
  }

  // 초기 동기화
  activateOtherCardIfNeeded(); // 내부에서 syncSubmitAndProgress 호출됨
  if (!otherInput) syncSubmitAndProgress();

  // ——— CSRF
  function getCsrfToken() {
    const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  // ——— 제출 동작: 마이페이지에서 온 경우만 AJAX 저장 후 복귀
  form.addEventListener('submit', (e) => {
    if (!isFromMypage) return; // 기본(백엔드 리다이렉트) 유지

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
      headers: { 'X-CSRFToken': getCsrfToken() },
    })
    .then(res => {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      location.assign(entryPath || '/users/senior/mypage/');
    })
    .catch(err => {
      console.error('Submit failed, fallback to native submit.', err);
      form.submit(); // 폴백
    });
  });
})();
