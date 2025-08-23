document.addEventListener('DOMContentLoaded', function () {

  //점수바 채우기
  const bar  = document.querySelector('.score-bar');
  const fill = document.querySelector('.score-fill');
  const bubbleImg = document.querySelector('.score');
  const bubbleTxt = document.querySelector('.score-text');

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
});