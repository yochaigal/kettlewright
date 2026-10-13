import {generatorTerm, equipmentTerm} from './locale.js';

const MARKER = /(^|\. | · )(Heart · )?(Monster|Lore|Special|Trap|Ruins|Shelter|Hazard|Waypoint|Settlement|Curiosity|Lair|Dungeon|Forest|Realm|Faction|NPC|Difficulty|Landmark|Terrain|Type|Feature|Condition|Water|Abundance|Scarcity|Path): /g;

export function localizeText(value, t = generatorTerm) {
  if (typeof value !== 'string') return value;
  const whole = t(value);
  if (/^\+\d+ Armor$/.test(value)) return '+' + t(value.slice(1));
  if (whole !== value) return whole;
  return value.replace(/^Path: (standard|hidden|conditional)$/, (_, kind) => `Path: ${t(kind)}`)
    .replace(/Difficulty: (Easy|Tough|Perilous)\./g, (_, difficulty) => `Difficulty: ${t(difficulty)}.`)
    .replace(/^(Standard|Hidden|Conditional), /, (_, path) => `${t(path)}, `)
    .replace(MARKER, (_, lead, heart, label) => `${lead}${heart ? `${t('Heart')} · ` : ''}${t(label)}: `);
}

export function localizeBody(body, t = generatorTerm) {
  return (body || '').split('\n').map(line => {
    // Translate link labels before markers, so Heart and Settlement stay together.
    const linked = line.replace(/\[([^\]\n]+)\](\(kw-generated\/[^)]+\))/g,
      (_, label, href) => `[${localizeText(label, t)}]${href}`);
    const heading = /^(#+ )(.+)$/.exec(linked);
    if (heading) return heading[1] + localizeText(heading[2], t);
    const field = /^\*\*([^*\n]+):\*\* (.*)$/.exec(linked);
    if (field) return `**${t(field[1])}:** ${localizeText(field[2], t)}`;
    return localizeText(linked, t);
  }).join('\n');
}

// Only freshly generated drafts pass here. User-authored and saved text is never translated.
export function localizeDraft(draft, t = generatorTerm) {
  draft.title = draft.category === 'item' && t === generatorTerm
    ? equipmentTerm(draft.title) : localizeText(draft.title, t);
  draft.body = localizeBody(draft.body, t);
  for (const child of draft.children || []) localizeDraft(child, t);
  return draft;
}

export function localizeGraph(graph, t = generatorTerm) {
  localizeDraft(graph, t);
  for (const node of graph.nodes || []) {
    localizeDraft(node, t);
    if (node.nested_draft) localizeGraph(node.nested_draft, t);
  }
  for (const edge of graph.edges || []) edge.body = localizeBody(edge.body, t);
  return graph;
}
