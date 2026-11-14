// 3D dice over the page that land on the values the server rolled.
//
// The server decides every roll (so the party's roll history can be trusted); this only animates it, using
// dice-box-threejs's predetermined notation ('1d6+1d8@3,5'). The library (vendor/dice-box-threejs) is loaded on
// first use. Without WebGL, with reduced motion, or with 3D dice turned off, show() resolves straight away and the
// caller shows the plain result.
//
//   await dice3d.show({values: [3, 5], sides: [6, 8]})

const LIBRARY = new URL('../../vendor/dice-box-threejs/dice-box-threejs.es.js', import.meta.url).href;
const PREFERENCE = 'dice3d-enabled';
const SIDES = new Set([4, 6, 8, 10, 12, 20, 100]);
const SETTLED_MS = 1600;  // how long the dice stay after they stop
const FADE_MS = 400;      // matches the opacity transition of #dice3d-stage
const TIMEOUT_MS = 8000;  // never keep the caller waiting on a stuck animation
const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)');

let stage = null, boxLoad = null, fadeTimer = null, clearTimer = null, animating = false;
let queue = Promise.resolve();

function hasWebGL() {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl'));
  } catch (_) {
    return false;
  }
}
let webgl = null;

/** True when this browser can show 3D dice at all (the toggle is hidden otherwise). */
function isAvailable() {
  webgl ??= hasWebGL();
  return webgl && !reducedMotion?.matches;
}

/** The viewer's own choice, remembered in this browser; on unless turned off. */
function isEnabled() {
  try {
    return localStorage.getItem(PREFERENCE) !== 'off';
  } catch (_) {
    return true;
  }
}

function setEnabled(enabled) {
  try { localStorage.setItem(PREFERENCE, enabled ? 'on' : 'off'); } catch (_) { /* Optional preference. */ }
  if (!enabled) clear();
  else preload();
}

function getStage() {
  if (!stage) {
    stage = document.createElement('div');
    stage.id = 'dice3d-stage';
    stage.setAttribute('aria-hidden', 'true');
    // Layout inline, so the dice have a full-screen canvas on any page; #dice3d-stage in modals.scss only
    // shows and fades it. Without that stylesheet the empty, click-through layer simply stays visible.
    stage.style.cssText = 'position:fixed;inset:0;z-index:1000;pointer-events:none;';
    document.body.append(stage);
  }
  return stage;
}

// Kettlewright is ink on paper: ink dice on the light theme, bone dice on the dark one.
function colourset() {
  const dark = document.body.classList.contains('dark-mode');
  return dark
    ? {name: 'kw-bone', foreground: '#141414', background: '#e8e2d3', outline: 'none', texture: 'none', material: 'plastic'}
    : {name: 'kw-ink', foreground: '#f6f2e8', background: '#1c1c1c', outline: 'none', texture: 'none', material: 'plastic'};
}

function loadBox() {
  boxLoad ??= (async () => {
    getStage();
    const {default: DiceBox} = await import(LIBRARY);
    const box = new DiceBox('#dice3d-stage', {
      // Dice size follows the screen so a pair still fits on a phone.
      baseScale: Math.round(Math.max(60, Math.min(100, Math.min(innerWidth, innerHeight) / 7))),
      shadows: true,
      sounds: false,
      theme_customColorset: colourset(),
      strength: 1.2,
    });
    await box.initialize();
    // Follow the light/dark switch (body.dark-mode) without reloading the library.
    new MutationObserver(() => box.updateConfig({theme_customColorset: colourset()}))
      .observe(document.body, {attributes: true, attributeFilter: ['class']});
    return box;
  })().catch(error => {
    console.warn('3D dice are unavailable; showing plain results.', error);
    return null;
  });
  return boxLoad;
}

/** Start loading the library early (e.g. when the dice modal opens) so the first roll isn't delayed. */
function preload() {
  if (isEnabled() && isAvailable()) loadBox();
}

/**
 * dice-box-threejs notation for the server's dice. The dice are drawn landing on these faces, but the values
 * the library reports back are unreliable for d4 (checked in a browser: drawn right, reported wrong), so
 * callers always show the server's values, never box.roll()'s result.
 *
 * A d100 is a tens die and a ones die. A d100 is a tens die and a ones die: 57 is 50 and 7,
 * 100 is 00 and 0 (the library's 00 is 100 and its 0 is 10).
 */
function notation(values, sides) {
  const dice = [], faces = [];
  values.forEach((value, index) => {
    if (sides[index] === 100) {
      dice.push('1d100', '1d10');
      faces.push(Math.floor((value % 100) / 10) * 10 || 100, value % 10 || 10);
    } else {
      dice.push(`1d${sides[index]}`);
      faces.push(value);
    }
  });
  return `${dice.join('+')}@${faces.join(',')}`;
}

function canShow(values, sides) {
  return Array.isArray(values) && Array.isArray(sides) && values.length > 0 && values.length === sides.length
    && sides.every((side, index) => SIDES.has(side) && Number.isInteger(values[index])
      && values[index] >= 1 && values[index] <= side);
}

function clear() {
  clearTimeout(fadeTimer);
  clearTimeout(clearTimer);
  if (!stage) return;
  stage.classList.remove('is-rolling', 'is-fading');
  boxLoad?.then(box => box?.clearDice());
}

function fadeOut() {
  stage.classList.add('is-fading');
  clearTimer = setTimeout(clear, FADE_MS);
}

/**
 * Roll 3D dice that land on result.values (with result.sides). Resolves true once they settle, or false
 * straight away when they aren't shown. Rolls play one at a time.
 */
function show(result) {
  const values = result?.values, sides = result?.sides;
  if (!isEnabled() || !isAvailable() || !canShow(values, sides)) return Promise.resolve(false);
  const run = async () => {
    const box = await loadBox();
    if (!box || !isEnabled()) return false;
    clearTimeout(fadeTimer);
    clearTimeout(clearTimer);
    stage.classList.remove('is-fading');
    stage.classList.add('is-rolling');
    let timer;
    animating = true;
    try {
      await Promise.race([
        box.roll(notation(values, sides)),
        new Promise(resolve => { timer = setTimeout(resolve, TIMEOUT_MS); }),
      ]);
    } catch (error) {
      console.warn('3D dice roll failed.', error);
      clear();
      return false;
    } finally {
      animating = false;
      clearTimeout(timer);
    }
    fadeTimer = setTimeout(fadeOut, SETTLED_MS);
    return true;
  };
  const rolling = queue.then(run, run);
  queue = rolling.catch(() => {});
  return rolling;
}

// Dismiss settled dice early with Escape; they never block clicks (pointer-events: none). A roll still in
// flight is left to finish, since clearing it would leave its promise waiting for the timeout.
document.addEventListener('keyup', event => {
  if (event.code === 'Escape' && !animating && stage?.classList.contains('is-rolling')) clear();
});

export default {show, preload, isAvailable, isEnabled, setEnabled, notation};
