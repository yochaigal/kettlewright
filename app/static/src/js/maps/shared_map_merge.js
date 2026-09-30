// Reapply only local changes since the acknowledged scene. Missing baseline
// elements are deletions; unrelated remote additions and edits remain intact.
export const sameDrawing = (a, b) => {
  if (a === b) return true;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  const keys = Object.keys(a);
  return keys.length === Object.keys(b).length && keys.every(key => Object.hasOwn(b, key) && sameDrawing(a[key], b[key]));
};

export function mergeDrawings(base, local, remote) {
  const before = new Map(base.elements.map(element => [element.id, element]));
  const ours = new Map(local.elements.map(element => [element.id, element]));
  const merged = new Map(remote.elements.map(element => [element.id, element]));
  for (const id of before.keys()) if (!ours.has(id)) merged.delete(id);
  for (const [id, element] of ours) {
    if (!sameDrawing(element, before.get(id))) merged.set(id, element);
  }
  // Keep remote stacking unless this client deliberately reordered old objects.
  const oldOrder = base.elements.filter(element => ours.has(element.id)).map(element => element.id);
  const localOrder = local.elements.filter(element => before.has(element.id)).map(element => element.id);
  const order = sameDrawing(oldOrder, localOrder) ? [...merged.keys()]
    : [...ours.keys(), ...merged.keys()];
  const elements = [...new Set(order)].filter(id => merged.has(id)).map(id => merged.get(id));
  const files = {...remote.files, ...local.files};
  const used = new Set(elements.filter(element => element.type === 'image').map(element => element.fileId));
  return {elements, files: Object.fromEntries(Object.entries(files).filter(([id]) => used.has(id))),
    appState: sameDrawing(local.appState, base.appState) ? remote.appState : local.appState};
}
