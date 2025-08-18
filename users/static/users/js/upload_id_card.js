(function () {
  /* 엘리먼트 */
  const form = document.getElementById('idForm');
  const djangoInput = form.querySelector('input[type="file"], input[name$="id_card_image"]') || null;
  const cameraInput = document.getElementById('cameraInput');
  const galleryInput = document.getElementById('galleryInput');
  const btnCamera = document.getElementById('btnCamera');
  const btnGallery = document.getElementById('btnGallery');
  const previewImg = document.getElementById('previewImage');
  const previewBox = document.getElementById('previewBox');

  /* 유틸: name 조정 (중복 전송 방지)*/
  const ensureSingleName = (active) => {
    const fieldName = (djangoInput && (djangoInput.name || djangoInput.id || 'id_card_image')) || 'id_card_image';
    // 활성 input만 name 유지, 나머지는 name 제거
    [djangoInput, cameraInput, galleryInput].forEach((inp) => {
      if (!inp) return;
      if (inp === active) {
        inp.name = fieldName;
      } else {
        inp.removeAttribute('name');
      }
    });
  };

  /* 미리보기 */
  const showPreview = (file) => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    previewImg.src = url;
    previewImg.style.display = 'block';
  };

  /* 이벤트: 버튼 클릭 -> 해당 input 오픈 */
  btnCamera.addEventListener('click', () => {
    ensureSingleName(cameraInput);
    cameraInput.value = ''; // 초기화
    cameraInput.click();
  });

  btnGallery.addEventListener('click', () => {
    // Django 렌더된 input 우선 사용 (accept 속성 보정)
    if (djangoInput) {
      djangoInput.setAttribute('accept', 'image/*');
      ensureSingleName(djangoInput);
      djangoInput.value = '';
      djangoInput.click();
    } else {
      ensureSingleName(galleryInput);
      galleryInput.value = '';
      galleryInput.click();
    }
  });

  /* 파일 선택 시 미리보기 + 자동 제출 */
  const onFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    showPreview(file);
    // 선택 후 바로 제출 (서버에서 검증/저장 후 다음 단계)
    // 필요 없으면 주석 처리
    form.requestSubmit();
  };

  cameraInput.addEventListener('change', onFileChange);
  galleryInput.addEventListener('change', onFileChange);
  if (djangoInput) djangoInput.addEventListener('change', onFileChange);

  /* 드래그 방지 (고정 사이즈라 스크롤/드래그 이슈 방지) */
  ['dragstart','drop'].forEach(ev => {
    document.addEventListener(ev, (e)=> e.preventDefault());
  });

  /*일러스트 영역 클릭 시 갤러리 열기(편의상 추가함) */
  previewBox.addEventListener('click', () => btnGallery.click());
})();
