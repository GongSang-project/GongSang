(function () {
  const app = document.getElementById('app-wrapper');
  const progress = document.getElementById('progressBar');
  const nextBtn = document.getElementById('nextBtn');
  const selectUserLink = document.getElementById('selectUserLink');
  const form = document.getElementById('surveyForm');

  const step  = parseInt(app?.dataset.step  || '1', 10);
  const total = parseInt(app?.dataset.total || '10', 10);

  const targetPercent   = Math.round((step / total) * 100);
  const baselinePercent = Math.round(((step - 1) / total) * 100);

  const radios = form.querySelectorAll('input[type="radio"]');
  const checks = form.querySelectorAll('input[type="checkbox"]');
  const textarea = form.querySelector('textarea');
  const checkHint = document.getElementById('checkHint');

  const doneSection = document.getElementById('doneSection');
  const doneCTA = doneSection ? doneSection.querySelector('.cta') : null;

  const headerEl = document.querySelector('.header');
  const progressWrap = document.querySelector('.progress-wrap');

  // 진행바 초기값
  progress.style.width = baselinePercent + '%';

  // ===== 유틸 =====
  const SURVEY_PREFIX = '/users/survey/';
  function normalizePath(u) {
    try { return new URL(u, location.origin).pathname.replace(/\/+$/, '/') || '/'; }
    catch { return ''; }
  }
  function isSurveyPath(u) {
    const p = normalizePath(u);
    return p.startsWith(SURVEY_PREFIX);
  }
  function isEntryMyPage() {
    const p = normalizePath(sessionStorage.getItem('survey_entry') || '');
    return p === '/users/youth/mypage/' || p === '/users/senior/mypage/';
  }

  // ===== (1) 설문 "외부" 진입 시에만 엔트리 저장 (매번 진입할 때 갱신) =====
  (function recordEntryFromReferrer() {
    const ref = document.referrer;
    if (!ref) return;
    try {
      const u = new URL(ref, location.origin);
      // 외부 진입 && 동일 오리진 && 설문 내부가 아닌 경로일 때만 저장
      if (u.origin === location.origin && !isSurveyPath(u.href)) {
        sessionStorage.setItem('survey_entry', u.href);
      }
    } catch { /* ignore */ }
  })();

  // ===== (2) 1단계 뒤로가기: 항상 저장된 "외부 진입 경로"로 이동 =====
  if (selectUserLink) {
    selectUserLink.hidden = step !== 1;
    if (step === 1) {
      selectUserLink.addEventListener('click', function (e) {
        e.preventDefault();
        const entry = sessionStorage.getItem('survey_entry');
        if (entry && !isSurveyPath(entry)) {
          window.location.assign(entry);
        } else {
          // 엔트리가 없거나 잘못 저장되었으면 기존 href로
          window.location.assign(selectUserLink.href);
        }
      });
    }
  }

  // ===== (3) 마지막 단계: 제출 가로채서 완료 화면 먼저 → CTA에서 처리 =====
  if (step === total) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      if (!doneSection) { form.submit(); return; }

      // 완료 오버레이 표시
      doneSection.hidden = false;
      form.hidden = true;
      progress.style.width = '100%';
      if (headerEl) headerEl.hidden = true;
      if (progressWrap) progressWrap.hidden = true;
      if (doneCTA) doneCTA.type = 'button';

      // 저장된 엔트리가 '마이페이지'면 CTA 문구 바꾸기
      if (doneCTA && isEntryMyPage()) {
        doneCTA.textContent = '마이페이지로 가기';
      }

      app.scrollTo({ top: 0, behavior: 'instant' });
    });

    // 완료 CTA 클릭: 마이페이지면 그리 이동, 아니면 백엔드 최종 제출
if (doneCTA) {
  doneCTA.addEventListener('click', async function (e) {
    e.preventDefault();
    doneCTA.disabled = true;

    const entry = sessionStorage.getItem('survey_entry');
    const goingMyPage = (() => {
      try {
        const p = new URL(entry, location.origin).pathname.replace(/\/+$/, '/') || '/';
        return p === '/users/youth/mypage/' || p === '/users/senior/mypage/';
      } catch { return false; }
    })();

    if (goingMyPage) {
      try {
        // 폼 최종 제출을 비동기로 실행 (서버 로직 실행, 리디렉트는 브라우저가 따르지 않음)
        const fd = new FormData(form);
        const csrf = (form.querySelector('input[name="csrfmiddlewaretoken"]') || {}).value || '';

        await fetch(form.action || location.href, {
          method: 'POST',
          body: fd,
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': csrf,          // Django CSRF
            'X-Requested-With': 'XMLHttpRequest'
          }
          // redirect: 'follow' 기본값이어도 페이지 네비게이션은 안 함 (fetch 내부에서만 따라감)
        });
      } catch (err) {
        // 실패하더라도 사용자 경험상 마이페이지로 보냄(필요하면 콘솔 로그)
        // console.error(err);
      }
      // 백 리디렉트는 무시하고, 우리가 직접 마이페이지로 이동
      location.assign(entry);
      return;
    }

    // 마이페이지 진입이 아니면 기존처럼 백엔드 최종 제출 + 리디렉트
    form.submit();
  });

  // 진입 경로가 마이페이지면 CTA 라벨 교체
  (function setDoneCtaLabelIfMyPage() {
    try {
      const entry = sessionStorage.getItem('survey_entry') || '';
      const p = new URL(entry, location.origin).pathname.replace(/\/+$/, '/') || '/';
      if (p === '/users/youth/mypage/' || p === '/users/senior/mypage/') {
        doneCTA.textContent = '마이페이지로 돌아가기';
      }
    } catch { /* noop */ }
  })();
}
// 완료 오버레이의 뒤로가기: 오버레이 닫고 10번 질문 화면 복귀
const doneBackBtn = doneSection ? doneSection.querySelector('.backBtn') : null;
if (doneBackBtn) {
  doneBackBtn.addEventListener('click', function (e) {
    e.preventDefault();

    // 오버레이 숨기고 폼/헤더/진행바 다시 표시
    doneSection.hidden = true;
    form.hidden = false;
    if (headerEl) headerEl.hidden = false;
    if (progressWrap) progressWrap.hidden = false;

    // 다음 번을 위해 완료 CTA 재활성화
    if (doneCTA) doneCTA.disabled = false;

    // 진행바/버튼 상태 재계산 후 맨 위로
    evaluate();
    app.scrollTo({ top: 0, behavior: 'instant' });
  });
}

  }

  // ===== 기존: 버튼 활성화/진행바 갱신 =====
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
