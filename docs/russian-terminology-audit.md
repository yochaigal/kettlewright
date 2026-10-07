# russian-terminology-audit

Audit date: 2026-10-07.

The reference is the Russian second edition at [ru.cairnrpg.com](https://ru.cairnrpg.com/).
Its source is [TheVarik/cairn-ru](https://github.com/TheVarik/cairn-ru), revision
[`681e7da6b0b489f7ba0ed2d05b00714c9f20be47`](https://github.com/TheVarik/cairn-ru/tree/681e7da6b0b489f7ba0ed2d05b00714c9f20be47).
The request is [kettlewright #347](https://github.com/yochaigal/kettlewright/issues/347).

## Reference sections

| Area | Reference |
| --- | --- |
| Attributes, armor, conditions, saves, combat, scars | [Core rules](https://ru.cairnrpg.com/second-edition/players-guide/core-rules/) |
| Traits, bonds, omens, inventory | [Character creation](https://ru.cairnrpg.com/second-edition/players-guide/character-creation/) |
| Backgrounds and their equipment | [Backgrounds](https://ru.cairnrpg.com/second-edition/backgrounds/) |
| Equipment names | [Marketplace](https://ru.cairnrpg.com/second-edition/players-guide/marketplace/) |
| Travel, weather, dungeon and wilderness events | [Procedures](https://ru.cairnrpg.com/second-edition/players-guide/procedures/) |
| Monster names and spell references | [Bestiary](https://ru.cairnrpg.com/second-edition/wardens-guide/bestiary/) |
| Monster generator vocabulary | [Creating monsters](https://ru.cairnrpg.com/second-edition/wardens-guide/creating-monsters/) |
| Dungeon generator headings | [Dungeon seeds](https://ru.cairnrpg.com/second-edition/wardens-guide/dungeon-seeds/) |
| Forest generator headings | [Forest seeds](https://ru.cairnrpg.com/second-edition/wardens-guide/forest-seeds/) |
| Realm, factions, resources, terrain | [Setting seeds](https://ru.cairnrpg.com/second-edition/wardens-guide/setting-seeds/) |
| Faction and realm naming terms | [Naming procedures](https://ru.cairnrpg.com/second-edition/wardens-guide/naming-procedures/) |
| NPC roles | [NPC tables](https://ru.cairnrpg.com/second-edition/wardens-guide/npc-tables/) |
| Relic names | [Reliquary](https://ru.cairnrpg.com/second-edition/wardens-guide/reliquary/) |
| Spell names | [Spellbooks](https://ru.cairnrpg.com/second-edition/wardens-guide/spellbooks/) |

## Main term decisions

| English | Russian |
| --- | --- |
| Realm | Королевство |
| Warden | Смотритель |
| NPC | ПС (персонаж Смотрителя) |
| HP / Hit Protection | ОЗ / очки защиты |
| STR / DEX / WIL | СИЛ / ЛОВ / ВОЛ |
| Deprived / Fatigue / Panicked | Истощение / Усталость / Паника |
| Critical Damage | Критический урон |
| petty / bulky / blast | мелкий / громоздкий / взрыв |
| Bonds / Omens / Scars | Узы / Знамения / Шрамы |
| Watch | Фаза |
| Agenda / Advantages / Obstacle | Повестка / Преимущества / Препятствие |
| Mixed Success / Major Success | Переменный успех / Значительный успех |
| Apparatus / Fealty / Subterfuge | Устройство / Верность / Ухищрения |
| Scarcity | Дефицит |
| Food / Medicine / Skilled Labor | Еда / Медицина / Рабочие |
| Textiles / Vessels | Текстиль / Корабли |
| General / Healer / Laborer / Thug | Полководец / Лекарь / Рабочий / Бандит |
| Heart (main settlement of a region) | Сердце |
| Lore / Hazard / Curiosity | Знания / Опасность / Диковинка |
| Construction / Composition | Строительство / Структура |
| Original Use / Impact | Изначальное применение / Воздействие |
| Terrain difficulty: Easy / Tough / Perilous | Легкая / Трудная / Опасная |
| Magic Dampener / Shroud / Vision | Подавление магии / Пелена / Видение |
| Disassemble / Mirrorwalk / Thicket / Teleport | Разбор / Зеркальный переход / Заросли / Телепортация |
| Wolfsbane / Pipeweed | Аконит / Трубочный табак |
| Smoke Pellets / False Cuffs | Дымовые бомбы / Фальшивые наручники |
| Smelting Hammer / Pain Band | Литейный молот / Повязка боли |
| Death-Whistle / Tally Stick | Смерть-свисток / Счетная палочка |
| Rime Seed / Paring Knife | Семя ледяной крапивы / Разделочный нож |
| Dawn Brigade / Oak Lord | Отряд Рассвета / Владыка Дуба |

The spell and equipment terms also apply inside descriptions. For example, the
Hexenbane's book and the spell generator both use «Разбор». The Outrider's item
and its description both use «Счетная палочка».

## Scars

| HP lost | Russian scar name |
| --- | --- |
| 1 | Шрам |
| 2 | Ошеломление |
| 3 | Опрокидывание |
| 4 | Перелом |
| 5 | Болезнь |
| 6 | Травма головы |
| 7 | Разрыв сухожилий |
| 8 | Потеря слуха |
| 9 | Изменение психики |
| 10 | Разрыв |
| 11 | Смертельная рана |
| 12 | Обречен |

## Source inconsistencies

- **Realm:** Setting seeds defines the term as «Королевство». The naming table
  uses «Царство» for one government type. The interface uses «Королевство»;
  the `ruler type` context uses «Царство». `Kingdom` uses «Королевство» in the
  naming table, so the two results stay distinct.
- **Arcane Eye, Disassemble, Mirrorwalk:** Some background pages use «Магический
  глаз», «Разборка» and «Зеркальный путь». Use the spell table's «Магическое око»,
  «Разбор» and «Зеркальный переход» for both item names and spell references.
- **Terrain:** Setting seeds uses «Простой» and «Труднопроходимый». Travel rules
  use «Легкая», «Трудная» and «Опасная». Use the travel terms for the contextual
  terrain-difficulty labels.
- **Quiet:** The dungeon event means «Спокойствие». The wilderness event finds
  useful resources and is called «Открытие» in the Russian procedures. Each
  description uses the term for its own event.
- **Healing Unguent / Healing Salve:** The Foundling page uses «Лечебная мазь»;
  the Greenwise page uses «Целебная мазь». Each item follows its background.
- **Leather Jerkin:** The Foundling page uses «Кожаный жакет»; the Outrider page
  uses «Кожаный камзол». Their separate English catalog keys preserve this
  distinction.
- **Teleport:** The spell is «Телепортация». A dungeon feature is
  «Телепортирует». The `dungeon feature` context selects the verb.
- **Shroud:** The spell is «Пелена». The NPC name is «Шрауд». NPC name lists
  use the `npc name` context, including names shared with ordinary words.
- **Thicket:** The spell is «Заросли». The forest naming table uses «Глушь».
  The `forest name noun` context selects the naming term.
- **Traits:** Character creation uses nouns such as «Осторожность». NPC tables
  use singular adjectives such as «Осторожный». Faction tables use plural
  adjectives such as «Осторожные». Each table has its own context.
- **Stable:** A dungeon room is «Конюшня». A forest spirit trait is «Надежный».
- **Trap:** The dungeon POI type is «Ловушка». Marketplace equipment is
  «Капкан», selected through the `equipment` context. The equipment lookup key
  stays `Trap`.
- **Hemlock:** The Russian NPC table repeats «Глиф» for both `Glyph` and
  `Hemlock`. Use «Хемлок» for `Hemlock` to retain the distinct name.
- **Table wording:** `Stubborn`/`Inflexible`, `Haven`, `Resilient`, and
  `Struggling` use the words in the corresponding Russian tables. These words
  can differ from a direct dictionary translation of the English key. The
  published game table is the reference for this audit.

### Open vocabulary-policy decisions

The PR keeps the published table wording below. The proposed alternatives were
not applied. A maintainer can choose whether these five terms should follow
the reference or the English meaning more closely.

| Key and context | Current reference wording | Proposed alternative |
| --- | --- | --- |
| `Stubborn` — `npc trait`, `dungeon faction trait` | Непреклонный | Упрямый |
| `Inflexible` — same two contexts | Упрямый | Непреклонный |
| `Haven` — ordinary key | Владение | Гавань |
| `Resilient` — `culture character` | Гибкий | Стойкий |
| `Struggling` — `culture character` | Тягостный | Бедствующий |

The first two alternatives would exchange the meanings while keeping
`Obstinate` distinct as «Своевольный». «Гавань» would avoid duplicating
`Refuge` («Пристанище» in the source naming table). The last two alternatives
retain masculine adjective forms and follow the English meanings more closely.
These are unresolved wording choices, not claims of runtime defects.

## Independent recheck

Claude Sonnet checked the source tables, catalog, and runtime consumers. It
confirmed the initial counts and entity-name checks. It also found that the
initial `Heart` replacement selected the wrong meaning, and that several
shared keys needed context. These findings led to the context-based lookup
in `translate_events_data` and the corrections described above.

The recheck also identified missing hireling roles, hireling equipment names,
pet names, the Catastrophic weather label, and the fifteenth bond description.
These entries now have translations. Empty pet notes now stay empty; gettext
does not receive an empty string and return the catalog header as notes.
The shared template translation filter also preserves empty strings.
Equipment names use the same contextual lookup in the library, Marketplace,
inventory titles, slot labels, and PDF item titles. Stored equipment keys stay
English when supplied by the Marketplace.

The initial review estimated 471 missing interface strings from literal
gettext calls. That estimate includes account security, Discord, campaigns,
import, and other recent interface features. Those strings require a complete
catalog extraction and localization pass. The compiled-catalog count below
measures existing entries, not interface coverage.

Background personal-name lists also have differences from the source. Some
source lists contain conflicting spellings, and the Marchguard list duplicates
the Mountebank list. The terminology checks below do not establish a canonical
spelling for every personal name in those lists.

The extended `NPCs.Names.d100` list is separate from the source's 60-name NPC
table. Of its 82 entries, 28 remain Latin-script names that the source does not
cover. These need a separate transliteration decision; the verified 60-name
cohort does not establish coverage for that extended list.

## Verification

The catalog contains 112 corrected translations and 312 added translations,
including context-specific entries. The first pass added 49 Marketplace
equipment names and the spell «Пелена». The recheck added translations for
names, roles, traits and other missing game terms.

The compiled catalog was checked against the source headings and tables:

- 20 background names.
- 84 bestiary names.
- 46 relic names.
- 100 spell names.
- All 70 Marketplace equipment names have catalog entries.
- The 60-name NPC table has translations, with the `Hemlock` correction above.

`msgfmt --check --statistics` reports 4464 translated messages. The audit also
checked that existing message keys are present, no entries are empty or fuzzy,
format checks pass, and compiled gettext lookups equal the PO translations.
The format check respects the catalog's existing `no-python-format` marker for
the literal `10%` in the Time Control description.

The focused test run passed 155 tests across generator translations,
companions, inventory slots, PDF export, equipment search, and the shared
Marketplace. The new checks cover Russian context selection, English and
Ukrainian fallback, client lookup markers, equipment identity, empty rendered
text, and empty pet notes. The context-selection, equipment-label, inventory
title, decorated character-sheet inventory, grammatical-form, and empty-text
regressions were observed failing before their fixes. The Ukrainian fallback check uses literal values from the
existing Ukrainian catalog; it was observed passing only.

The final Sonnet delta check confirmed that the last inventory-header finding
was fixed and found no new defects in that fix. The reviewer independently
reran all 10 generator-translation tests successfully.