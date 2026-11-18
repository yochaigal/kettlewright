// Dice results on screen over the whiteboard (#385): your own rolls once their dice settle, and the
// public rolls of everyone else in the party as they arrive ('dice_rolled' socket events).
//
// The server also sends your own public rolls back to you as 'dice_rolled'. That echo can arrive before
// your 3D dice have landed, so while a roll of yours is in flight other messages wait; once its result is
// known the echo is dropped and the rest are shown.
const ECHO_MS = 15000;

export function createRollOsd({container, format = (name, result) => `${name}: ${result}`, limit = 4, duration = 6000,
  now = () => Date.now(), schedule = setTimeout}) {
  let holds = 0, waiting = [], expected = [];

  function show(text) {
    if (!container || !text) return;
    const item = container.ownerDocument.createElement('div');
    item.className = 'board-roll-osd-item';
    item.textContent = text;
    item.addEventListener('click', () => item.remove());
    container.append(item);
    while (container.children.length > limit) container.firstElementChild.remove();
    schedule(() => {
      item.classList.add('is-leaving');
      schedule(() => item.remove(), 400);
    }, duration);
  }

  // The exact text the server announces (app/lib/character_rolls.py publish_roll).
  const echoOf = (name, result) => `${name} rolled a ${result}`;
  function isEcho(message) {
    expected = expected.filter(item => now() - item.at < ECHO_MS);
    const index = expected.findIndex(item => item.text === message);
    if (index < 0) return false;
    expected.splice(index, 1);
    return true;
  }

  return {
    /** A roll of yours started: hold other results until it is known. */
    hold() {holds += 1;},
    /** Your roll's result arrived (name and result as the server announces them), or it failed (no name). */
    release(name, result) {
      holds = Math.max(0, holds - 1);
      if (name && result) expected.push({text: echoOf(name, result), at: now()});
      const queued = waiting; waiting = [];
      for (const message of queued) this.received(message);
    },
    /** Show your own result, after its dice have settled. */
    own(name, result) {show(format(name, result));},
    /** A 'dice_rolled' message from the server. */
    received(message) {
      if (typeof message !== 'string' || !message) return;
      if (holds) {waiting.push(message); return;}
      if (!isEcho(message)) show(message);
    },
  };
}
