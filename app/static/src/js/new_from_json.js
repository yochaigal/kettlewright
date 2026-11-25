import {conditionKeys, gameSystem} from '#kettlewright';
const form = document.getElementById("character-form");
const fileInput = document.getElementById("jsonFile");
const submit = document.getElementById("submit-button");
const error = document.getElementById("json-error");
const characterAction = form.action;
const characterSubmit = submit.value;
const panels = {
  pet: document.getElementById("import-pet"),
  hireling: document.getElementById("import-hireling"),
  character: document.getElementById("import-character"),
};
let kind = null;
let data = null;

function selectKind(selected) {
  kind = selected;
  for (const [type, panel] of Object.entries(panels)) {
    panel.hidden = type !== selected;
    for (const input of panel.querySelectorAll("select, input")) input.disabled = type !== selected;
  }
  form.action = panels[selected]?.dataset.action || characterAction;
  submit.value = panels[selected]?.dataset.submit || characterSubmit;
  const parent = panels[selected]?.querySelector("select");
  submit.disabled = !data || (selected !== "character" && !parent?.value);
}

for (const panel of Object.values(panels)) {
  panel.addEventListener("change", () => selectKind(kind));
}
let selection = 0;
submit.disabled = true;

// Markdown sheets only describe characters. The server reads them into the
// JSON export shape, so they go through the same form and checks as JSON.
function isMarkdown(file, text) {
  return /\.(md|markdown)$/i.test(file.name) || !text.trimStart().startsWith("{");
}

async function parseMarkdown(text) {
  const body = new FormData();
  body.append("csrf_token", form.elements.csrf_token?.value ?? "");
  body.append("markdown", text);
  const response = await fetch(form.dataset.markdownUrl, {method: "POST", body, credentials: "same-origin"});
  if (!response.ok) throw new Error("Invalid Markdown");
  return response.json();
}

fileInput.addEventListener("change", async () => {
  const version = ++selection;
  data = null;
  selectKind(null);
  error.textContent = "";
  const file = fileInput.files[0];
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) {
    error.textContent = error.dataset.tooLarge;
    return;
  }
  try {
    const text = await file.text();
    const parsed = isMarkdown(file, text) ? await parseMarkdown(text) : JSON.parse(text);
    if (!parsed || Array.isArray(parsed) || typeof parsed !== "object" || !parsed.name) {
      throw new Error("Invalid export");
    }
    const detected = ["pet", "hireling"].includes(parsed.kind) ? parsed.kind :
      (!parsed.kind && parsed.background ? "character" : null);
    if (!detected) throw new Error("Unknown export type");
    for (const field of ["items", "containers"]) {
      if (typeof parsed[field] === "string") parsed[field] = JSON.parse(parsed[field]);
      if (parsed[field] != null && !Array.isArray(parsed[field])) throw new Error("Invalid inventory");
    }
    if (version !== selection) return;
    data = parsed;
    selectKind(detected);
  } catch {
    if (version === selection) error.textContent = error.dataset.invalid;
  }
});

form.addEventListener("submit", (event) => {
  if (!data) {
    event.preventDefault();
    return;
  }
  if (kind !== "character") return;
  // The sheet's stats (kettlewright) and their maximums, attributes first: strength, strength_max, ... hp, hp_max.
  const {hp, attributes} = gameSystem();
  const numeric = [...[...attributes, hp].flatMap(stat => [stat.key, stat.key + "_max"]), "gold"];
  const text = ["name", "background", "custom_name", "custom_background", "description", "bonds", "omens", "scars", "notes", "image_url", "traits", "background_table1_question", "background_table1_answer", "background_table2_question", "background_table2_answer"];
  for (const field of numeric) form.elements[field].value = data[field] ?? 0;
  for (const field of text) form.elements[field].value = data[field] ?? "";
  for (const field of ["custom_image", ...conditionKeys()]) {
    if (!form.elements[field]) continue;
    form.elements[field].value = [true, 1, "true", "True", "1"].includes(data[field]) ? "true" : "false";
  }
  form.elements.edition.value = data.edition === "barebones" ? "barebones" : "2e";
  // The character's game system, and what the file has beyond the form's fields: the stats and conditions a system
  // keeps without a column ("luck": 7). The server keeps only those of the character's system (kettlewright).
  if (form.elements.game_system) form.elements.game_system.value = typeof data.game_system === "string" ? data.game_system : "";
  if (form.elements.system_stats) {
    const extra = Object.entries(data).filter(([field, value]) =>
      !form.elements[field] && ["number", "boolean"].includes(typeof value));
    form.elements.system_stats.value = JSON.stringify(Object.fromEntries(extra));
  }
  form.elements.pets.value = JSON.stringify(data.pets ?? []);
  form.elements.items.value = JSON.stringify(data.items ?? []);
  form.elements.containers.value = JSON.stringify(data.containers ?? []);
});
