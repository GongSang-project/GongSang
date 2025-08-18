
(() => {
  const form = document.getElementById('userInfoForm');
  if (!form) return;

  const bar = document.getElementById('progressBar');
  const submitBtn = document.getElementById('submitBtn');

  const livingRadios = form.querySelectorAll('input[name="living_type"]');

  function isSelected() {
    return Array.from(livingRadios).some(r => r.checked);
  }

  function updateUI() {
    const ok = isSelected();
    if (bar) {
      bar.style.width = ok ? '100%' : '0%';
      bar.setAttribute('aria-valuenow', ok ? '100' : '0');
    }
    if (submitBtn) submitBtn.disabled = !ok;
  }

  updateUI();

  livingRadios.forEach(r => {
    r.addEventListener('change', updateUI);
    r.addEventListener('input', updateUI);
  });
})();

(function () {
  const otherCard = document.getElementById('otherCard');
  const otherInput = document.getElementById('id_living_type_other');
  const radioInputs = document.querySelectorAll('.radio-card input[type="radio"]');
  const submitBtn = document.getElementById('submitBtn');

  // 카드 클릭 → 입력창 포커스
  if (otherCard && otherInput) {
    otherCard.addEventListener('click', () => {
      otherInput.focus();
    });

    const syncOtherActive = () => {
      const hasValue = otherInput.value && otherInput.value.trim().length > 0;
      if (document.activeElement === otherInput || hasValue) {
        otherCard.classList.add('active');
        // 라디오가 이미 선택되어 있다면 해제(선택은 기타로 대체하는 UX)
        if (hasValue) {
          radioInputs.forEach(r => (r.checked = false));
        }
      } else {
        otherCard.classList.remove('active');
      }
      updateSubmitState();
    };

    otherInput.addEventListener('focus', syncOtherActive);
    otherInput.addEventListener('blur', syncOtherActive);
    otherInput.addEventListener('input', syncOtherActive);
  }

  // 라디오 선택 시 기타 카드 비활성화/입력 비움(서로 배타적으로 동작)
  radioInputs.forEach(r => {
    r.addEventListener('change', () => {
      if (r.checked && otherCard && otherInput) {
        otherCard.classList.remove('active');
        otherInput.value = '';
      }
      updateSubmitState();
    });
  });

  // 제출 버튼 활성화: 라디오 선택 또는 기타 입력값 존재하면 활성화
  function updateSubmitState() {
    const anyRadioChecked = Array.from(radioInputs).some(r => r.checked);
    const otherHasValue = otherInput && otherInput.value.trim().length > 0;
    submitBtn.disabled = !(anyRadioChecked || otherHasValue);
  }

  // 초기 상태 동기화
  updateSubmitState();
})();
