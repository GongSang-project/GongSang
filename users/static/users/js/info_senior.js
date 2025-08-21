

document.addEventListener('DOMContentLoaded', () => {
  const form       = document.getElementById('userInfoForm');
  if (!form) return; // 폼 없으면 종료

  const progressBar = document.getElementById('progressBar');         
  const submitBtn   = document.getElementById('submitBtn');           
  const otherCard   = document.getElementById('otherCard');         
  const otherInput  = document.getElementById('id_living_type_other');
  const radios      = document.querySelectorAll('.radio-card input[type="radio"]'); 

  const anyRadioChecked = () => Array.from(radios).some(r => r.checked);
  const otherHasValue   = () => !!(otherInput && otherInput.value.trim());

  // 진행바
  const setProgress = (on) => {
    if (!progressBar) return;
    progressBar.style.width = on ? '100%' : '0%';
    progressBar.setAttribute('aria-valuenow', on ? '100' : '0');
  };

  // 제출 버튼
  const setSubmitEnabled = (on) => {
    if (submitBtn) submitBtn.disabled = !on;
  };

  // 입력 상태와 진행바, 제출버튼 동기화
  const syncSubmitAndProgress = () => {
    const ok = anyRadioChecked() || otherHasValue();
    setProgress(ok);
    setSubmitEnabled(ok);
  };
 
  // 기타 카드 활성 상태 시 동작
  const activateOtherCardIfNeeded = () => {
    if (!otherCard) return;

    const active =
      (document.activeElement === otherInput) || otherHasValue();
    otherCard.classList.toggle('active', active);

    // 기타에 값이 있으면 라디오 해제
    if (otherHasValue()) radios.forEach(r => (r.checked = false));

    // 진행바, 제출버튼 재동기화 
    syncSubmitAndProgress();
  };

  //라디오 선택 시 기타 비우기, 동시에 선택 되지 않게 함
  const onRadioChange = () => {
    if (otherCard) otherCard.classList.remove('active');
    if (otherInput) otherInput.value = '';
    syncSubmitAndProgress();
  };


  radios.forEach(r => {
    r.addEventListener('change', onRadioChange);
    r.addEventListener('input',  onRadioChange);
  });

  if (otherCard && otherInput) {
    otherCard.addEventListener('click', () => otherInput.focus());
    otherInput.addEventListener('focus', activateOtherCardIfNeeded);
    otherInput.addEventListener('blur',  activateOtherCardIfNeeded);
    otherInput.addEventListener('input', activateOtherCardIfNeeded);
  }

  // ---- 초기 동기화 ----
  activateOtherCardIfNeeded();
  syncSubmitAndProgress();
});
