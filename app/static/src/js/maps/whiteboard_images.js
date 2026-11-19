// A whiteboard holds 12 MB of images (#386). Excalidraw keeps a pasted map as a PNG of up to
// 1440 px, often several MB, so a few maps filled a board and every later save was refused.
// Large PNG and JPEG images, and SVG (which the server does not take), become WebP before they
// are saved. Tokens and other small images stay as they are.
export const COMPRESS_ABOVE = 600 * 1024; // characters of data URL, about 450 KB of image
const MAX_SIDE = 1440;
const SVG = 'image/svg+xml';

export function needsCompression(file) {
  return Boolean(file) && typeof file.dataURL === 'string'
    && (file.mimeType === SVG || ['image/png', 'image/jpeg'].includes(file.mimeType) && file.dataURL.length > COMPRESS_ABOVE);
}

// Draws the image on a canvas and encodes it as WebP (PNG where the browser cannot encode WebP).
// `size` is the image's size on the board, for SVGs that do not state their own.
export async function encodeImage(file, size = {}, quality = 0.85) {
  const image = new Image();
  image.src = file.dataURL;
  await image.decode();
  let width = image.naturalWidth || size.width || 1024, height = image.naturalHeight || size.height || 1024;
  // SVGs are drawn at twice their board size so they stay sharp when zoomed in.
  if (file.mimeType === SVG && size.width && size.height) [width, height] = [size.width * 2, size.height * 2];
  const scale = Math.min(1, MAX_SIDE / Math.max(width, height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(width * scale)); canvas.height = Math.max(1, Math.round(height * scale));
  canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
  const webp = canvas.toDataURL('image/webp', quality);
  return webp.startsWith('data:image/webp;') ? {mimeType: 'image/webp', dataURL: webp}
    : {mimeType: 'image/png', dataURL: canvas.toDataURL('image/png')};
}

// busy(drawing, base) starts compressing new large images and reports whether any are still
// being compressed (or waiting to be swapped in), so the board holds its save until they are done.
// Once an image is compressed, its elements point at the smaller copy; undo that brings the
// original back gets the same copy again.
export function createImageCompressor({getApi, captureUpdate, onSettled, encode = encodeImage,
  newId = () => crypto.randomUUID().replaceAll('-', '')}) {
  const done = new Map(), running = new Set();
  let stopped = false;
  function swap(id) {
    const api = getApi(), file = done.get(id);
    if (!api || !file) return;
    api.addFiles([file]);
    api.updateScene({captureUpdate, elements: api.getSceneElements().map(element =>
      element.fileId === id ? {...element, fileId: file.id, version: element.version + 1} : element)});
  }
  async function start(id, file, size) {
    running.add(id);
    try {
      const result = await encode(file, size);
      // A PNG that does not get smaller is kept; an SVG is always converted, or the server refuses it.
      if (file.mimeType === SVG || result.dataURL.length < file.dataURL.length) {
        done.set(id, {...result, id: newId(), created: Date.now()});
      } else done.set(id, null);
    } catch (_) {
      done.set(id, null);
    } finally {
      running.delete(id);
      if (!stopped) {swap(id); onSettled();}
    }
  }
  function busy(drawing, base) {
    let waiting = false;
    for (const [id, file] of Object.entries(drawing.files)) {
      if (base?.files?.[id] || done.get(id) === null || !needsCompression(file)) continue;
      waiting = true;
      if (done.has(id)) swap(id);
      else if (!running.has(id)) {
        const element = drawing.elements.find(item => item.fileId === id);
        start(id, file, {width: element?.width, height: element?.height});
      }
    }
    return waiting;
  }
  return {busy, destroy() {stopped = true;}};
}
