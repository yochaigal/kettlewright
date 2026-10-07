# Ukrainian terminology audit

Audit date: 2026-10-07.
Baseline: `4529e65eef13429c0612bbd493eff3d3e5f9f4e9`.
The [pre-fix comparison](ukrainian-catalog-comparison.md) records the initial gaps.

## Sources and scope

Only Cairn's first edition was available in Ukrainian for this work, together
with its optional adventurer guide. This pass uses that translation as its
starting point and checks shared terms against it. The current English
second-edition JSON defines the effects and mechanics in Kettlewright.
The [Russian audit](russian-terminology-audit.md) identifies table meanings and
context collisions.

| Supplied source | Physical pages | Sections checked |
| --- | ---: | --- |
| `_source/Каїрн-сторінки.pdf` | 48 | 11: attributes and HP; 19–20: equipment; 26: casting and conditions; 30–31: scars; 32–33: bestiary; 35–39: spells |
| `_source/Каїрн-Путівник пригодника-сторінки.pdf` | 24 | 12: wilderness events |

Source SHA256 values:

```text
Rules book: 1072354b626d0a2728c833016c1ee6a3553f02782cceb09e1ca644e337312e67
Adventurer guide: 5179cf6f635bd94e368e85674467a4a13eb5235e11c889a47dd935f03e67fcaa
```

These are physical PDF page numbers, not printed page numbers. Both PDFs have
native text but no bookmarks. Selected pages were read after checking their
page metadata; no whole-book OCR was needed.

The catalog uses the detailed spell descriptions as its reference when a
heading differs from the short list. For example, `Spider Climb` is «Павуче
лазання» in the detailed table and «Павуче лазіння» in the short list.

## Catalog changes

| Measure | Before | After |
| --- | ---: | ---: |
| Translated messages | 4152 | 4481 |
| Ordinary entries | 4144 | 4226 |
| Contextual entries | 8 | 255 |
| Distinct contexts | 6 | 26 |
| Russian reference keys absent from Ukrainian | 312 | 0 |
| Ukrainian-only contextual keys | 0 | 17 |

This pass adds 329 entries: 82 ordinary entries and 247 contextual entries.
It changes 74 existing translations. All 4152 existing keys remain present.

The 82 ordinary additions cover 49 Marketplace names, 10 hireling roles,
6 additional hireling-equipment names, 5 pet or mount names, 7 naming or
terrain terms, and 5 other entries. The last group includes `Shroud`,
`Catastrophic`, `Warden`, `Slow.`, and the Stone Heart bond description.

The contextual additions cover the 230 Russian reference entries and
17 further Ukrainian cases:

- `spell name`: `Vision`.
- `npc trait`: `Intelligent`, `Incompetent`, `Popular`.
- `npc quirk`: `Lanky`, `Scarred`.
- `culture character`: `Harmonious`.
- `faction trait`: `Aloof`, `Greedy`, `Honest`, `Impulsive`, `Naive`,
  `Stubborn`, `Vain`, `Witty`.
- `forest description`: `Awakening`.
- `forest name adjective`: `Frozen`.

Some new context entries currently equal their ordinary translation. They
record the table's own term alongside entries whose meaning or form differs.

## Main decisions

| English key or use | Ukrainian result | Reason |
| --- | --- | --- |
| `HP`, `DEX`, `WIL` | ПЗ, СПР, ВОЛ | The Ukrainian book uses these abbreviations. |
| `Warden` | Хранитель | The Ukrainian book and existing descriptions use this role name. |
| `Deprived` | Позбавлення | The Ukrainian rules use this named condition. |
| `Pain Band` | Каблучка болю | The English description explicitly says “ring”. «Каблучка» adds no claim about a stone or seal. |
| `Air bladder` | Повітряний міхур | Equipment list, physical page 20. |
| `Caltrops` | Кальтропи | Equipment list, physical page 20. |
| `Plate`, `Flail`, `War Hammer` | Лати, Ціп, Бойовий молот | Armor and weapon list, physical page 19. |
| `Stable`, dungeon room | Стайня | A room or building. |
| `Stable`, forest spirit trait | Стабільний | A spirit's trait, not a building. |
| `Mystic`, NPC role | Містик | A person, rather than «Містичний». |
| `Religious`, culture character | Релігійна | A cultural trait, rather than the clergy noun «Духівництво». |
| `Toxic`, dungeon condition | Отруйне | An adjective; its naming-noun use remains «Отрута». |
| `Trap`, equipment | Капкан | Portable equipment; the ordinary POI label remains «Пастка». |
| `Growth`, forest naming noun | Поросль | Vegetation in a forest name, rather than abstract growth. |
| `Thicket`, spell | Зарості | Detailed spell table, physical page 36. |
| `Thicket`, forest naming noun | Гущавина | The forest naming meaning has its own context. |
| Wilderness `Quiet` event | Знахідка | The guide calls the resource-finding event «Знахідка» on physical page 12. |

`Pain Band` has the same name in its item entry and description. The description
also says «носіть каблучку», so the grammatical form agrees with the new name.

