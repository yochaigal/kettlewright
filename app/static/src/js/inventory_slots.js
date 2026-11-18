// Pointer events cover both mouse and touch. Keyboard movement uses the same API.
// Dropping on a container tab, or on the slots a carried container (a cart)
// takes up, moves the item into that container instead.
let selection = null;
let pointer = null;
let preview = null;

function clearSelection() {
  if (selection) {
    selection.root.querySelectorAll('.slot-picked, .slot-drop-target, .slot-container-target').forEach(element => {
      element.classList.remove('slot-picked', 'slot-drop-target', 'slot-container-target', 'is-full');
    });
    selection.root.classList.remove('slot-dragging-across');
    selection.root.querySelector('.slot-status').textContent = '';
    selection.handle.setAttribute('aria-pressed', 'false');
  }
  preview?.remove();
  preview = null;
  selection = null;
  pointer = null;
}

function targetSlot(slot) {
  if (!selection) return;
  selection.slot = Math.max(0, Math.min(slot, Number(selection.root.dataset.capacity) - selection.span));
  if (selection.span === 2) selection.slot -= selection.slot % 2;
  selection.root.querySelectorAll('.inventory-slot').forEach(row => {
    const start = Number(row.dataset.slot);
    row.classList.toggle('slot-drop-target', start < selection.slot + selection.span
      && start + Number(row.dataset.span) > selection.slot);
  });
  selection.root.querySelector('.slot-status').textContent =
    `${selection.root.dataset.moveHint} ${selection.root.dataset.slotLabel}: ${selection.slot + 1}`;
}

// The container under the pointer, if this item may go there.
function containerAt(x, y) {
  if (!selection?.size) return null;
  const target = document.elementFromPoint(x, y)?.closest('[data-drop-container]');
  return target && selection.root.contains(target) ? target : null;
}

function targetContainer(target) {
  if (!selection) return;
  selection.root.querySelectorAll('.slot-container-target').forEach(element => {
    if (element !== target) element.classList.remove('slot-container-target', 'is-full');
  });
  selection.container = target;
  if (!target) return;
  const full = Number(target.dataset.free) < selection.size;
  target.classList.add('slot-container-target');
  target.classList.toggle('is-full', full);
  selection.root.querySelectorAll('.slot-drop-target').forEach(row => row.classList.remove('slot-drop-target'));
  selection.root.querySelector('.slot-status').textContent = full ? selection.root.dataset.containerFull
    : `${selection.root.dataset.moveTo} ${target.dataset.dropName}`;
}

function pick(handle) {
  clearSelection();
  const row = handle.closest('.inventory-slot');
  selection = { handle, root: handle.closest('.slot-inventory'), itemId: handle.dataset.moveItem,
    slot: Number(row.dataset.slot), span: Number(row.dataset.span),
    size: Number(handle.dataset.moveAcross || 0), container: null };
  handle.setAttribute('aria-pressed', 'true');
  row.classList.add('slot-picked');
  targetSlot(selection.slot);
}

async function place() {
  if (!selection) return;
  const { root, itemId, slot, container } = selection;
  if (container && Number(container.dataset.free) < selection.size) {
    clearSelection();
    root.querySelector('.slot-status').textContent = root.dataset.containerFull;
    return;
  }
  clearSelection();
  root.classList.add('slot-saving');
  const values = { item_id: itemId, csrf_token: root.dataset.csrf, inventory_context: 'sheet' };
  if (container) values.container = container.dataset.dropContainer;
  else values.slot = slot;
  try {
    await window.htmx.ajax('POST', root.dataset.moveUrl, {
      source: root, target: '#inventory-container', swap: 'innerHTML', values,
    });
    document.querySelectorAll('[data-move-item]').forEach(handle => {
      if (handle.dataset.moveItem === itemId) handle.focus({ preventScroll: true });
    });
  } catch (_) {
    root.querySelector('.slot-status').textContent = root.dataset.moveError;
  } finally {
    root.classList.remove('slot-saving');
  }
}

