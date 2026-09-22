const form = document.getElementById("character-form");
const fileInput = document.getElementById("jsonFile");
const submit = document.getElementById("submit-button");
const error = document.getElementById("json-error");
let data = null;
let selection = 0;
submit.disabled = true;

fileInput.addEventListener("change", async () => {
  const version = ++selection;
  data = null;
  submit.disabled = true;
  error.textContent = "";
  const file = fileInput.files[0];
  if (!file) return;
  try {
    const parsed = JSON.parse(await file.text());
    if (!parsed || Array.isArray(parsed) || typeof parsed !== "object" || !parsed.name || !parsed.background) {
      throw new Error("Invalid character");
    }
    for (const field of ["items", "containers"]) {
      if (typeof parsed[field] === "string") parsed[field] = JSON.parse(parsed[field]);
      if (parsed[field] != null && !Array.isArray(parsed[field])) throw new Error("Invalid inventory");
    }
    if (version !== selection) return;
    data = parsed;
    submit.disabled = false;
  } catch {
    if (version === selection) error.textContent = error.dataset.invalid;
  }
});

form.addEventListener("submit", (event) => {
  if (!data) {
    event.preventDefault();
    return;
  }
  const numeric = ["strength", "strength_max", "dexterity", "dexterity_max", "willpower", "willpower_max", "hp", "hp_max", "gold"];
  const text = ["name", "background", "custom_name", "custom_background", "description", "bonds", "omens", "scars", "notes", "image_url", "traits"];
  for (const field of numeric) form.elements[field].value = data[field] ?? 0;
  for (const field of text) form.elements[field].value = data[field] ?? "";
  for (const field of ["custom_image", "deprived", "panicked", "dead"]) {
    form.elements[field].value = [true, 1, "true", "True", "1"].includes(data[field]) ? "true" : "false";
  }
  form.elements.items.value = JSON.stringify(data.items ?? []);
  form.elements.containers.value = JSON.stringify(data.containers ?? []);
});
