// Excalidraw's scrollToContent rounds down to 10% zoom steps. Large realm
// drawings need a continuous fit to avoid losing much of the available space.
export function fittedViewport([left, top, right, bottom], width, height) {
  const value = Math.max(0.1, Math.min(30,
    width * 0.9 / Math.max(1, right - left),
    height * 0.9 / Math.max(1, bottom - top)));
  return {zoom: {value},
    scrollX: width / (2 * value) - (left + right) / 2,
    scrollY: height / (2 * value) - (top + bottom) / 2};
}
