// Excalidraw 0.18 uses regional codes for these shipped app locales.
const codes = {de: 'de-DE', es: 'es-ES', pl: 'pl-PL', ru: 'ru-RU', uk: 'uk-UA'};

export function editorLocale(locale) {
  const normalized = (locale || 'en').replace('_', '-');
  return codes[normalized] || normalized;
}
