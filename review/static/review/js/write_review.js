// 라벨에서 별/인풋을 제거하고 순수 텍스트만 얻기
function rvGetTextWithoutStars(node){
  const clone = node.cloneNode(true);
  clone.querySelectorAll('.label-stars, input').forEach(n => n.remove());
  // 혹시 텍스트에 ★가 섞여있어도 제거
  return clone.textContent.replace(/[★☆]/g, '').replace(/\s+/g,' ').trim();
}

function rvSyncGroupSelection(changedRadio){
  const group = document.querySelectorAll(`input[type="radio"][name="${changedRadio.name}"]`);
  group.forEach(r => r.closest('.rv-radio-card')?.classList.toggle('selected', r.checked));
}

/** 해당 단계의 '다음' 버튼 활성/비활성 */
function rvEnableNextIfChosen(stepEl){
  if (!stepEl) return;
  const nextBtn = stepEl.querySelector('.cta');
  if (!nextBtn) return;
  const hasChecked = !!stepEl.querySelector('input[type="radio"]:checked');
  nextBtn.disabled = !hasChecked;
}

/** 라디오들을 카드형으로 감싸고 선택/해제에 맞춰 UI와 버튼을 갱신 */
function rvEnhanceRadioCards(){
  document.querySelectorAll('.step .form-wrapper').forEach(wrapper => {
    const radios = Array.from(wrapper.querySelectorAll('input[type="radio"]'));
    if (!radios.length) return;

    // ★ Step6 대비: is_anonymous 체크박스를 먼저 잡아둔다(나중에 wrapper를 비워서 날아가므로)
    const anonInput = wrapper.querySelector('input[name="is_anonymous"]');
    const anonForLabel = anonInput ? wrapper.querySelector(`label[for="${anonInput.id}"]`) : null;
    const anonWrapLabel = anonInput ? anonInput.closest('label') : null;
    let anonLabelText = '익명으로 후기 작성하기';
    if (anonForLabel) anonLabelText = anonForLabel.textContent.replace(':','').trim();
    else if (anonWrapLabel) {
      const temp = anonWrapLabel.cloneNode(true);
      temp.querySelector('input')?.remove();
      anonLabelText = temp.textContent.replace(/\s+/g,' ').replace(':','').trim() || anonLabelText;
    }

    // 이미 카드화되어 있으면 버튼 상태만 갱신
    if (wrapper.querySelector('.rv-radio-card')) {
      rvEnableNextIfChosen(wrapper.closest('.step'));
      return;
    }

    // 라디오 → 카드화
    const list = document.createElement('div');
    list.className = 'rv-radio-list';

    radios.forEach(radio => {
      let forLabel = wrapper.querySelector(`label[for="${radio.id}"]`);
      let wrapLabel = radio.closest('label');

      // 별과 텍스트 분리
      let starFromFor  = forLabel?.querySelector('.label-stars');
      let starFromWrap = wrapLabel?.querySelector('.label-stars');
      let starEl = (starFromFor || starFromWrap) ? (starFromFor || starFromWrap).cloneNode(true) : null;

      let text = '';
      if (forLabel) {
        const clone = forLabel.cloneNode(true);
        clone.querySelectorAll('.label-stars, input').forEach(n => n.remove());
        text = clone.textContent.replace(/[★☆]/g,'').replace(/\s+/g,' ').trim();
        forLabel.remove();
      } else if (wrapLabel) {
        const clone = wrapLabel.cloneNode(true);
        clone.querySelector('input')?.remove();
        text = clone.textContent.replace(/[★☆]/g,'').replace(/\s+/g,' ').trim();
      } else {
        text = radio.value || '옵션';
      }

      const card = document.createElement('div');
      card.className = 'rv-radio-card';

      const row = document.createElement('div');
      row.className = 'rv-row';

      if (starEl) row.appendChild(starEl);

      const span = document.createElement('span');
      span.className = 'rv-label';
      span.textContent = text;
      row.appendChild(span);

      card.appendChild(radio);       // 원래 라디오를 카드 안으로 이동
      card.appendChild(row);
      list.appendChild(card);

      if (radio.checked) card.classList.add('selected');

      card.addEventListener('click', () => {
        radio.checked = true;
        rvSyncGroupSelection(radio);
        rvEnableNextIfChosen(card.closest('.step'));
      });
      radio.addEventListener('change', () => {
        rvSyncGroupSelection(radio);
        rvEnableNextIfChosen(radio.closest('.step'));
      });

      if (wrapLabel && wrapLabel !== card && wrapLabel.parentElement){
        try { wrapLabel.replaceWith(card); } catch {}
      }
    });

    // wrapper 비우고 라디오 리스트 삽입
    wrapper.innerHTML = '';
    wrapper.appendChild(list);

    // ★ 익명 토글 스위치 생성/삽입
    if (anonInput) {
      // 라벨 제거(있다면)
      anonForLabel?.remove();
      if (anonWrapLabel && anonWrapLabel !== anonInput) {
        try { anonWrapLabel.replaceWith(anonInput); } catch {}
      }

      // 실제 체크박스는 숨긴 뒤 row에 붙인다
      anonInput.classList.add('anon-input');

      const row = document.createElement('div');
      row.className = 'anon-row';

      const txt = document.createElement('span');
      txt.className = 'anon-text';
      txt.textContent = anonLabelText || '익명으로 후기 작성하기';

      const sw = document.createElement('button');
      sw.type = 'button';
      sw.className = 'switch';
      sw.setAttribute('role','switch');

      const sync = () => {
        sw.classList.toggle('on', !!anonInput.checked);
        sw.setAttribute('aria-checked', anonInput.checked ? 'true' : 'false');
      };
      sw.addEventListener('click', () => {
        anonInput.checked = !anonInput.checked;
        sync();
      });
      anonInput.addEventListener('change', sync);
      sync();

      row.appendChild(txt);
      row.appendChild(sw);
      row.appendChild(anonInput);   // 폼 제출을 위해 DOM에 포함

      wrapper.appendChild(row);
    }

    // 초기 다음 버튼 상태
    rvEnableNextIfChosen(wrapper.closest('.step'));
  });
}

