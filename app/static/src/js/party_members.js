import { initializeStatEditor, updateStatElement } from "./quick_stats.js";

// Keep one authoritative snapshot, and preserve inputs while a player is editing.
const states = new WeakMap();

function stateFor(panel) {
  if (!states.has(panel)) states.set(panel, { loading: false, dirty: false });
  return states.get(panel);
}

function isEditing(member) {
  return member.contains(document.activeElement) || member.querySelector('[data-saving], [data-edited]');
}

function updateMember(existing, incoming) {
  if (!isEditing(existing)) {
    existing.replaceWith(incoming);
    return;
  }
  // Presence still updates while a stat is being edited.
  if (incoming.dataset.online !== undefined) existing.dataset.online = incoming.dataset.online;
  const oldStats = existing.querySelectorAll('.party-member-stat');
  incoming.querySelectorAll('.party-member-stat').forEach((stat, index) => {
    updateStatElement(oldStats[index], stat);
  });
  for (const selector of ['.party-member-identity', '.party-member-slots']) {
    const old = existing.querySelector(selector);
    if (!old.contains(document.activeElement)) old.replaceWith(incoming.querySelector(selector));
  }
}

export async function refreshPartyMembers(partyId = null) {
  const panel = document.getElementById('party-members');
  if (!panel || (partyId !== null && String(partyId) !== panel.dataset.partyId)) return;
  const state = stateFor(panel);
  state.dirty = true;
  if (state.loading) return;
  state.loading = true;
  try {
    while (state.dirty && panel.isConnected) {
      state.dirty = false;
      const response = await fetch(panel.dataset.membersUrl, { cache: 'no-store' });
      if (!response.ok || response.redirected) {
        if (response.redirected || response.status === 404 || response.status === 403) {
          panel.querySelector('#party-members-content').replaceChildren();
        }
        throw new Error('Party refresh failed');
      }
      const template = document.createElement('template');
      template.innerHTML = await response.text();
      if (!panel.isConnected) return;
      const content = panel.querySelector('#party-members-content');
      const current = new Map([...content.querySelectorAll('[data-character-id]')]
        .map(member => [member.dataset.characterId, member]));
      // Reuse focused/unsaved rows; do not blur inputs on every socket event.
      const next = [...template.content.children];
      for (const incoming of next) {
        const existing = current.get(incoming.dataset.characterId);
        if (existing) {
          updateMember(existing, incoming);
          current.delete(incoming.dataset.characterId);
        } else {
          content.append(incoming);
        }
      }
      for (const removed of current.values()) removed.remove();
      // Remove an obsolete empty-state message when the first member joins.
      if (next.some(node => node.dataset.characterId)) {
        content.querySelectorAll(':scope > p').forEach(node => node.remove());
      } else {
        content.replaceChildren(...next);
      }
      applyConnectedFilter(panel);
    }
  } catch (_) {
    panel.querySelector('.party-members-status').textContent = panel.dataset.loadError;
  } finally {
    state.loading = false;
  }
}

// "Connected only" (#424): the Warden hides characters whose players do not have
// Kettlewright open. The members list marks each card data-online; the party
// actions' pickers follow it, so a hidden character is never ticked by default.
const connectedKey = panel => `party-connected-only-${panel.dataset.partyId}`;

function connectedOnly(panel) {
  return panel.querySelector('[data-connected-only]')?.getAttribute('aria-pressed') === 'true';
}

export function applyConnectedFilter(panel = document.getElementById('party-members')) {
  if (!panel) return;
  const enabled = connectedOnly(panel);
  panel.classList.toggle('party-connected-only', enabled);
  const offline = new Set([...panel.querySelectorAll('[data-character-id][data-online="0"]')]
    .map(member => member.dataset.characterId));
  const summary = panel.querySelector('.party-presence-summary');
  if (summary) {
    const total = panel.querySelectorAll('[data-character-id][data-online]').length;
    summary.hidden = !enabled;
    summary.textContent = summary.dataset.template
      .replace('%(connected)s', String(total - offline.size)).replace('%(hidden)s', String(offline.size));
  }
  document.querySelectorAll('.wilderness-choice input[name="participants"]').forEach(input => {
    const hide = enabled && offline.has(input.value);
    const label = input.closest('.wilderness-choice');
    if (hide && !label.hidden) {
      input.dataset.wasChecked = String(input.checked);
      input.checked = false;
    } else if (!hide && label.hidden && input.dataset.wasChecked !== undefined) {
      input.checked = input.dataset.wasChecked === 'true';
    }
    label.hidden = hide;
    input.disabled = hide;
  });
}

export function initializePartyMembers() {
  const panel = document.getElementById('party-members');
  if (!panel || panel.dataset.initialized) return;
  panel.dataset.initialized = 'true';
  const storageKey = `party-layout-${panel.dataset.partyId}`;
  function setLayout(layout) {
    panel.classList.toggle('party-compact', layout === 'compact');
    panel.querySelectorAll('[data-party-layout]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.partyLayout === layout));
    });
  }
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved === 'cards' || saved === 'compact') setLayout(saved);
  } catch (_) { /* Storage is optional. */ }
  panel.querySelectorAll('[data-party-layout]').forEach(button => {
    button.addEventListener('click', () => {
      setLayout(button.dataset.partyLayout);
      try { localStorage.setItem(storageKey, button.dataset.partyLayout); } catch (_) { /* Optional. */ }
    });
  });

  const toggle = panel.querySelector('[data-connected-only]');
  if (toggle) {
    try { toggle.setAttribute('aria-pressed', String(localStorage.getItem(connectedKey(panel)) === 'on')); } catch (_) { /* Optional. */ }
    toggle.addEventListener('click', () => {
      const enabled = !connectedOnly(panel);
      toggle.setAttribute('aria-pressed', String(enabled));
      try { localStorage.setItem(connectedKey(panel), enabled ? 'on' : 'off'); } catch (_) { /* Optional. */ }
      applyConnectedFilter(panel);
      if (enabled) refreshPartyMembers(panel.dataset.partyId);
    });
    // Presence changes are not pushed: check again every 30 seconds while the page is visible.
    setInterval(() => { if (!document.hidden) refreshPartyMembers(panel.dataset.partyId); }, 30000);
  }
  applyConnectedFilter(panel);

  initializeStatEditor(panel, () => refreshPartyMembers(panel.dataset.partyId));
  refreshPartyMembers();
}
