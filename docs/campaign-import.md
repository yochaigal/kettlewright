# Importing campaigns

Open **Campaigns → Import archive**, choose a ZIP, TAR or TAR.GZ archive, and review every destination before choosing **Import all into my library**. Previewing does not create campaigns or articles. Confirmation imports the whole batch once, privately, into the signed-in warden's library. Existing records are never overwritten or matched by title.

Each UTF-8 `.md` file starts with YAML Front Matter:

```markdown
---
layout: default
title: My Campaign
type: Campaign
---
The campaign description goes here.
```

```markdown
---
layout: default
title: My Dungeon
parent: My Campaign
type: Dungeon
---
The dungeon description goes here.
```

`parent` matches an exact, unique `title` in the same archive. Archive folders and file order do not determine hierarchy. A parent can be any imported article or a Campaign; Campaigns themselves must be roots. Missing or ambiguous parents, cycles and unsupported types block the entire import until corrected. Articles without a parent go to **Unfiled articles**; their children stay nested there.

Supported types are Campaign, Realm, Dungeon, Forest, Freeform, Overview, NPC, Location, Lore, Faction, Relic, Note, Bestiary, Item, Spellbook, Culture and Custom. Type matching ignores case and also accepts the category labels shown in the app, including plurals. Campaign descriptions become Overview articles. Geography types become empty editable maps carrying their Markdown description; Markdown headings do not generate map geometry.

Only Markdown files are imported. Images and attachments in the archive are listed as skipped; use HTTP(S) image URLs in descriptions. The normal description validation and HTML sanitization apply. Imported originals do not become visible to a party until explicitly published.

Limits: 10 MB uploaded archive, 500 archive entries, 512 KB per file, 50,000 description characters, 20 MB total unpacked content and 20 hierarchy levels. Archive entries are read without extracting paths; links and special TAR members are rejected. Preview confirmation is bound to its owner and expires after one hour. Creating another valid preview replaces that owner's previous pending preview.

Deployment requires installing the updated requirements and applying migration `318a01` with `flask db upgrade`.
