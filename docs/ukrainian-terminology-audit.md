# Ukrainian translation notes

## Sources and edition

Use [ua.cairnrpg.com](https://ua.cairnrpg.com/) as the online Ukrainian reference.
Its [SRD](https://ua.cairnrpg.com/cairn-srd/) is **Cairn first edition (v1.0)**.
Kettlewright's current game data is second edition: use the Ukrainian SRD for
shared terminology and meanings, and the English second-edition data for mechanics
and content absent from the first edition.

| Terms | Online reference |
| --- | --- |
| Character terms and HP | [Character creation](https://ua.cairnrpg.com/cairn-srd/#створення-персонажа) |
| Equipment | [Equipment list](https://ua.cairnrpg.com/cairn-srd/#список-спорядження-ціни-в-золотих) |
| Conditions and scars | [Deprivation and fatigue](https://ua.cairnrpg.com/cairn-srd/#виснаження-та-втома), [scars](https://ua.cairnrpg.com/cairn-srd/#шрами-1) |
| Spell effects | [100 spells](https://ua.cairnrpg.com/cairn-srd/#100-заклинань) |

The online SRD is partly translated and differs from the Ukrainian print books
used in [PR #349](https://github.com/yochaigal/kettlewright/pull/349).
For example, it uses «ЗУ» and «Наглядач», while the catalog uses the print terms
«ПЗ» and «Хранитель». Many online spell headings remain English. The selected
catalog terms below follow the checked print translation.

## Choosing terms

- Use a term's table context and effect to determine its meaning.
- Use the selected Ukrainian spell name in item titles, background descriptions
  and creature spell lists, with the grammatical form the sentence requires.
- Where the print spell list and detailed descriptions differ, use the detailed
  table: for example, «Павуче лазання» rather than «Павуче лазіння».
- Keep NPC trait forms masculine; use feminine forms for «фракція» and «вдача».
  Russian grammar identifies the table's role, not the Ukrainian grammatical form.
- Keep stored English equipment keys intact when changing their display names.

Translations live in the [Ukrainian catalog](../app/translations/uk/LC_MESSAGES/messages.po).
The [generator context map](../app/main.py) separates table meanings, with ordinary
gettext fallback through [term lookup](../app/lib/translations.py).

## Selected wording

| Term | Ukrainian choice and reason |
| --- | --- |
| `HP`, `STR`, `DEX`, `WIL` | «ПЗ», «СИЛ», «СПР», «ВОЛ», following the checked print translation. |
| `Warden`, `Deprived` | «Хранитель», «Позбавлення», following the same print rules. |
| `Pain Band` | «Каблучка болю»: the English description explicitly says “ring”, without specifying a stone or seal. |
| `Marble Craze` | «Кульковий шал»: the effect creates glass marbles. This is the chosen alternative to the print heading «Мармурове божевілля». |
| Wilderness `Quiet` | «Знахідка», following the resource-finding event in the Ukrainian adventurer guide. |

The first edition does not supply headings for `Fish Lung`, `Skillful Repair`
or `Passage`. Their current names — «Риб’яча легеня», «Вправний ремонт» and
«Прохід» — are translations of the second-edition entries, not names verified
against a Ukrainian second-edition publication.

## Meanings that need separate contexts

| English key | Ukrainian meanings |
| --- | --- |
| `Vision` | `spell name` «Видіння»; ordinary «Зір» for a monster ability target. |
| `Teleport` | Spell «Телепортація»; `dungeon feature` «Телепортує». |
| `Shroud` | Spell «Пелена»; `npc name` «Шрауд». |
| `Stable` | Dungeon room «Стайня»; forest spirit trait «Стабільний». |
| `Trap` | POI «Пастка»; `equipment` «Капкан». |
| `Thicket` | Spell «Зарості»; `forest name noun` «Гущавина». |
| `Mystic` | Naming adjective «Містичний»; `npc role` «Містик». |

The Russian notes can help interpret a shared English key, but their wording
is not a Ukrainian glossary. Check the source of a personal-name table before
assuming that a first-edition name list covers it.

Historical PDF references, coverage counts and verification results are in
[PR #349](https://github.com/yochaigal/kettlewright/pull/349).