document.addEventListener('DOMContentLoaded', () => {
    
  //텍스트 필드에 placeholder
   const ta4 = document.querySelector('#step4 textarea');
    if (ta4) ta4.placeholder = '직접 입력';
    const ta5 = document.querySelector('#step5 textarea');
    if (ta5) ta5.placeholder = '직접 입력';
    // --- DOM 요소 한번에 선언 ---
    const appWrapper = document.getElementById('app-wrapper'); 
    const form = document.getElementById('reviewForm');
    const progressBar = document.getElementById('progressBar');
    const headerBackLink = document.getElementById('headerBackLink');
    const steps = document.querySelectorAll('.step');
    const doneSection = document.getElementById('doneSection'); 
    const totalSteps = 6; // 실제 질문 스텝 수

    let currentStep = 1;

    // --- 이벤트 리스너 설정 ---
    // 헤더의 메인 뒤로가기 버튼
    headerBackLink.addEventListener('click', (event) => {
        event.preventDefault(); // a 태그의 기본 동작(href로 이동)을 막습니다.
        history.back();         // 브라우저의 이전 페이지로 이동합니다.
    });

    // --- 페이지 이동 및 UI 업데이트 함수 ---
    const goToStep = (stepNumber) => {
        currentStep = stepNumber;

        steps.forEach(step => step.classList.remove('active'));
        const activeStep = document.getElementById(`step${stepNumber}`);
        if (activeStep) {
            activeStep.classList.add('active');
        }
        if (doneSection) {
    if (stepNumber === 7) {
      doneSection.hidden = false;             // 완료 섹션 보이기
      appWrapper.classList.add('is-complete'); // 헤더/진행바 숨김
    } else {
      doneSection.hidden = true;
      appWrapper.classList.remove('is-complete');
    }
  }
        


        updateProgressBar();
        updateHeader();
        window.scrollTo(0, 0);
    };

    // --- 진행률 바 업데이트 ---
    const updateProgressBar = () => {
        const progress = Math.min(100, (currentStep / totalSteps) * 100);
        progressBar.style.width = `${progress}%`;
    };

    // --- 헤더 상태 업데이트 (메인 뒤로가기 버튼 표시 여부) ---
    const updateHeader = () => {
        const step1 = document.getElementById('step1');
        const isReviewScreen = step1 ? step1.classList.contains('is-review') : false;
        // 1단계의 첫 화면에서만 메인 뒤로가기 버튼을 보여줍니다.
        headerBackLink.style.display = (currentStep === 1 && !isReviewScreen) ? 'block' : 'none';
    };

    // --- 각 스텝의 버튼 기능 초기화 ---
    const initializeSteps = () => {
        steps.forEach(step => {
            const stepNum = parseInt(step.id.replace('step', ''));
            const nextBtn = step.querySelector(`button[data-action="next"]`);
            const backBtn = step.querySelector(`button[data-action="back"]`);

            // "다음" 버튼 클릭 이벤트
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    if (stepNum < 7) {
                        goToStep(stepNum + 1);
                    }
                });
            }

            // "이전" 버튼 클릭 이벤트
            if (backBtn) {
                backBtn.addEventListener('click', () => {
                    if (stepNum > 1) {
                        goToStep(stepNum - 1);
                    }
                });
            }

            // 스텝 유형에 따른 버튼 활성화 로직
            if ([2, 3, 6].includes(stepNum)) { // 라디오 버튼 스텝
                const radios = step.querySelectorAll('input[type="radio"]');
                radios.forEach(radio => {
                    radio.addEventListener('change', () => {
                        if (nextBtn) nextBtn.disabled = false;
                    });
                });
            } else if ([4, 5].includes(stepNum)) { // 텍스트 영역 스텝
                if (nextBtn) nextBtn.disabled = false;
            }
        });
    };

    // --- 3단계 별점 UI 추가 ---
    const setupStarRating = () => {
        const step3Labels = document.querySelectorAll('#step3 .form-wrapper label');
        // 이미 별점이 추가되었는지 확인하여 중복 추가 방지
        if (step3Labels.length > 0 && step3Labels[0].querySelector('.label-stars')) {
            return;
        }
        const ratingMap = { "매우 만족": 5, "만족": 4, "보통": 3, "불만족": 2, "매우 불만족": 1 };
        step3Labels.forEach(label => {
            const text = label.textContent.trim();
            const ratingValue = ratingMap[text];
            if (ratingValue) {
                const starSpan = document.createElement('span');
                starSpan.className = 'label-stars';
                starSpan.textContent = '★'.repeat(ratingValue);
                label.prepend(starSpan);
            }
        });
    };

    // --- 1단계: 계약서 첨부 로직 ---
    const setupStep1 = () => {
        const step1 = document.getElementById('step1');
        if (!step1) return;
        const introScreen = step1.querySelector('.intro');
        const reviewScreen = step1.querySelector('.view');
        const fileInput = form.querySelector('input[type="file"]');
        const btnCamera = document.getElementById('btnCamera');
        const btnGallery = document.getElementById('btnGallery');
        const btnAgain = document.getElementById('btnAgain');
        const btnBackIntro = reviewScreen.querySelector('[data-action="back-intro"]');
        const reviewImage = document.getElementById('reviewImage');
        const confirmBtn = reviewScreen.querySelector('button[data-action="next"]');

        let lastMode = 'gallery';

        const openPicker = (mode) => {
            lastMode = mode;
            if (mode === 'camera') {
                fileInput.setAttribute('capture', 'environment');
            } else {
                fileInput.removeAttribute('capture');
            }
            fileInput.click();
        };

        const showPreview = (file) => {
            if (file && file.type.startsWith('image/')) {
                reviewImage.src = URL.createObjectURL(file);
                step1.classList.add('is-review');
                reviewScreen.hidden = false;
                introScreen.hidden = true;
                confirmBtn.disabled = false;
                btnAgain.textContent = (lastMode === 'camera') ? '다시 촬영' : '다시 첨부';
                updateHeader();
            }
        };

        btnCamera.addEventListener('click', () => openPicker('camera'));
        btnGallery.addEventListener('click', () => openPicker('gallery'));
        fileInput.addEventListener('change', (e) => showPreview(e.target.files[0]));

        btnAgain.addEventListener('click', () => openPicker(lastMode));
        
        btnBackIntro.addEventListener('click', () => {
             step1.classList.remove('is-review');
             reviewScreen.hidden = true;
             introScreen.hidden = false;
             fileInput.value = ''; // 파일 선택 취소
             confirmBtn.disabled = true;
             updateHeader();
        });
        
        confirmBtn.disabled = true; // 초기에는 확인 버튼 비활성화
    };
    
    // --- 최종 제출 이벤트 ---
    form.addEventListener('submit', (e) => {
        // e.preventDefault(); // 테스트 시 제출 막기
        console.log('Form submitted');
    });

    // --- 모든 기능 초기화 실행 ---
    initializeSteps();
    setupStep1();
    setupStarRating();
    goToStep(1); // 첫 화면을 1번 스텝으로 설정
    rvEnhanceRadioCards();
});