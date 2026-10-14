// Stats are a viewer-specific overlay, never serialized into the shared drawing.
export function actorKey(id) {
  const companion = id.match(/^actor-companion-(\d+)-/);
  if (companion) return `companion:${companion[1]}`;
  return id.match(/^actor-(\d+)-/)?.[1] || null;
}

export function tokenStatsPosition(element, state) {
  const zoom = state.zoom.value, angle = element.angle || 0;
  const height = Math.abs(element.width * Math.sin(angle)) + Math.abs(element.height * Math.cos(angle));
  // Party tokens start at 80 scene units. Resize the whole block with the token,
  // including its spacing, and then apply the camera zoom without a size floor.
  const scale = Math.min(element.width, element.height) / 80 * zoom;
  return {x: (element.x + element.width / 2 + state.scrollX) * zoom,
    y: (element.y + element.height / 2 + height / 2 + state.scrollY) * zoom + 2 * scale,
    scale};
}

export function createTokenStats({editor, config, getApi, canReveal, confirmReveal, isPlayerPreview, socket}) {
  const layer = document.createElement('div'); layer.className = 'token-stats-layer';
  let actors = new Map(), nodes = new Map(), host = null, frame = null, epoch = 0, stopped = false;
  const saving = new Set();
  function redraw() {if (!stopped && frame === null) frame = requestAnimationFrame(draw);}
  function draw() {
    frame = null;
    const api = getApi(), nextHost = editor.querySelector('.excalidraw');
    if (!api || !nextHost || stopped) return;
    if (host !== nextHost) {host = nextHost; host.append(layer);}
    const state = api.getAppState(), visible = new Set();
    for (const element of api.getSceneElements()) {
      const actor = actors.get(actorKey(element.id));
      if (!actor || element.isDeleted || element.opacity === 0 || (isPlayerPreview() && actor.kind === 'monster' && !actor.shared)) continue;
      const position = tokenStatsPosition(element, state);
      if (position.x < -160 * position.scale || position.x > state.width + 160 * position.scale
          || position.y < -80 * position.scale || position.y > state.height) continue;
      visible.add(element.id);
      let node = nodes.get(element.id);
      if (!node) {
        node = document.createElement('div'); node.className = 'token-stats';
        nodes.set(element.id, node); layer.append(node);
      }
      Object.assign(node.style, {left: `${position.x}px`, top: `${position.y}px`,
        transform: `translateX(-50%) scale(${position.scale})`});
      // Reuse DOM while moving a token so buttons keep their focus and pointer target.
      if (node.actor === actor) {
        const button = node.querySelector('button');
        if (button) button.disabled = !canReveal() || saving.has(actor.id);
        continue;
      }
      node.actor = actor; node.replaceChildren();
      node.setAttribute('aria-label', actor.name);
      const stats = document.createElement('span'); stats.className = 'token-stat-values';
      for (const key of ['hp', 'strength', 'dexterity', 'willpower']) {
        if (!actor.stats[key]) continue;
        const value = document.createElement('span');
        value.textContent = `${{hp: 'HP', strength: 'STR', dexterity: 'DEX', willpower: 'WIL'}[key]} ${actor.stats[key][0]}`;
        stats.append(value);
      }
      node.append(stats);
      const combat = document.createElement('small');
      const armor = document.createElement('span'); armor.title = `${config.messages.armor} ${actor.armor}`;
      armor.setAttribute('aria-label', armor.title);
      const shield = document.createElement('i'); shield.className = 'fa-solid fa-shield-halved'; shield.setAttribute('aria-hidden', 'true');
      armor.append(shield, document.createTextNode(` ${actor.armor}`));
      combat.append(armor);
      if (actor.attack) combat.append(document.createTextNode(` · ${actor.attack}`));
      node.append(combat);
      if (config.warden && !isPlayerPreview() && actor.kind === 'monster') {
        const button = document.createElement('button'); button.type = 'button';
        button.title = button.ariaLabel = config.messages[actor.shared ? 'hideStats' : 'showStats'];
        button.setAttribute('aria-pressed', String(actor.shared));
        button.disabled = !canReveal() || saving.has(actor.id);
        const icon = document.createElement('i'); icon.className = `fa-solid ${actor.shared ? 'fa-eye' : 'fa-eye-slash'}`;
        icon.setAttribute('aria-hidden', 'true'); button.append(icon); node.append(button);
        button.addEventListener('pointerdown', event => event.stopPropagation());
        button.addEventListener('click', event => {event.stopPropagation(); toggleVisibility(actor);});
      }
    }
    for (const [id, node] of nodes) if (!visible.has(id)) {node.remove(); nodes.delete(id);}
  }
  async function refresh() {
    if (stopped) return;
    const run = ++epoch;
    try {
      const response = await fetch(config.statsUrl, {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (!response.ok || response.redirected) throw new Error();
      const data = await response.json();
      if (run !== epoch || stopped) return;
      actors = new Map(data.actors.map(actor => [actor.id, actor]));
    } catch (_) {
      // Clear stale stats, including permissions revoked while the connection was lost.
      if (run !== epoch || stopped) return;
      actors.clear();
    }
    redraw();
  }
  async function toggleVisibility(actor) {
    if (!canReveal() || saving.has(actor.id)) return;
    saving.add(actor.id); redraw();
    try {
      if (!actor.shared && !await confirmReveal(actor)) return;
      if (stopped || !canReveal()) return;
      const id = actor.id.split(':')[1];
      const response = await fetch(config.visibilityUrl.replace('/0/visibility', `/${id}/visibility`), {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({shared: !actor.shared, csrf_token: config.csrfToken}), signal: AbortSignal.timeout(10000),
      });
      if (!response.ok || response.redirected) throw new Error();
      await refresh();
    } catch (_) {getApi()?.setToast({message: config.messages.visibilityFailed});}
    finally {saving.delete(actor.id); redraw();}
  }
  function changed(data) {
    if (data.party_id !== config.partyId) return;
    actors.clear(); redraw(); refresh();
  }
  const connected = () => refresh();
  const visible = () => {if (!document.hidden) refresh();};
  socket.on('party_actors_changed', changed); socket.on('party_members_changed', changed); socket.on('connect', connected);
  document.addEventListener('visibilitychange', visible);
  const timer = setInterval(refresh, 5000), resize = new ResizeObserver(redraw); resize.observe(editor);
  refresh();
  return {redraw, refresh, reset() {nodes.forEach(node => node.remove()); nodes.clear(); redraw();}, destroy() {
    stopped = true; ++epoch; clearInterval(timer); resize.disconnect();
    socket.off('party_actors_changed', changed); socket.off('party_members_changed', changed); socket.off('connect', connected);
    document.removeEventListener('visibilitychange', visible);
    if (frame !== null) cancelAnimationFrame(frame); layer.remove(); actors.clear(); nodes.clear();
  }};
}
