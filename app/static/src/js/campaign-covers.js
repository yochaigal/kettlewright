// Campaign covers sit in wide frames (#430). Cropping portrait art there, such as
// a printed adventure cover, keeps only a sliver of its middle and the edge of
// its border. Show the whole picture instead, over a blurred copy that fills the
// frame. Landscape pictures keep the plain crop.

export function isPortrait(width, height) {
  return width > 0 && height > width;
}

export function fitCover(img) {
  const frame = img.parentElement;
  if (!frame || frame.classList.contains('cover-portrait') || !isPortrait(img.naturalWidth, img.naturalHeight)) return;
  const backdrop = img.cloneNode();
  backdrop.removeAttribute('data-cover');
  backdrop.removeAttribute('loading');
  backdrop.className = 'cover-backdrop';
  backdrop.alt = '';
  backdrop.setAttribute('aria-hidden', 'true');
  img.before(backdrop);
  frame.classList.add('cover-portrait');
}

if (typeof document !== 'undefined') {
  for (const img of document.querySelectorAll('img[data-cover]')) {
    if (img.complete) fitCover(img);
    else img.addEventListener('load', () => fitCover(img), {once: true});
  }
}