NPC trait entries use masculine forms for the person. General faction traits
use feminine forms for «фракція». Culture traits use feminine forms for
«вдача». Naming adjectives and naming nouns have separate entries where one
English key serves both tables.

### Spell titles and references

The detailed Ukrainian spell table supplies shared spell names. Item names,
background descriptions, and bestiary spell lists use the same titles.
Examples include:

| English | Ukrainian |
| --- | --- |
| `Arcane Eye` | Чарівне око |
| `Auditory Illusion` | Звукова ілюзія |
| `Disassemble` | Розібрати |
| `Mirrorwalk` | Дзеркальний прохід |
| `Charm` | Зачарування |
| `Pacify` | Заспокоєння |
| `Smoke Form` | Форма диму |
| `Teleport` | Телепортація |
| `Vision`, spell name | Видіння |
| `Shroud` | Пелена |
| `Magic Dampener` | Послаблення магії |

`Teleport` is a noun in the spell list and the verb «Телепортує» in the
`dungeon feature` context. `Vision` keeps «Зір» as its ordinary translation,
which fits a monster ability target. A new `spell name` context gives it
«Видіння» in spellbook titles.

The generator selects `spell name` through the `('Spellbooks', 'name')` path.
Other spell names and other locales retain the normal fallback lookup.

Names were changed inside explicit spell references. Generic prose remains
free to use an ordinary noun: a thicket in a description is not necessarily
the title «Зарості», and `Ward Stone` remains «Камінь-оберіг».

### Bestiary and names

The supplied Ukrainian bestiary contains six of the generator's monsters.
Their names now match that book: «Кореневий гоблін», «Кам’яні гончаки»,
«Люди в капюшонах», «Деревний троль», «Боґарт», and «Крижаний ельф».
The other 78 names have Ukrainian entries but were not checked against a
published Ukrainian bestiary in this pass.

The main 60-name NPC table now produces Cyrillic names throughout. The
52 targeted name entries use Ukrainian transliterations, including «Шрауд»
for the NPC and «Пелена» for the spell. Shared proper-name spellings already
present in Ukrainian are retained where possible, such as «Квілл».

The supplied first-edition books do not establish canonical spellings for
the second-edition NPC name table. This pass localizes those names; it does
not claim agreement with a published Ukrainian second edition.

## Coverage and deferred work

| Cohort | Available Ukrainian entries after this pass | Source check |
| --- | ---: | --- |
| Background names | 20/20 | Coverage; no supplied second-edition background book |
| Bestiary names | 84/84 | Six names match the supplied Ukrainian bestiary |
| Relic names | 46/46 | Coverage |
| Spell names | 100/100 | 96 match the detailed Ukrainian PDF headings |
| Marketplace names | 70/70 | Coverage; shared equipment terms use the supplied book |
| Main NPC name table | 60/60 | All results are Cyrillic |
| Extended NPC name table | 54/82 | 28 positions still use Latin-script names |
| Scar names | 12/12 | All names match the supplied Ukrainian scar table |

Four spell titles are outside the first-edition PDF headings:

- `Fish Lung` → «Риб’яча легеня».
- `Skillful Repair` → «Вправний ремонт».
- `Passage` → «Прохід».
- `Marble Craze` → «Кульковий шал».

The first three belong to the current second-edition list and lack a
corresponding heading in the supplied first-edition book. The chosen title
for `Marble Craze` is «Кульковий шал». The PDF heading is «Мармурове
божевілля», but the effect describes glass marbles; the catalog uses the
glass-ball meaning.

The PDF's `X-Ray Vision` description repeats the `Liquid Air` effect. The
English generator description gives the X-ray effect. The name is usable;
the PDF description is not the source of the generator's mechanics.

`Haven` now has the Ukrainian entry «Пристанище», using the English naming
meaning of a safe place. The Russian catalog retains its existing values for
the five vocabulary choices recorded in the Russian audit.

The spelling pass for the remaining 28 extended NPC names and the background
personal-name lists is deferred. A fresh extraction of newer interface strings
is also deferred. The 4481-message count measures existing catalog entries,
not complete interface coverage.

## Verification

- `msgfmt --check --statistics` reports 4481 translated messages.
- All 4152 original Ukrainian keys and all 4464 Russian reference keys are present.
- No messages are empty or fuzzy; Babel format checks pass.
- Every PO translation equals its compiled MO lookup.
- All 70 Marketplace names and all 100 spell names resolve to Ukrainian.
- All 60 main-table NPC names resolve to Cyrillic text.
- The title check finds 100 PDF headings and 96 matching generator spell names.
- All 12 scar names and selected equipment names match their physical PDF pages.
- The catalog contains no Russian-only letters.
- `git diff --check` passes.

The focused run passed 157 tests across generator translations, companions,
inventory slots, PDF export, equipment search, and the shared Marketplace.
Both new regressions were observed failing against the old catalog for the
expected reason, then passing with the corrected catalog:

1. Tools used «Зір» and «Телепортує» as spell titles; now it uses «Видіння»
   and «Телепортація» while retaining the target and feature meanings.
2. The item-library option displayed `Air bladder` in English; now it displays
   «Повітряний міхур» while its stored data still identifies `Air bladder`.