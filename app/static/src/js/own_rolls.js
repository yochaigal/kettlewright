// Rolls made in this tab. The server announces every public roll to the whole party, the roller included
// ("Brielle rolled a 20 (d20) · STR 11 · Failure"), but the tab that rolled already says it its own way
// (the dice, the dice dialog, "STR save: 20 vs 11 — Failure"). So that tab drops the echo of its own roll;
// the roller's other tabs, and everyone else, still get it.
//
// The echo can arrive before the roll's own response: while a roll of this tab is in flight, announcements
// wait, and are shown (or dropped, when they are this tab's roll) once it is done.

let pending = 0;
const results = [];
const held = [];

const forget = (result) => {
  const index = results.indexOf(result);
  if (index >= 0) results.splice(index, 1);
};

// True (and forgotten) when the message announces one of this tab's rolls.
const consume = (message) => {
  const index = results.findIndex((result) => typeof message === 'string' && message.endsWith(` rolled a ${result}`));
  if (index < 0) return false;
  results.splice(index, 1);
  return true;
};

const flush = () => {
  if (pending) return;
  held.splice(0).forEach(([message, show]) => { if (!consume(message)) show(message); });
};

export const ownRolls = {
  /** Wrap a roll request of this tab: resolves to its result ({result: '7 (d8)', ...}). */
  async track(request) {
    pending += 1;
    let rolled = null;
    try {
      rolled = await request;
      return rolled;
    } finally {
      pending -= 1;
      if (rolled?.result) {
        results.push(rolled.result);
        setTimeout(() => forget(rolled.result), 15000);  // An echo that never comes (a private roll, offline).
      }
      flush();
    }
  },
  /** A party roll announcement: shown with show(message), unless it is this tab's own roll. */
  receive(message, show) {
    if (pending) held.push([message, show]);
    else if (!consume(message)) show(message);
  },
};

export default ownRolls;
