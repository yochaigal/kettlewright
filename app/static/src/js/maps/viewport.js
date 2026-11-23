// Excalidraw's scrollToContent rounds down to 10% zoom steps. Large realm
// drawings need a continuous fit to avoid losing much of the available space.
export function fittedViewport([left, top, right, bottom], width, height) {
  // Never zoom in past 100%: a lone pin or a small sketch stays readable, not huge.
  const value = Math.max(0.1, Math.min(1,
    width * 0.9 / Math.max(1, right - left),
    height * 0.9 / Math.max(1, bottom - top)));
  return {zoom: {value},
    scrollX: width / (2 * value) - (left + right) / 2,
    scrollY: height / (2 * value) - (top + bottom) / 2};
}

// An image map (#506): the picture fills the frame (contain), with no margin and no 100% cap.
export function imageViewport([left, top, right, bottom], width, height) {
  const value = Math.max(0.01, Math.min(width / Math.max(1, right - left), height / Math.max(1, bottom - top)));
  return {zoom: {value}, scrollX: width / (2 * value) - (left + right) / 2, scrollY: height / (2 * value) - (top + bottom) / 2};
}

// Keeps an image map's view inside the picture: never smaller than it fits, never panned past its edges.
// Returns the corrected {zoom, scrollX, scrollY}, or null when the view is already inside.
export function clampToImage([left, top, right, bottom], {width, height, zoom, scrollX, scrollY}) {
  const fit = imageViewport([left, top, right, bottom], width, height);
  const value = Math.max(zoom.value, fit.zoom.value);
  const axis = (scroll, size, low, high) => {
    const span = size / value;
    if (high - low <= span) return span / 2 - (low + high) / 2;  // Smaller than the frame: centred.
    return Math.min(-low, Math.max(span - high, scroll));
  };
  const next = {zoom: {value}, scrollX: axis(scrollX, width, left, right), scrollY: axis(scrollY, height, top, bottom)};
  const same = Math.abs(value - zoom.value) < 1e-6 && Math.abs(next.scrollX - scrollX) < 0.5 && Math.abs(next.scrollY - scrollY) < 0.5;
  return same ? null : next;
}

// An image map's picture size, for a frame of the same shape (#506); null when there is no picture.
export function imageAspect(drawing) {
  const image = drawing?.elements?.find(element => element.type === 'image' && !element.isDeleted);
  return image && image.width > 0 && image.height > 0 ? image.width / image.height : null;
}
