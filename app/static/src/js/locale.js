// Messages come from Babel in the current page's locale. Keep stored keys intact.
function messages(id) {
  return JSON.parse(globalThis.document?.getElementById(id)?.textContent || '{}');
}

export function interfaceText(key, parameters = {}) {
  const text = messages('interface-labels')[key] || key;
  return text.replace(/%\((\w+)\)s/g, (token, name) => parameters[name] ?? token);
}

export function generatorTerm(key) {
  return messages('generator-labels')[key] || key;
}

export function equipmentTerm(key) {
  return messages('generator-labels')['equipment:' + key] || key;
}
