// Transient collaborator pointers use Excalidraw's native laser renderer.
// They never enter the scene save queue or survive a socket reconnection.
export function createLaserSync({socket, getApi, getGeneration, config, canSend, now = Date.now}) {
  const peers = new Map();
  let lastSent = -Infinity, active = false, pending = null, trailing = null;
  function publish() {
    const api = getApi();
    if (api) api.updateScene({collaborators: new Map([...peers].map(([id, peer]) => [id, peer.value]))});
  }
  function send() {
    trailing = null;
    if (!pending || !socket.connected || !canSend()) {pending = null; return;}
    socket.volatile.emit('whiteboard_laser', {...pending, party_id: config.partyId,
      generation: getGeneration(), csrf_token: config.csrfToken});
    lastSent = now(); pending = null;
  }
  function pointerUpdate({pointer, button}) {
    const laser = pointer?.tool === 'laser';
    if (!laser && !active) return;
    active = laser;
    pending = {pointer: laser ? {x: pointer.x, y: pointer.y, tool: 'laser'} : null, button};
    if (now() - lastSent >= 40) {clearTimeout(trailing); send();}
    else if (!trailing) trailing = setTimeout(send, 40 - (now() - lastSent));
  }
  function stop() {if (active) pointerUpdate({pointer: null, button: 'up'});}
  function clear() {
    clearTimeout(trailing); trailing = null; pending = null; active = false;
    if (peers.size) {peers.clear(); publish();}
  }
  socket.on('whiteboard_laser', data => {
    if (data.party_id !== config.partyId || data.generation !== getGeneration() || !getApi()) return;
    if (data.pointer) peers.set(data.sender, {time: now(), value: {
      pointer: data.pointer, button: data.button, username: data.username, color: {background: '#e8590c', stroke: '#e8590c'},
    }});
    else peers.delete(data.sender);
    publish();
  });
  socket.on('disconnect', clear);
  const expiry = setInterval(() => {
    let changed = false;
    for (const [id, peer] of peers) if (now() - peer.time > 1500) {peers.delete(id); changed = true;}
    if (changed) publish();
  }, 500);
  return {pointerUpdate, stop, clear, destroy() {clear(); clearInterval(expiry);}};
}
