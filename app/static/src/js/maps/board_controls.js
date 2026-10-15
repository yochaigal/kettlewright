import {restoreElements, CaptureUpdateAction} from 'excalidraw';
import diceModal from '../dice_modal.js';

export function setupBoardControls({config, getApi, canEdit}) {
  const panel = document.getElementById('party-panel'), frame = document.getElementById('party-frame');
  const partyButton = document.getElementById('board-party');
  const warning = document.getElementById('reveal-stats-confirm');
  let resolveReveal = null;
  function finishReveal(confirmed = false) {
    const resolve = resolveReveal; resolveReveal = null;
    warning?.close(); resolve?.(confirmed);
  }
  function confirmReveal(actor) {
    if (!warning || resolveReveal) return Promise.resolve(false);
    document.getElementById('reveal-monster-name').textContent = actor.name;
    return new Promise(resolve => {resolveReveal = resolve; warning.showModal();});
  }
  warning?.addEventListener('close', () => {if (!warning.open) finishReveal();});
  warning?.addEventListener('cancel', event => {event.preventDefault(); finishReveal();});
  document.getElementById('cancel-reveal-stats')?.addEventListener('click', () => finishReveal());
  document.getElementById('confirm-reveal-stats')?.addEventListener('click', () => finishReveal(true));
  frame.addEventListener('load', () => {
    frame.contentDocument?.body.classList.add('board-embedded');
    frame.contentDocument?.addEventListener('dragstart', event => {
      const portrait = event.target.closest('[data-party-actor]');
      if (!portrait || !canEdit()) return;
      event.dataTransfer.clearData();
      event.dataTransfer.setData('application/x-kettlewright-actor', portrait.dataset.partyActor);
      event.dataTransfer.effectAllowed = 'copy';
    });
  });
  partyButton.addEventListener('click', () => {
    if (panel.open) {panel.close(); return;}
    frame.src = config.partyUrl;
    panel.show(); partyButton.setAttribute('aria-expanded', 'true');
  });
  document.getElementById('close-party').addEventListener('click', () => panel.close());
  panel.addEventListener('close', () => {
    partyButton.setAttribute('aria-expanded', 'false'); frame.src = 'about:blank';
  });
  const lockButton = document.getElementById('lock-map');
  function selection() {
    if (!lockButton) return;
    const background = getApi()?.getSceneElements().filter(element => !element.id.startsWith('actor-')) || [];
    const locked = background.length > 0 && background.every(element => element.locked);
    lockButton.setAttribute('aria-pressed', String(locked));
    lockButton.classList.toggle('map-unlocked', !locked);
    lockButton.title = lockButton.ariaLabel = config.messages[locked ? 'unlockMap' : 'lockMap'];
    lockButton.disabled = !canEdit() || !background.length;
  }
  lockButton?.addEventListener('click', () => {
    if (!canEdit()) return;
    const api = getApi(), locked = lockButton.getAttribute('aria-pressed') !== 'true';
    const elements = api.getSceneElements().map(element => {
      if (element.id.startsWith('actor-') || element.locked === locked) return element;
      return {...element, locked, version: element.version + 1, versionNonce: Math.floor(Math.random() * 2147483647)};
    });
    api.updateScene({elements: restoreElements(elements, null), captureUpdate: CaptureUpdateAction.IMMEDIATELY});
    selection();
  });
  if (!config.warden) {
    diceModal.initialize(async dice => {
      const body = new FormData();
      body.set('dice', dice); body.set('csrf_token', config.csrfToken); body.set('public_roll', 'on');
      const response = await fetch(config.rollUrl, {method: 'POST', body, signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error(config.messages.rollFailed);
      return response.json();
    });
    document.getElementById('board-dice').addEventListener('click', () => diceModal.showDiceModal());
  }
  return {selection, confirmReveal, destroy() {
    finishReveal();
    panel.close(); frame.src = 'about:blank';
    document.getElementById('dice-modal').classList.remove('is-active');
  }};
}
