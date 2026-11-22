# Public API

Kettlewright has a small, read-only JSON API for the public **Tools**: random
characters, monsters and the random tables. Use it to build your own apps,
bots or sites on top of Kettlewright content.

- No account, login or key is needed. The API never reads or changes user data.
- Every endpoint is a `GET` and returns JSON.
- Any website may call it from the browser (CORS is open for `/api/v1/`).
- Add `?lang=` (`de`, `es`, `pl`, `pt_BR`, `ru`, `uk`) to get translated text.
  Without it, the response is in English (or in the language a browser
  already picked on the Kettlewright site).
- Everything is rolled on the server, so each request gives a new result.

The base URL is your Kettlewright site, for example
`https://kettlewright.com`. `GET /api/v1/` lists every endpoint.

## Random characters

`GET /api/v1/characters/random`

| Parameter | Meaning |
|---|---|
| `background` | Optional. A Cairn 2e background name (any case), such as `Mountebank`. Random if omitted. |
| | `barebones` rolls a Barebones character; `barebones:<package>` uses a gear package. |

The response is the same character the Tools page's Character tool makes: name,
background and its two table answers, attributes, HP, armor, gold, traits,
bonds, omens, `items`, `containers` and `pets`. `image_url` is a full URL.

```sh
curl "https://kettlewright.com/api/v1/characters/random?background=Mountebank"
```

`GET /api/v1/backgrounds` lists the background names (use them as
`background`), their descriptions and the Barebones gear packages.

## Monsters

- `GET /api/v1/monsters` lists the monster catalog: name, HP, armor, STR, DEX,
  WIL, attack, notes, source link and portrait.
- `GET /api/v1/monsters/<key>` returns one monster, for example
  `/api/v1/monsters/acolyte`. The `key` is in the list.

## Rolling on a table

`GET /api/v1/roll/<table>`

| Table | Result |
|---|---|
| `dungeon-events` | A Dungeon Event |
| `wilderness-events` | A Wilderness Event |
| `weather` | Weather; add `?season=Spring`, `Summer`, `Fall` or `Winter` (random if omitted) |
| `reaction` | A Reaction Roll (2d6) |
| `random-monster` | A monster from the random monster table |
| `custom-monster` | A made-up monster: physique, feature, quirks, weakness, attack, critical damage, ability |
| `relic` | A relic |
| `spellbook` | A spellbook |

Each result has the same shape as on the Tools page:

```json
{
  "title": "Weather",
  "category": "weather",
  "fields": {"Season": "Winter", "Type": "Unpleasant", "Effect": "…", "Examples": "…"}
}
```

## All tables

`GET /api/v1/tables` returns every table the Tools page uses, including the
Realm, Dungeon, Forest, faction, NPC and naming tables. The Realm, Dungeon and
Forest generators themselves run in the browser and have no endpoint yet, but
you can roll on these tables in your own code.

## Errors

Errors use the HTTP status code and a JSON body:

```json
{"error": "Unknown background 'Nope'. See /api/v1/backgrounds.", "status": 404}
```

`404` means an unknown endpoint, table, monster, background or package; `400`
means a bad parameter value.

## Older endpoint

`GET /api/users/<username>/characters/<url_name>/` returns one saved character,
like its public sheet page. It predates `/api/v1`, is kept for existing users,
and may change in a later version.
