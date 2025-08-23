function getParam(name) {
  const m = new URLSearchParams(location.search).get(name);
  return m ? decodeURIComponent(m) : null;
}

document.addEventListener("DOMContentLoaded", function () {
  const backBtn = document.getElementById("backBtn");
  if (!backBtn) return;

  backBtn.addEventListener("click", function () {
    const nextUrl = getParam("next");
    if (nextUrl) {
      location.href = nextUrl;
    } else if (
      document.referrer &&
      new URL(document.referrer).origin === location.origin
    ) {
      history.back();
    } else {
      location.href = backBtn.dataset.fallbackUrl;
    }
  });
});