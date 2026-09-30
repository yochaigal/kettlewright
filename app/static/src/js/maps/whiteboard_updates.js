// Apply a server delta only to its exact acknowledged base revision.
// A missing/reordered packet requests an authoritative HTTP resync instead.
export function stateFromUpdate(event, current) {
  if (event.generation < current.generation) return current;
  if (event.update?.state) return event.update.state;
  if (!event.update || event.generation !== current.generation) return null;
  let drawing = current.drawing;
  if (event.version > current.version) {
    const delta = event.update.drawing;
    if (!delta || delta.base_version !== current.version || !drawing) return null;
    const elements = new Map(drawing.elements.map(element => [element.id, element]));
    for (const element of delta.elements) elements.set(element.id, element);
    if (delta.order.some(id => !elements.has(id))) return null;
    const ordered = delta.order.map(id => elements.get(id));
    const files = {...drawing.files, ...delta.files};
    const used = new Set(ordered.filter(element => element.type === 'image').map(element => element.fileId));
    if ([...used].some(id => !files[id])) return null;
    drawing = {elements: ordered, files: Object.fromEntries(Object.entries(files).filter(([id]) => used.has(id))), appState: delta.appState};
  }
  if (event.fog_version > current.fog_version && !event.update.fog) return null;
  return {generation: current.generation, version: Math.max(event.version, current.version), drawing,
    fog: event.fog_version > current.fog_version ? event.update.fog : current.fog,
    fog_version: Math.max(event.fog_version, current.fog_version)};
}
