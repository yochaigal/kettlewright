// Keep the upstream files intact, including older Excalidraw v1 libraries.
export function libraryItems(data, name) {
  if (data.type !== 'excalidrawlib') throw new Error('Invalid Excalidraw library');
  if (data.version === 2 && Array.isArray(data.libraryItems)) return data.libraryItems;
  if (data.version === 1 && Array.isArray(data.library)) {
    return data.library.map((elements, index) => ({
      id: `${name}-${index}`, status: 'published', created: 0, elements,
    }));
  }
  throw new Error('Unsupported Excalidraw library version');
}

export const MAP_LIBRARIES = ['architecture', 'maps', 'creatures', 'planning'];
const baseUrl = new URL('../../../vendor/excalidraw-libraries/', import.meta.url);

export async function loadLibraries(names = MAP_LIBRARIES, url = baseUrl) {
  const results = await Promise.allSettled(names.map(async name => {
    const response = await fetch(new URL(`${name}.excalidrawlib`, url), {signal: AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error('Library failed');
    return libraryItems(await response.json(), name);
  }));
  return {
    items: results.flatMap(result => result.status === 'fulfilled' ? result.value : []),
    failed: results.some(result => result.status === 'rejected'),
  };
}
