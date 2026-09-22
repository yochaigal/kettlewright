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
    }
  } catch (_) {
    panel.querySelector('.party-members-status').textContent = panel.dataset.loadError;
  } finally {
    state.loading = false;
  }
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

  initializeStatEditor(panel, () => refreshPartyMembers(panel.dataset.partyId));
  refreshPartyMembers();
}
