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

const statKeys = ['hp', 'strength', 'dexterity', 'willpower'];

export function createTokenStats({editor, config, getApi, canReveal, confirmReveal, isPlayerPreview, updates}) {
  const layer = document.createElement('div'); layer.className = 'token-stats-layer';
  let actors = new Map(), nodes = new Map(), host = null, frame = null, stopped = false;
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
      if (node.actor && patchStats(node, actor)) {node.actor = actor; continue;}
      node.actor = actor; node.replaceChildren();
      node.setAttribute('aria-label', actor.name);
      const stats = document.createElement('span'); stats.className = 'token-stat-values';
      for (const key of statKeys) {
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
        button.addEventListener('click', event => {event.stopPropagation(); toggleVisibility(node.actor);});
      }
    }
    for (const [id, node] of nodes) if (!visible.has(id)) {node.remove(); nodes.delete(id);}
  }
  function patchStats(node, actor) {
    const previous = node.actor;
    // Shape/visibility changes may add or remove controls. Value changes stay in place.
    if (previous.kind !== actor.kind || previous.shared !== actor.shared
        || Boolean(previous.attack) !== Boolean(actor.attack)
        || statKeys.some(key => Boolean(previous.stats[key]) !== Boolean(actor.stats[key]))) return false;
    if (previous.name !== actor.name) node.setAttribute('aria-label', actor.name);
    const values = node.children[0].children;
    statKeys.filter(key => actor.stats[key]).forEach((key, index) => {
      if (previous.stats[key][0] !== actor.stats[key][0]) {
        values[index].textContent = `${{hp: 'HP', strength: 'STR', dexterity: 'DEX', willpower: 'WIL'}[key]} ${actor.stats[key][0]}`;
      }
    });
    const combat = node.children[1], armor = combat.children[0];
    if (previous.armor !== actor.armor) {
      armor.title = `${config.messages.armor} ${actor.armor}`;
      armor.setAttribute('aria-label', armor.title);
      armor.lastChild.textContent = ` ${actor.armor}`;
    }
    if (previous.attack !== actor.attack) combat.lastChild.textContent = ` · ${actor.attack}`;
    const button = node.querySelector('button');
    if (button) button.disabled = !canReveal() || saving.has(actor.id);
    return true;
  }
  const refresh = () => updates.refresh();
  const unsubscribe = updates.subscribe('stats', data => {
    if (stopped) return;
    // A failed permission refresh clears stale private stats.
    actors = new Map((data || []).map(actor => [actor.id,
      JSON.stringify(actors.get(actor.id)) === JSON.stringify(actor) ? actors.get(actor.id) : actor]));
    redraw();
  });
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
  const resize = new ResizeObserver(redraw); resize.observe(editor);
  return {redraw, refresh, reset() {nodes.forEach(node => node.remove()); nodes.clear(); redraw();}, destroy() {
    stopped = true; unsubscribe(); resize.disconnect();
    if (frame !== null) cancelAnimationFrame(frame); layer.remove(); actors.clear(); nodes.clear();
  }};
}
