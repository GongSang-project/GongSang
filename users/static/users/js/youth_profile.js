document.addEventListener('DOMContentLoaded', function () {

  //점수바 채우기
  const bar  = document.querySelector('.score-bar');
  const fill = document.querySelector('.score-fill');
  const bubbleImg = document.querySelector('.score');
  const bubbleTxt = document.querySelector('.score-text');
  const bottomCta = document.getElementById('bottom-cta');
  const ctaCall = document.getElementById('cta-call');   // 번호 복사 버튼
  const ctaCancel = document.getElementById('cta-copy'); // 취소 버튼
  const overlay = document.getElementById('overlay');

  if (bar && fill) {
    const raw = parseFloat(bar.dataset.score || '0');
    const score = Math.max(0, Math.min(100, isNaN(raw) ? 0 : raw));

    const maxW = bar.clientWidth;             
    const fillPx = Math.round((score / 100) * maxW);
    fill.style.width = fillPx + 'px';

    // 점수 말풍선(이미지/텍스트) 위치: fill 끝지점
    if (bubbleImg && bubbleTxt) {
      const barLeft  = bar.offsetLeft;         
      const halfImg  = (bubbleImg.clientWidth || 42) / 2;
      const minX     = barLeft + halfImg;
      const maxX     = barLeft + maxW - halfImg;
      const endX     = barLeft + fillPx;
      const leftPx   = Math.max(minX, Math.min(endX, maxX));

      bubbleImg.style.left = leftPx + 'px';
      bubbleTxt.style.left = leftPx + 'px';
    }
  }

  //태그 3개씩만 뜨도록
  const box = document.getElementById('hashdtags');
  if(!box) return;
  const kids = Array.from(box.children);
  kids.forEach((el,i)=>{
    if ((i+1)%3===0){
        const br =document.createElement('i');
        br.className='break';
        box.insertBefore(br, el.nextSibling);
    }
  });

  // 쿠키에서 CSRF 읽기
  function getCsrfToken(name = 'csrftoken') {
    const m = document.cookie.match(new RegExp('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)'));
    return m ? decodeURIComponent(m.pop()) : '';
  }

  function openCTA(phoneNumber) {
    console.log('openCTA called with:', phoneNumber);

    const sanitized = String(phoneNumber).replace(/[^\d+]/g, '');

    ctaCall.textContent = `📞  통화 ${phoneNumber}`;
    ctaCall.dataset.phone = phoneNumber;
    ctaCall.setAttribute('href', `tel:${sanitized}`);

    bottomCta.setAttribute('aria-hidden', 'false');
    bottomCta.classList.add('show');

    overlay.hidden = false;
    overlay.classList.add('show');
  }

  function closeCTA() {
    bottomCta.setAttribute('aria-hidden', 'true');
    bottomCta.classList.remove('show');
    ctaCall.removeAttribute('data-phone');

    overlay.classList.remove('show');
    overlay.hidden=true;
  }

  // 번호 복사 동작
  // ctaCall?.addEventListener('click', (e) => {
  //   e.preventDefault();
  //   const phone = ctaCall.dataset.phone;
  //   if (!phone) return closeCTA();

  //   navigator.clipboard.writeText(phone)
  //     .then(() => alert(`전화번호가 복사되었습니다: ${phone}`))
  //     .catch(() => alert('복사에 실패했습니다. 수동으로 복사해주세요.'));
  //   closeCTA();
  // });

  //모바일에서 전화앱으로 이동
  ctaCall?.addEventListener('click', () => {
  closeCTA();
});

  // 취소버튼 눌러서 닫기
  ctaCancel?.addEventListener('click', closeCTA);
  //오버레이 눌러서 닫기
  overlay?.addEventListener('click', closeCTA);


  // 전화번호 요청 버튼들
  document.querySelectorAll('.telnum_btn').forEach((button) => {
    button.addEventListener('click', async () => {
      const requestId = button.dataset.requestId;
      if (!requestId) return;


      const url = `/matching/confirm_contact/${requestId}/`;
      console.log('POST =>', url);


      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          body: JSON.stringify({}),
        });

        if (!resp.ok) {
          const text = await resp.text();
          console.warn('HTTP Error', resp.status, text.slice(0,200));
          throw new Error(text || `HTTP ${resp.status}`);
        }

        const ct = resp.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
          const body = await resp.text();
          console.warn('Non-JSON response', resp.status, body.slice(0,200));
          alert('로그인이 필요하거나 권한/라우팅 문제일 수 있어요.');
          return;
        }
        
        const data = await resp.json();
        console.log('API data:', data);

        if (data && data.phone_number) {
          openCTA(data.phone_number);
        } else {
          alert(data && data.message ? data.message : '전화번호를 불러올 수 없습니다.');
        }
      } catch (err) {
        console.error(err);
        alert('요청 처리 중 오류가 발생했습니다.');
      }
    });
  });
});

(function () {
  const app = document.getElementById('app-wrapper');
  const reviews = document.querySelector('.reviews-section');
  const line = document.querySelector('.line3');
  const traits = document.querySelector('.traits-section');

  if (!app || !reviews || !line || !traits) return;

  // offsetParent 기준 하단 좌표
  const bottomOf = (el) => el.offsetTop + el.offsetHeight;

  function place() {
    // 1) 리뷰 섹션 실제 바닥
    const anchorBottom = bottomOf(reviews);

    // 2) 라인: 바닥에서 22px 아래
    const GAP = 22;
    line.style.top = (anchorBottom + GAP) + 'px';

    // 3) 성향 섹션: 라인 아래 22px (라인은 1px 보더라 높이가 거의 0)
    const lineH = line.offsetHeight || 1;
    traits.style.top = (anchorBottom + GAP + lineH + GAP) + 'px';
  }

  // 최초/리사이즈/폰트-이미지 로딩/동적 내용변경 대응
  window.addEventListener('load', place, { passive: true });
  window.addEventListener('resize', place, { passive: true });

  // 리뷰 요약/해시태그/리뷰 목록 변화에도 대응
  const mo = new MutationObserver(place);
  mo.observe(reviews, { childList: true, subtree: true, characterData: true });

  place();
})();