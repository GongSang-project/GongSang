// 스플래쉬 화면

document.addEventListener('DOMContentLoaded', () => {
  const splash = document.getElementById('splash');
  if (!splash) return;

  document.body.classList.add('splashing');

  setTimeout(() => {
    splash.classList.add('hidden');
    document.body.classList.remove('splashing');
  }, 3000);
});