document.addEventListener('DOMContentLoaded', () => {
  const bottomCta = document.getElementById('bottom-cta');
  const ctaCall = document.getElementById('cta-call');   // 번호 복사 버튼
  const ctaCancel = document.getElementById('cta-copy'); // 취소 버튼
  const overlay = document.getElementById('overlay');

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