import {localizeGraph, localizeText} from '../../generator-locale.js';
import {generateResult, graphFromResult} from '../../content_generators.js';

// New campaign dialog. "Random campaign" generates the draft here, with the same
// generator as the map page, and submits it with the campaign so both save together.
// If generation fails, the form is sent without a draft and the server opens the
// map page instead, where the generator can be retried.
export default function newCampaign() {
  return {
    start: 'empty', kind: 'realm', children: true, generating: false,
    async submit(event) {
      if (this.start !== 'random') return;
      event.preventDefault();
      if (this.generating) return;
      this.generating = true;
      const form = event.target;
      try {
        const response = await fetch('/maps/tables');
        if (!response.ok) throw new Error('Unable to load generator tables.');
        const tables = await response.json();
        const value = name => form.elements[name]?.value ?? '';
        const percent = (name, fallback) => {
          const number = Number(value(name));
          return value(name) !== '' && Number.isInteger(number) && number >= 0 && number <= 100 ? number : fallback;
        };
        const poiCount = value('poi_count');
        const subcategory = {realm: 'Realm', dungeon: 'Dungeon', forest: 'Forest'}[this.kind];
        const result = generateResult(tables, 'Worldbuilding', subcategory, Math.random,
          poiCount ? {poiCount: Number(poiCount)} : {});
        const graph = graphFromResult(result, Math.random, tables, {generateChildren: this.children,
          forestChance: percent('forest_chance', 50), dungeonChance: percent('dungeon_chance', 25)});
        localizeGraph(graph);
        this.field(form, 'title', localizeText(result.title));
        this.field(form, 'body', graph.body || '');
        this.field(form, 'draft', JSON.stringify(graph));
      } catch {
        // Submit without a draft; the server falls back to the map page.
      }
      form.submit();
    },
    field(form, name, value) {
      let input = form.querySelector(`input[type=hidden][name="${name}"]`);
      if (!input) {
        input = Object.assign(document.createElement('input'), {type: 'hidden', name});
        form.append(input);
      }
      input.value = value;
    },
  };
}
