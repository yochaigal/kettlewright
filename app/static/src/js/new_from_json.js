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
    const parsed = JSON.parse(await file.text());
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
  const numeric = ["strength", "strength_max", "dexterity", "dexterity_max", "willpower", "willpower_max", "hp", "hp_max", "gold"];
  const text = ["name", "background", "custom_name", "custom_background", "description", "bonds", "omens", "scars", "notes", "image_url", "traits", "background_table1_question", "background_table1_answer", "background_table2_question", "background_table2_answer"];
  for (const field of numeric) form.elements[field].value = data[field] ?? 0;
  for (const field of text) form.elements[field].value = data[field] ?? "";
  for (const field of ["custom_image", "deprived", "panicked", "dead"]) {
    form.elements[field].value = [true, 1, "true", "True", "1"].includes(data[field]) ? "true" : "false";
  }
  form.elements.pets.value = JSON.stringify(data.pets ?? []);
  form.elements.items.value = JSON.stringify(data.items ?? []);
  form.elements.containers.value = JSON.stringify(data.containers ?? []);
});
