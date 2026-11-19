// The whiteboard inside a Discord Activity (#423). Runs before the board's modules.
// Discord's CSP allows no inline script, so the settings the site writes inline are made here.
(function () {
  const script = document.currentScript;
  // Excalidraw loads its fonts from here: esm.sh, through Discord's /esm URL mapping.
  // It must be absolute, or Excalidraw falls back to its CDN, which the CSP blocks.
  window.EXCALIDRAW_ASSET_PATH = new URL(script.dataset.assetPath, location.href).href;
  // Excalidraw also lists esm.sh itself as a fallback for each font. The CSP refuses it, so drop it:
  // otherwise the browser tries it too and logs a refusal for every font.
  const NativeFontFace = window.FontFace;
  window.FontFace = function FontFace(family, source, descriptors) {
    if (typeof source === 'string') {
      source = source.split(/,\s*(?=url\()/).filter(part => !part.includes('https://esm.sh/')).join(', ') || source;
    }
    return new NativeFontFace(family, source, descriptors);
  };
  window.FontFace.prototype = NativeFontFace.prototype;
  const config = JSON.parse(document.getElementById('shared-map-config').textContent);
  // There is no cookie session inside Discord: every request to Kettlewright carries the board's token.
  // The server accepts it for this party's whiteboard only (app/lib/activity.py).
  const send = window.fetch.bind(window);
  window.fetch = function (input, init) {
    const request = new Request(input instanceof Request ? input : new URL(input, location.href), init);
    if (new URL(request.url).origin !== location.origin) return send(request);
    const headers = new Headers(request.headers);
    headers.set('Authorization', 'Bearer ' + config.activityToken);
    return send(new Request(request, {headers}));
  };
  // The site shows this when the board's modules fail to load; it does so with an inline script.
  window.addEventListener('error', event => {
    if (event.target instanceof HTMLScriptElement) {
      document.getElementById('map-status').textContent = config.messages.loadFailed;
    }
  }, true);
})();
