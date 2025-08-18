(function () {
  const app = document.getElementById('app');

  // Views
  const stepChoose = document.getElementById('step-choose');
  const stepReview = document.getElementById('step-review');
  const stepDone   = document.getElementById('step-done');  

  // Common
  const btnBack = document.getElementById('btnBack');

  // Choose step elements
  const form = document.getElementById('idForm');
  const djangoInput = form.querySelector('input[type="file"], input[name$="id_card_image"]') || null;
  const cameraInput = document.getElementById('cameraInput');
  const galleryInput = document.getElementById('galleryInput');
  const btnCamera = document.getElementById('btnCamera');
  const btnGallery = document.getElementById('btnGallery');
  const previewImg = document.getElementById('previewImage');
  const previewBox = document.getElementById('previewBox');

  // Review step elements
  const btnAgain = document.getElementById('btnAgain');
  const btnConfirm = document.getElementById('btnConfirm');
  const reviewImage = document.getElementById('reviewImage');
  const placeholder = stepReview.querySelector('.ph');

  // Done step elements
  const btnGoSurvey = document.getElementById('btnGoSurvey');

  // 현재 선택 소스
  let lastSource = null;    // 'camera' | 'upload'
  let activeInput = null;   // 실제 파일을 가진 <input>

  /** 라우팅(히스토리) — 모든 view 공통 처리 */
  const views = {
    choose: stepChoose,
    review: stepReview,
    done:   stepDone,
  };
  const show = (name, push = true) => {
    Object.values(views).forEach(v => v.hidden = true);
    (views[name] || stepChoose).hidden = false;
    if (push) history.pushState({ step: name }, '', '');
  };

  // 최초 진입
  show('choose', false);

  btnBack.addEventListener('click', () => history.back());
  window.addEventListener('popstate', (e) => {
    const step = (e.state && e.state.step) || 'choose';
    show(step, false);
  });

  /* 이름 충돌 방지: 활성 input만 name 유지 */
  const ensureSingleName = (active) => {
    const fieldName = (djangoInput && (djangoInput.name || djangoInput.id || 'id_card_image')) || 'id_card_image';
    [djangoInput, cameraInput, galleryInput].forEach((inp) => {
      if (!inp) return;
      if (inp === active) inp.name = fieldName;
      else inp.removeAttribute('name');
    });
  };

  /*프리뷰 표시 */
  const setPreview = (file) => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    // 선택 화면의 카드에도 보여줌
    previewImg.src = url;
    previewImg.style.display = 'block';
    // 확인 화면
    reviewImage.src = url;
    reviewImage.onload = () => { reviewImage.style.display = 'block'; placeholder.style.display = 'none'; };
  };

  /*파일 선택 공통 핸들러: 확인 화면으로 전환 */
  const onFileChange = (e, sourceLabel) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    activeInput = e.target;
    lastSource = sourceLabel;    // 'camera' | 'upload'
    ensureSingleName(activeInput);
    setPreview(file);
    // 라벨 변경
    btnAgain.textContent = (lastSource === 'upload') ? '다시 첨부' : '다시 촬영';
    // 확인 화면으로
    show('review');
  };

  /* 버튼 -> 파일 선택 열기 */
  btnCamera.addEventListener('click', () => {
    cameraInput.value = '';
    cameraInput.click();
  });
  btnGallery.addEventListener('click', () => {
    // Django 렌더 input 우선
    const target = djangoInput || galleryInput;
    target.setAttribute('accept', 'image/*');
    target.value = '';
    target.click();
  });

  cameraInput.addEventListener('change', (e)=> onFileChange(e, 'camera'));
  galleryInput.addEventListener('change', (e)=> onFileChange(e, 'upload'));
  if (djangoInput) djangoInput.addEventListener('change', (e)=> onFileChange(e, 'upload'));

  /*확인 화면: 다시/확인 */
  btnAgain.addEventListener('click', () => {
    if (lastSource === 'camera') {
      cameraInput.value = '';
      cameraInput.click();
    } else {
      const target = djangoInput || galleryInput;
      target.value = '';
      target.click();
    }
  });

  //'확인'을 누르면 바로 제출하지 말고 완료 화면을 먼저 보여줌
  btnConfirm.addEventListener('click', () => {
    show('done');  // 완료 화면
  });

  // 완료 화면에서 '성향 조사하기' 눌렀을 때 폼 제출
  btnGoSurvey.addEventListener('click', () => {
    form.requestSubmit();
  });

  /* 편의: 카드 클릭 시 갤러리 열기 */
  previewBox.addEventListener('click', () => btnGallery.click());

  /*드래그 방지 */
  ['dragstart','drop'].forEach(ev => {
    document.addEventListener(ev, (e)=> e.preventDefault());
  });
})();
