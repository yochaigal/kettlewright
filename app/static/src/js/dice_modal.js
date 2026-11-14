import notification from "./notification.js";
import dice3d from "./dice3d.js";

const HISTORY_MAX = 6;
const modal = document.getElementById("dice-modal");
const $ = (id) => document.getElementById(id);

// "4, 3 (d6+d6) · STR 12 · Success" → "STR 12 · Success": what the result line says beyond the dice.
function extraDetail(text) {
  const match = String(text || "").match(/\(d\d+(?:\+d\d+)*\)\s*(.*)$/);
  return match ? match[1].replace(/^[=·:\s—-]+/, "").trim() : "";
}

const diceModal = {
  mode: "character",
  resultText: $("dice-modal-roll-result"),
  detailText: $("dice-modal-roll-detail"),
  holds: 0,
  history: [],
  opener: null,

  initialize(rollCallback) {
    $("dice-modal-background").addEventListener("click", () => this.hide());
    $("dice-modal-close")?.addEventListener("click", () => this.hide());

    const roll = async (dice, label) => {
      this.hold();
      this.showRolling(label, dice);
      try {
        await this.showResult(await rollCallback(dice), {label});
      } catch (error) {
        this.showError(error.message);
        notification.showNotification(error.message);
      } finally {
        this.release();
      }
    };
    modal.querySelectorAll("button[data-dice]").forEach((button) => {
      const label = button.querySelector(".dice-modal-die-label")?.textContent.trim() || button.dataset.dice;
      button.setAttribute("aria-label", label);
      button.addEventListener("click", () => roll(button.dataset.dice, label));
    });

    // Show/hide d100 based on mode
    this.updateD100Visibility();
    this.initialize3dToggle();

    document.addEventListener("keyup", (e) => {
      if (e.code === "Escape" && modal.classList.contains("is-active")) this.hide();
    });
  },

  initialize3dToggle() {
    const toggle = $("dice-modal-3d-toggle");
    if (!toggle) return;
    toggle.closest("label").hidden = !dice3d.isAvailable();
    toggle.checked = dice3d.isEnabled();
    toggle.addEventListener("change", () => dice3d.setEnabled(toggle.checked));
  },

  // Rolls and their dice animation keep the modal's buttons disabled; nested holds release together.
  hold() {
    this.holds += 1;
    this.setButtonsDisabled(true);
  },

  release() {
    this.holds = Math.max(0, this.holds - 1);
    if (!this.holds) this.setButtonsDisabled(false);
  },

  setButtonsDisabled(disabled) {
    modal.querySelectorAll(".modal-card-body button").forEach((button) => { button.disabled = disabled; });
    modal.setAttribute("aria-busy", String(disabled));
  },

  setState(state) {
    const tray = $("dice-modal-tray");
    if (tray) tray.dataset.state = state;
  },

  // A die silhouette for the tray, copied from the matching button so the shapes live in one place.
  face(sides, value) {
    const source = modal.querySelector(`button[data-dice="d${sides}"] .die-icon`)
      || modal.querySelector(`.die-icon[data-sides="${sides}"]`);
    const face = document.createElement("span");
    face.className = "dice-modal-face";
    if (source) {
      const icon = source.cloneNode(true);
      const number = icon.querySelector(".die-num");
      number.textContent = value;
      if (String(value).length > 2) number.classList.add("is-long");
      face.append(icon);
    } else {
      face.textContent = value;
    }
    return face;
  },

  drawFaces(sides, values) {
    const faces = $("dice-modal-faces");
    if (!faces) return;
    faces.replaceChildren(...sides.map((side, index) => this.face(side, values ? values[index] : "?")));
  },

  setNotation(text) {
    const notation = $("dice-modal-notation");
    if (notation) notation.textContent = text || "";
  },

  /** The tray while the server rolls: the chosen dice, wobbling, with no numbers yet. */
  showRolling(label, dice) {
    const sides = String(dice || "").split("+").map((term) => Number(term.replace(/\D/g, ""))).filter(Boolean);
    this.setNotation(label);
    this.drawFaces(sides, null);
    this.resultText.textContent = modal.dataset.rollingText || "…";
    if (this.detailText) this.detailText.textContent = "";
    this.setState("rolling");
  },

  showError(message) {
    this.resultText.textContent = message;
    if (this.detailText) this.detailText.textContent = "";
    $("dice-modal-faces")?.replaceChildren();
    this.setState("error");
  },

  /**
   * Show a server roll ({result, values, sides}): the 3D dice first, when enabled, then the faces and
   * numbers in the tray. options.label names the roll ("d6+d6", "Reaction Roll", a monster's attack).
   */
  async showResult(result, {label = ""} = {}) {
    if (!result) return;
    const values = Array.isArray(result.values) ? result.values : [];
    const sides = Array.isArray(result.sides) && result.sides.length === values.length ? result.sides : [];
    const name = label || sides.map((side) => `d${side}`).join("+");
    this.hold();
    if ($("dice-modal-tray")?.dataset.state !== "rolling") this.showRolling(name, sides.map((side) => `d${side}`).join("+"));
    try {
      await dice3d.show(result);
    } finally {
      this.setNotation(name);
      if (sides.length) this.drawFaces(sides, values);
      else $("dice-modal-faces")?.replaceChildren();
      this.resultText.textContent = values.length ? values.join(", ") : result.result || "";
      if (this.detailText) this.detailText.textContent = this.detailFor(result, values);
      this.setState(sides.length ? "done" : "text");
      this.remember(name, values.length ? values.join(", ") : result.result || "");
      this.release();
    }
  },

  // Under the faces: the outcome the server added (a save, a reaction), or for two dice the highest
  // (Cairn keeps the highest of several damage dice; the sum is not shown).
  detailFor(result, values) {
    const extra = extraDetail(result.result);
    if (extra) return extra;
    if (values.length === 2) return `${modal.dataset.highestText || "Highest"} ${Math.max(...values)}`;
    return "";
  },

  remember(label, outcome) {
    const list = $("dice-modal-history");
    if (!list) return;
    this.history.unshift({label, outcome});
    this.history.length = Math.min(this.history.length, HISTORY_MAX);
    list.replaceChildren(...this.history.map(({label: what, outcome: got}) => {
      const item = document.createElement("li");
      const name = document.createElement("span");
      name.className = "dice-modal-history-what";
      name.textContent = what;
      const value = document.createElement("span");
      value.className = "dice-modal-history-value";
      value.textContent = got;
      item.append(name, value);
      return item;
    }));
    $("dice-modal-history-wrap").hidden = false;
  },

  updateD100Visibility() {
    const d100Button = $("dice-modal-d100-button");
    if (d100Button) d100Button.hidden = this.mode !== "party";
  },

  showDiceModal() {
    this.opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    modal.classList.add("is-active");
    this.resultText.textContent = "";
    if (this.detailText) this.detailText.textContent = "";
    this.setNotation("");
    $("dice-modal-faces")?.replaceChildren();
    this.setState("idle");
    dice3d.preload();
    requestAnimationFrame(() => modal.querySelector(".dice-modal-die:not([hidden])")?.focus({preventScroll: true}));
  },

  hide() {
    if (!modal.classList.contains("is-active")) return;
    modal.classList.remove("is-active");
    if (this.opener?.isConnected) this.opener.focus({preventScroll: true});
    this.opener = null;
  },

  setMode(mode) {
    this.mode = mode;
    this.updateD100Visibility();
  },
};

export default diceModal;