document.addEventListener('pointerdown', event => {
  const handle = event.target.closest('[data-move-item]');
  if (!handle || event.button !== 0) return;
  pick(handle);
  pointer = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
  handle.setPointerCapture(event.pointerId);
});
document.addEventListener('pointermove', event => {
  if (!pointer || event.pointerId !== pointer.id || !selection) return;
  if (Math.hypot(event.clientX - pointer.x, event.clientY - pointer.y) < 5 && !pointer.moved) return;
  pointer.moved = true;
  if (!preview) {
    preview = document.createElement('div');
    preview.className = 'slot-drag-preview';
    preview.textContent = selection.handle.closest('.inventory-slot').querySelector('.slot-item-name').textContent;
    document.body.append(preview);
    if (selection.size) selection.root.classList.add('slot-dragging-across');
  }
  preview.style.left = `${event.clientX + 12}px`;
  preview.style.top = `${event.clientY + 12}px`;
  const container = containerAt(event.clientX, event.clientY);
  targetContainer(container);
  const row = container ? null : document.elementFromPoint(event.clientX, event.clientY)?.closest('.inventory-slot');
  if (row && selection.root.contains(row)) {
    const rect = row.getBoundingClientRect();
    targetSlot(Number(row.dataset.slot) + Math.min(Number(row.dataset.span) - 1,
      Math.floor((event.clientX - rect.left) / (rect.width / Number(row.dataset.span)))));
  }
  // Let long inventories scroll while dragging near the viewport edges. In the whiteboard's
  // party panel the page scrolls inside <body>, not the window (#407).
  const scroller = document.documentElement.classList.contains('board-embedded') ? document.body : window;
  if (event.clientY < 60) scroller.scrollBy(0, -12);
  else if (event.clientY > window.innerHeight - 60) scroller.scrollBy(0, 12);
});
document.addEventListener('pointerup', event => {
  if (!pointer || event.pointerId !== pointer.id) return;
  const moved = pointer.moved;
  pointer = null;
  if (moved) {
    targetContainer(containerAt(event.clientX, event.clientY));
    const row = document.elementFromPoint(event.clientX, event.clientY)?.closest('.inventory-slot');
    if (selection?.container || (row && selection?.root.contains(row))) place();
    else clearSelection();
  }
});
document.addEventListener('pointercancel', clearSelection);
document.addEventListener('click', event => {
  if (!selection) return;
  if (event.target.closest('[data-move-item]')) return;
  // Picked with a click: a click on a container tab or a cart moves it there.
  const container = containerAt(event.clientX, event.clientY);
  if (container) {
    event.preventDefault();
    event.stopImmediatePropagation();
    targetContainer(container);
    place();
    return;
  }
  const row = event.target.closest('.inventory-slot');
  if (row && selection.root.contains(row)) {
    event.preventDefault();
    event.stopImmediatePropagation();
    targetSlot(Number(row.dataset.slot));
    place();
  } else clearSelection();
}, true);
document.addEventListener('keydown', event => {
  const handle = event.target.closest('[data-move-item]');
  if (!handle || !['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'Enter', ' ', 'Escape'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'Escape') return clearSelection();
  const alreadySelected = selection?.handle === handle;
  if (!alreadySelected) pick(handle);
  if (event.key === 'ArrowUp') targetSlot(selection.slot - 2);
  else if (event.key === 'ArrowDown') targetSlot(selection.slot + 2);
  else if (event.key === 'ArrowLeft') targetSlot(selection.slot - selection.span);
  else if (event.key === 'ArrowRight') targetSlot(selection.slot + selection.span);
  else if (event.key === 'Home') targetSlot(0);
  else if (event.key === 'End') targetSlot(Number(selection.root.dataset.capacity) - selection.span);
  else if (alreadySelected) place();
});
['htmx:responseError', 'htmx:sendError'].forEach(name => {
  document.addEventListener(name, event => {
    const root = event.detail.elt.closest('.slot-inventory');
    if (root) root.querySelector('.slot-status').textContent = root.dataset.moveError;
  });
});
document.addEventListener('htmx:beforeSwap', event => {
  if (event.detail.target.id === 'inventory-container') clearSelection();
});
