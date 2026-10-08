# Russian translation notes

## Sources

Use the **Russian second edition** at [ru.cairnrpg.com](https://ru.cairnrpg.com/)
and its [source repository](https://github.com/TheVarik/cairn-ru).

| Terms | Reference |
| --- | --- |
| Attributes, conditions, combat, scars | [Core rules](https://ru.cairnrpg.com/second-edition/players-guide/core-rules/) |
| Character traits and background equipment | [Character creation](https://ru.cairnrpg.com/second-edition/players-guide/character-creation/), [backgrounds](https://ru.cairnrpg.com/second-edition/backgrounds/) |
| Equipment | [Marketplace](https://ru.cairnrpg.com/second-edition/players-guide/marketplace/) |
| Travel, weather, events, terrain difficulty | [Procedures](https://ru.cairnrpg.com/second-edition/players-guide/procedures/) |
| Creatures and spell references | [Bestiary](https://ru.cairnrpg.com/second-edition/wardens-guide/bestiary/) |
| NPC roles and names | [NPC tables](https://ru.cairnrpg.com/second-edition/wardens-guide/npc-tables/) |
| Relics | [Reliquary](https://ru.cairnrpg.com/second-edition/wardens-guide/reliquary/) |
| Spell names | [Spellbooks](https://ru.cairnrpg.com/second-edition/wardens-guide/spellbooks/) |
| Setting and naming tables | [Setting seeds](https://ru.cairnrpg.com/second-edition/wardens-guide/setting-seeds/), [naming procedures](https://ru.cairnrpg.com/second-edition/wardens-guide/naming-procedures/) |

## Choosing terms

- Use the published table for the term's actual role, rather than a dictionary
  translation of an isolated English key.
- Use spell-table names in background equipment and creature descriptions too.
  For example, prefer «Магическое око», «Разбор» and «Зеркальный переход» over
  the alternative spell names on some background pages.
- Use travel-rule labels «Легкая», «Трудная», «Опасная» for terrain difficulty.
- Preserve grammatical forms for each table: character traits can be nouns,
  NPC traits singular adjectives, and faction traits plural adjectives.
- Keep stored English equipment keys intact when changing their display names.

Translations live in the [Russian catalog](../app/translations/ru/LC_MESSAGES/messages.po).
The [generator context map](../app/main.py) selects a table-specific meaning;
[term lookup](../app/lib/translations.py) falls back to ordinary gettext.

## Meanings that need separate contexts

| English key | Russian meanings |
| --- | --- |
| `Realm` | «Королевство» in the interface; «Царство» in `ruler type`. `Kingdom` remains «Королевство». |
| `Teleport` | Spell «Телепортация»; `dungeon feature` «Телепортирует». |
| `Shroud` | Spell «Пелена»; `npc name` «Шрауд». |
| `Thicket` | Spell «Заросли»; `forest name noun` «Глушь». |
| `Stable` | Dungeon room «Конюшня»; forest spirit trait «Надежный». |
| `Trap` | POI «Ловушка»; `equipment` «Капкан». |
| `Cautious` | Character «Осторожность»; NPC «Осторожный»; faction «Осторожные». |

The two `Quiet` event descriptions also have different meanings: dungeon
«Спокойствие» and wilderness «Открытие». Translate each full description for
its own event.

## Reference wording and exceptions

The catalog keeps these published choices despite their differences from
literal English. The alternatives discussed in [PR #348](https://github.com/yochaigal/kettlewright/pull/348)
were not applied.

| Key and context | Current wording |
| --- | --- |
| `Stubborn`, NPC and dungeon faction traits | Непреклонный |
| `Inflexible`, same contexts | Упрямый |
| `Haven`, ordinary key | Владение |
| `Resilient`, culture character | Гибкий |
| `Struggling`, culture character | Тягостный |

- `Hemlock` uses «Хемлок»: the source repeats «Глиф» for both `Glyph` and `Hemlock`.
- Preserve separate background terms where the English keys differ: Foundling's
  `Healing Unguent` / `Leather Jerkin` use «Лечебная мазь» / «Кожаный жакет»;
  Greenwise's `Healing Salve` uses «Целебная мазь», and Outrider's
  `Leather jerkin` uses «Кожаный камзол». These keys are case-sensitive.
- `Pain Band` follows the Russian table's «Повязка боли». Its English effect
  describes a ring; this Russian wording is not a rule for the Ukrainian name.

Historical coverage counts, source revision and verification results are in
[PR #348](https://github.com/yochaigal/kettlewright/pull/348).
