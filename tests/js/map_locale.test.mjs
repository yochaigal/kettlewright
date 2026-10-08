import test from 'node:test';
import assert from 'node:assert/strict';
import {editorLocale} from '../../app/static/src/js/maps/locale.js';

// Codes are the Excalidraw v0.18.0 i18n.ts language-registry contract.
for (const [appLocale, acceptedCode] of [
  ['ru', 'ru-RU'], ['uk', 'uk-UA'], ['de', 'de-DE'], ['es', 'es-ES'],
  ['pl', 'pl-PL'], ['pt_BR', 'pt-BR'], ['ru-RU', 'ru-RU'], ['en', 'en'],
  [undefined, 'en'],
]) {
  test(`the map adapter passes ${appLocale ?? 'the default'} as an accepted editor code`, () => {
    // #given
    const locale = appLocale;
    // #when
    const actual = editorLocale(locale);
    // #then
    assert.equal(actual, acceptedCode);
  });
}
