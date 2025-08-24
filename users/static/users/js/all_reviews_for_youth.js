//백버튼 동작. 바로 직전 페이지로 이동
document.addEventListener("DOMContentLoaded", () => {
  const backBtn = document.getElementById("backBtn");
  if (!backBtn) return;

  backBtn.addEventListener("click", (e) => {
    e.preventDefault();

    const ref = document.referrer;
    if (!ref) return; // referrer 없으면 아무 동작 안 함

    let sameOrigin = false;
    try {
      sameOrigin = new URL(ref).origin === window.location.origin;
    } catch (_) {
      sameOrigin = false;
    }

    if (sameOrigin && history.length > 1) {
      history.back();
    }
  });
});