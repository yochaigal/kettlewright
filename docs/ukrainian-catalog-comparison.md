# Russian and Ukrainian catalog comparison

Comparison date: 2026-10-07.
Baseline: `4529e65eef13429c0612bbd493eff3d3e5f9f4e9`, after PR #348 merged.

This document records the pre-fix catalog state. The implemented Ukrainian
pass is recorded in [ukrainian-terminology-audit.md](ukrainian-terminology-audit.md).
For the quoted baseline values, use that commit's PO file; local file links
can now show the corrected wording.

## Summary

The Ukrainian catalog contains all 4152 keys it shares with Russian. It lacks
312 keys now present in Russian: 82 ordinary keys and 230 contextual keys.
Both catalogs pass format checks and match their compiled MO files.

The main gaps are Marketplace names, NPC names, and table-specific meanings.
Some existing Ukrainian translations also give the same spell different names
in the spell list, equipment, and bestiary descriptions.

This comparison records findings and possible fixes. It does not establish an
approved Ukrainian glossary. The Russian catalog supplies table context;
English keys and descriptions supply the underlying meaning.

## Inputs and method

- [Russian PO](../app/translations/ru/LC_MESSAGES/messages.po) and its MO file.
- [Ukrainian PO](../app/translations/uk/LC_MESSAGES/messages.po) and its MO file.
- [Russian terminology audit](russian-terminology-audit.md).
- [Generator context rules](../app/main.py#L517) and
  [translation fallback](../app/lib/translations.py).
- Generator JSON, backgrounds, Marketplace, hirelings, pets, bonds, and scars.
- [Tools labels](../app/templates/main/tools.html#L6) and
  [spellbook result selection](../app/static/src/js/content_generators.js#L12).

Keys were compared as `(msgctxt, msgid)` pairs, excluding catalog headers.
Every PO translation was compared with the corresponding MO lookup.
The bundled `event_data.json` equals the combined standalone generator data.

The term review covered the entity names below and 879 distinct contextual
generator requests. It also covered the 112 existing Russian entries changed
in PR #348. Description checks focused on named spell references, the linked
equipment descriptions, scars, and the terms listed in the Russian audit.
An automated scan checked existing Ukrainian entries for Russian-only letters,
unchanged long English descriptions, copied long Russian text, and numeric
differences. This is a catalog comparison, not a page-by-page audit against
the Ukrainian PDFs.

## Catalog structure

| Measure | Russian | Ukrainian |
| --- | ---: | ---: |
| Translated messages | 4464 | 4152 |
| Ordinary entries | 4226 | 4144 |
| Contextual entries | 238 | 8 |
| Distinct contexts | 25 | 6 |
| Empty entries | 0 | 0 |
| Fuzzy entries | 0 | 0 |
| PO/MO lookup mismatches | 0 | 0 |
| Format errors | 0 | 0 |

There are 4152 shared keys, 312 Russian-only keys, and no Ukrainian-only keys.
A missing contextual entry does not always mean the displayed Ukrainian is
wrong. The helper falls back to ordinary gettext. Some ordinary translations
already fit the requested table; others select the wrong meaning or form.

### Entity-name coverage

The counts below measure available translations, not agreement with a
published Ukrainian edition.

| Cohort | Total | Russian entries | Ukrainian entries | Ukrainian gap |
| --- | ---: | ---: | ---: | --- |
| Background names | 20 | 20 | 20 | None |
| Bestiary names | 84 | 84 | 84 | None |
| Relic names | 46 | 46 | 46 | None |
| Spell names | 100 | 100 | 99 | `Shroud` |
| Marketplace names | 70 | 70 | 21 | 49 names |
| Main NPC name table | 60 | 60 | 13 | 47 Latin-script results |
| Extended NPC name table | 82 | 54 | 6 | 76 Latin-script results |
| Scar names | 12 | 12 | 12 | Wording needs review |

There are 21 background files but 20 distinct background names; two files use
`Aurifex`. NPC counts measure table positions. The extended table repeats
`Lysander`, so its 82 positions contain 81 distinct names. The two NPC tables
overlap and their gaps must not be added together.

### Missing ordinary keys: 82

The groups below are disjoint. Equipment already counted under Marketplace
is excluded from the additional hireling-equipment group.

| Group | Missing keys |
| --- | ---: |
| Marketplace equipment | 49 |
| Hireling roles | 10 |
| Additional hireling equipment | 6 |
| Pet and mount names | 5 |
| Naming and terrain terms | 7 |
| Other terms and one bond description | 5 |
| **Total** | **82** |

**Marketplace, 49:** `Air bladder`, `Animal feed`, `Axe`,
`Bathing Goods (Soap, Perfume, etc.)`, `Book`, `Bow`, `Caltrops`, `Card deck`,
`Chain (10ft)`, `Chalk`, `Chest`, `Chisel`,
`Common Agents (Glue, Grease, etc.)`, `Common Tools (Hammer, Shovel, etc.)`,
`Complex Instruments (Bagpipes, Fiddle, etc.)`, `Containers (Sack, Waterskin, etc.)`,
`Cooking Gear (Pots, Utensils, etc.)`, `Costume Gear (Face Paint, Disguise)`,
`Cudgel`, `Dowsing rod`, `Expeditionary Gear (Climbing Spikes, Pulley), etc.`,
`Fire oil`, `Fishing rod`, `Flail`, `Games (Cards, Dice, etc.)`,
`Grappling hook`, `Halberd`, `Helmet`, `Mace`, `Net`,
`Outdoor Comfort (Blanket, Hammock, etc.)`, `Parchment`, `Plate`, `Pole (10ft)`,
`Repellent (Wolfsbane, Mugwort, etc.)`, `Sedative`, `Sewing kit`, `Sickle`,
`Simple Instruments (Pipes, Lute, etc.)`, `Smoking pipe`, `Spear`,
`Specialized Tools (Ink, etc.)`, `Spiked boots`, `Staff`, `Sword`,
`Tent (fits 2, bulky)`, `Thieving Tools (Lockpick, Metal File, etc.)`,
`War Hammer`, `Wilderness Clothes (Poncho, Cloak, etc.)`.

**Hireling roles, 10:** `Alchemist`, `Animal Handler`, `Bodyguard`,
`Local Guide`, `Lockpick`, `Navigator`, `Sailor`, `Tracker`, `Trapper`,
`Veteran Bodyguard`. Here `Lockpick` names a hireling, not a tool.

**Additional hireling equipment, 6:** `Alchemical Tools`, `Animal Feed`,
`Rope`, `Smithing Tools`, `Thieving Tools`, `Writing Tools`.
`Animal Feed` and Marketplace's `Animal feed` are different gettext keys.

**Pet and mount names, 5:** `Dematerialized Pet`, `Hollow Wolf`, `Horse`,
`Mule`, `Raised Servant`.

**Naming and terrain, 7:** `Bastion`, `Folly`, `Glimmer`, `Haunt`, `Haven`,
`runnel creek`, `vasts`.

**Other, 5:** `Catastrophic`, `Shroud`, `Slow.`, `Warden`, and the bond
description beginning “You crossed a creature of the Wood, and it cursed you
with a Stone Heart.” The standalone `Warden` entry is absent, while existing
descriptions already use «Хранитель».

### Missing contextual keys: 230

Ukrainian has the eight older entries for `season`, `culture`, `relic`,
`terrain difficulty`, `trail`, and `faction agent`. It has no entries in the
19 contexts added for the Russian table audit.

| Context | Russian entries absent from Ukrainian |
| --- | ---: |
| `culture character` | 19 |
| `dungeon condition` | 5 |
| `dungeon faction trait` | 15 |
| `dungeon feature` | 2 |
| `dungeon room` | 3 |
| `equipment` | 1 |
| `faction trait` | 40 |
| `forest description` | 6 |
| `forest goal` | 1 |
| `forest name adjective` | 7 |
| `forest name noun` | 2 |
| `forest spirit trait` | 21 |
| `name adjective` | 13 |
| `name noun` | 5 |
| `npc name` | 52 |
| `npc quirk` | 9 |
| `npc role` | 1 |
| `npc trait` | 25 |
| `ruler type` | 3 |
| **Total** | **230** |

These counts identify reference entries to examine. They are not a requirement
to create 230 Ukrainian entries: Ukrainian needs separate entries where the
meaning or grammatical form changes.

## Confirmed meaning and consistency problems

| Key or use | Current Ukrainian | Evidence and possible correction |
| --- | --- | --- |
| `Stable`, forest spirit trait | Стайня | [Ordinary entry](../app/translations/uk/LC_MESSAGES/messages.po#L11245) means a building. Keep it for a dungeon room; use an adjective such as «Стабільний» for the spirit. |
| `Teleport`, spell title | Телепортує | [Ordinary entry](../app/translations/uk/LC_MESSAGES/messages.po#L11478) is a verb. The bestiary already uses «Телепортація» for the spell at [7717](../app/translations/uk/LC_MESSAGES/messages.po#L7717). Preserve the verb through `dungeon feature`. |
| `Awakening`, forest goal | Пробуджений | A completed-state adjective is used as a goal. The description and goal need different forms, such as «Пробуджений» and «Пробудження». |
| `Mystic`, NPC role | Містичний | [Ordinary entry](../app/translations/uk/LC_MESSAGES/messages.po#L14028) is an adjective. A person needs a noun such as «Містик» in `npc role`. |
| `Religious`, culture character | Духівництво | [Ordinary entry](../app/translations/uk/LC_MESSAGES/messages.po#L11735) names clergy, not a cultural trait. Use a separate adjective in `culture character`. |
| `Toxic`, dungeon condition | Отрута | The noun “poison” is used as a condition adjective. Keep noun and adjective meanings separate. |
| `Amber`, `Copper`, `Granite`, `Cold`, naming adjectives | Бурштин, Мідь, Граніт, Холод | These are noun forms in the adjective table. Add adjective forms without changing their noun uses. |
| `Crystal`, forest naming adjective | Кристал | A noun is used in the adjective table. A form such as «Кристальний» needs its own context. |

### Spell names inside descriptions

These are references to the same English spell, not separate spells.

| Spell | Catalog title | Other names already in Ukrainian | Locations |
| --- | --- | --- | --- |
| `Arcane Eye` | Чаклунське око | Чарівне око; Таємне око | [3380](../app/translations/uk/LC_MESSAGES/messages.po#L3380), [3387](../app/translations/uk/LC_MESSAGES/messages.po#L3387), [8272](../app/translations/uk/LC_MESSAGES/messages.po#L8272), [8499](../app/translations/uk/LC_MESSAGES/messages.po#L8499) |
| `Auditory Illusion` | Звукова ілюзія | Слухова ілюзія | [6128](../app/translations/uk/LC_MESSAGES/messages.po#L6128) |
| `Disassemble` | Розбирання | Роз’єднання | [5208](../app/translations/uk/LC_MESSAGES/messages.po#L5208), [5217](../app/translations/uk/LC_MESSAGES/messages.po#L5217) |
| `Charm` | Зачарування | Чари | Spellbook references at [7252](../app/translations/uk/LC_MESSAGES/messages.po#L7252), [7689](../app/translations/uk/LC_MESSAGES/messages.po#L7689), [8100](../app/translations/uk/LC_MESSAGES/messages.po#L8100) |
| `Pacify` | Замирення | Умиротворення | [8272](../app/translations/uk/LC_MESSAGES/messages.po#L8272) |
| `Smoke Form` | Подоба диму | Димова форма | [8272](../app/translations/uk/LC_MESSAGES/messages.po#L8272), [8499](../app/translations/uk/LC_MESSAGES/messages.po#L8499) |
| `Vision` | Зір | Видіння | [7689](../app/translations/uk/LC_MESSAGES/messages.po#L7689), [8272](../app/translations/uk/LC_MESSAGES/messages.po#L8272) |
| `Elemental Wall` | Стихійна стіна | Стіна стихій | [8272](../app/translations/uk/LC_MESSAGES/messages.po#L8272) |
| `Teleport` | Телепортує | Телепортація | [7717](../app/translations/uk/LC_MESSAGES/messages.po#L7717), [8272](../app/translations/uk/LC_MESSAGES/messages.po#L8272) |

`Vision` also names an ability target in the custom-monster table. «Зір» fits
that use. Changing the ordinary key to «Видіння» needs a separate target
context or a separate spell-name context; the current lookup rules do not
distinguish those two paths.

### Forms within one table

NPC traits mix forms for different subjects: `Intelligent` → «Розумна»,
`Cautious` → «Обережний», and `Craven` → «Боягуз». Faction traits mix feminine
and masculine adjectives with nouns. Culture traits include «Альтруїстична»
and «Стійкий», while their label is «Вдача». Each table needs one form policy
for its Ukrainian subject, rather than the gender used by Russian.

The main NPC table also falls back to ordinary meanings for `Brave` →
«Хоробрий», `Shade` → «Тінь», `Sky` → «Небо», and `Storm` → «Гроза».
The Russian table treats these as names. A Ukrainian naming policy must
determine whether they are translated nicknames or transliterated names.

## Differences that are not automatic fixes

| Term | Russian | Ukrainian | Finding |
| --- | --- | --- | --- |
| `Pain Band` | Повязка боли | Перстень болю | The English description says to wear the ring. Ukrainian preserves that object; copying the Russian noun would lose it. |
| `Tupshead Crown` | Тупоголовая корона | Бараняча корона | Ukrainian preserves the ram meaning of “tup”. The Russian table is not an automatic replacement. |
| `Wolfsbane` | Аконит | Тоя (Вовкобій) | Ukrainian plant names are valid language-specific vocabulary. |
| `Paring Knife` | Разделочный нож | Ніж для чищення | Ukrainian gives the normal meaning of the English tool. |
| `HP`, `DEX`, `NPC` | ОЗ, ЛОВ, ПС | ПЗ, СПР, НІП | Different language abbreviations do not establish a defect. |
| Wilderness `Quiet` | Открытие | Затишшя | Both descriptions give the resource-finding effect. The title difference needs a Ukrainian-source decision. |
| `Realm` | Королевство | Володіння | Both name a domain. Selecting Ukrainian edition terminology needs a source decision. |

The five open Russian choices remain open. Their current Ukrainian values are:

| Key and relevant context | Russian reference value | Current Ukrainian fallback |
| --- | --- | --- |
| `Stubborn`, NPC and dungeon faction traits | Непреклонный | Впертий |
| `Inflexible`, same contexts | Упрямый | Негнучкий |
| `Haven`, ordinary key | Владение | Missing; English fallback |
| `Resilient`, culture character | Гибкий | Стійкий |
| `Struggling`, culture character | Тягостный | Знедолена |

These differences do not authorize changes to either language. The Ukrainian
`Stubborn`, `Inflexible`, and `Resilient` values are closer to the English keys
than the corresponding Russian reference values.

## Verification and next pass

`msgfmt --check --statistics -o /dev/null` passes for both PO files and reports
4464 and 4152 translated messages. Babel message checks also pass, and every
existing PO translation equals its MO lookup. The automated text scan found
no Russian-only letters, unchanged long English descriptions, or identical
long Russian/Ukrainian translations among existing Ukrainian entries.
Its five numeric candidates were benign: numbers written as words or added
metric equivalents. Missing entries are counted separately above.

The next translation pass has four concrete groups:

1. Fill the ordinary-key gaps, including `Shroud` and the Stone Heart bond.
2. Separate meanings and forms where ordinary fallback is wrong.
3. Choose one Ukrainian title per spell and align its item and bestiary references.
4. Check edition-specific terms, scar headings, and proper names against Ukrainian sources.

The 312-key difference measures parity with Russian, not total interface
coverage. A fresh extraction is still needed to count current interface
strings absent from both catalogs.
