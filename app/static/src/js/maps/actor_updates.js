// One viewer-specific HTTP snapshot for stats, artwork and roll permissions.
// Socket events trigger updates; polling only repairs missed notifications.
export function createActorUpdates({config, socket, denied = () => false}) {
  const listeners = new Map();
  let latest, stopped = false, running = null, again = false, timer, poll, placement;
  function publish(data) {
    latest = data;
    for (const [key, callbacks] of listeners) for (const callback of callbacks) callback(data?.[key] ?? null);
  }
  function refresh() {
    if (stopped || document.hidden) return Promise.resolve();
    if (running) {again = true; return running;}
    running = (async () => {
      try {
        const response = await fetch(config.actorsUrl + (config.boardContext?.scene_id ? '?scene_id=' + config.boardContext.scene_id : ''), {cache: 'no-store', signal: AbortSignal.timeout(10000)});
        if (stopped || denied(response)) return;
        if (!response.ok || response.redirected) throw new Error();
        const data = await response.json();
        if (!stopped) publish(data);
      } catch (_) {if (!stopped) publish(null);}
      finally {
        running = null;
        if (again) {again = false; schedule();}
      }
    })();
    return running;
  }
  function schedule() {
    if (!stopped && !timer && !document.hidden) timer = setTimeout(() => {timer = null; refresh();}, 100);
  }
  const changed = data => {if (data.party_id === config.partyId) schedule();};
  const visible = () => {if (!document.hidden) schedule();};
  function polling() {clearInterval(poll); poll = setInterval(() => refresh(), socket.connected ? 60000 : 15000);}
  const connected = () => {polling(); schedule();};
  socket.on('party_actors_changed', changed); socket.on('party_members_changed', changed);
  socket.on('connect', connected); socket.on('disconnect', polling);
  document.addEventListener('visibilitychange', visible);
  polling(); refresh();
  return {refresh,
    subscribe(key, callback) {
      if (!listeners.has(key)) listeners.set(key, new Set());
      listeners.get(key).add(callback);
      if (latest !== undefined) callback(latest?.[key] ?? null);
      return () => listeners.get(key)?.delete(callback);
    },
    placed(elements) {
      const next = [...new Set(elements.filter(e => !e.isDeleted && /^actor-(companion-)?\d+-/.test(e.id)).map(e => e.id))].sort().join();
      if (placement !== undefined && placement !== next) schedule();
      placement = next;
    },
    destroy() {
      stopped = true; clearTimeout(timer); clearInterval(poll); listeners.clear();
      socket.off('party_actors_changed', changed); socket.off('party_members_changed', changed);
      socket.off('connect', connected); socket.off('disconnect', polling);
      document.removeEventListener('visibilitychange', visible);
    }};
}
