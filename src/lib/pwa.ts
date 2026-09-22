if ('serviceWorker' in navigator && (window.isSecureContext || window.location.hostname === 'localhost')) {
  window.addEventListener('load', () => {
    const baseUrl = new URL(import.meta.env.BASE_URL, window.location.origin);
    const serviceWorkerUrl = new URL('service-worker.js', baseUrl);

    void navigator.serviceWorker.register(serviceWorkerUrl, {
      scope: baseUrl.pathname,
    }).catch((error: unknown) => {
      console.warn('[Arteteca] No se pudo registrar el modo instalable.', error);
    });
  });
}
