window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  let deferredPrompt = e;
  const installBtn = document.getElementById('install-btn');
  if (installBtn) installBtn.style.display = 'block';

  installBtn.addEventListener('click', () => {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(() => {
      deferredPrompt = null;
    });
  });
});
