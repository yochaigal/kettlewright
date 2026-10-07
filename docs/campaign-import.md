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

Exports use optional archive-local `id` and `parent_id` fields to preserve hierarchy
when titles repeat. IDs must be unique; `parent_id` takes precedence over `parent`
and must refer to an ID in this archive. Optional `heart` accepts `true` or `false`;
`path_type` accepts `standard`, `hidden` or `conditional`. See
[Campaign export](campaign-export.md) for the file format and an example campaign.

Supported types are Campaign, Realm, Dungeon, Forest, Freeform, Overview, NPC, Location, Lore, Faction, Relic, Note, Bestiary, Item, Spellbook, Culture and Custom. Type matching ignores case and also accepts the category labels shown in the app, including plurals. Campaign descriptions become Overview articles. Geography types become empty editable maps carrying their Markdown description; Markdown headings do not generate map geometry.

Referenced Kettlewright map JSON and ordinary `.excalidraw` scenes are imported
alongside Markdown. The preview shows each map's filename, point/path counts and
drawing element count. Missing references, invalid geometry or incompatible drawings
block the whole import before confirmation. Unreferenced map files and attachments
are listed as skipped. Use HTTP(S) image URLs in descriptions; they remain Markdown
references and are not fetched. Legacy local description uploads are not migrated.
The normal description validation and HTML sanitization apply. Imported originals
do not become visible to a party until explicitly published.

Limits: 50 MB uploaded archive, 500 archive entries, 512 KB per Markdown/attachment,
16 MB per JSON/.excalidraw map file, 50,000 description characters, 100 MB total
unpacked content and 20 hierarchy levels. A map allows 200 points and 800 paths;
its drawing allows 2000 elements and 12 MB. Archive entries are read without
extracting paths; links and special TAR members are rejected. Preview confirmation
is bound to its owner and expires after one hour. Creating another valid preview
replaces that owner's previous pending preview.

## Hand-drawn maps and Obsidian

Prepare normal Markdown articles with the front matter shown above. Obsidian vault
notes are not automatically converted: add `layout`, `title`, `type` and `parent`
(or `id`/`parent_id`) to the notes you want to import. Internal `[[links]]` are
supported as described below; `![[embeds]]` remain literal text. One archive can contain the whole
prepared campaign, with one Campaign root and any number of article files.

Export each drawing to an ordinary `.excalidraw` JSON file. The Obsidian plugin's
[official documentation](https://github.com/zsviczian/obsidian-excalidraw-plugin#settings)
describes the Compatibility features for exporting/synchronizing legacy `.excalidraw`
files and copying scenes to excalidraw.com. Its own `.excalidraw.md` format,
including `compressed-json`, is not directly imported. Export a self-contained
scene with any drawing images embedded in its `files` data; references to separate
vault files or remote images are not fetched by Kettlewright.

Add one field to the article that should own the drawing:

```markdown
---
layout: default
title: The Ashen Marches
type: Realm
parent: My Campaign
map: maps/world.excalidraw
---
The village is north of the ruined abbey.
```

Put the named file in the same archive:

```text
campaign.md
world.md
maps/world.excalidraw
```

`map` paths are relative to the archive bundle root (the directory containing
`manifest.json`, if supplied), rather than to the article's own folder. A single
containing folder added by a ZIP tool is accepted. A manifest is not required for
hand-drawn imports. Use Realm, Dungeon, Forest, Freeform or another spatial article
type (for example Terrain or Settlement) for the article owning the map.

The imported scene is an **editable drawing**. A drawn village, label or arrow
does not automatically become a point article, NPC or route: create or link those
interactive articles in Kettlewright after import. Kettlewright's own exports
already contain that structure in their map sidecars, so those maps restore both
the drawing and interactive points/paths without manual JSON preparation.

Supported drawing elements are rectangles, ellipses, diamonds, text, lines, arrows,
freehand strokes and embedded PNG/JPEG/WebP/GIF images. Frames and web/Markdown
embeds are unsupported and block import; remove them or flatten them to a supported
image before exporting. Element links and Obsidian-specific metadata are removed.
Canvas settings (including background colour, viewport and theme) and custom vault
fonts are not restored; text appearance can differ. Missing embedded image data
blocks import rather than silently dropping the picture.

[`examples/hand-drawn-campaign/`](examples/hand-drawn-campaign/) is a minimal
prepared bundle, with a real `.excalidraw` scene and no hand-authored graph JSON.

## Article links

Editors, previews and imported Markdown accept `[[Village]]`, `[[Village|label]]`,
`[[places/Village]]`, `[[Village#History]]` and relative Markdown links such as
`[history](places/Village.md#History)`. Nested headings can use `#Parent#Child`.
Type `[[` in an editor to select an article or heading. Links inside code remain code.

Links resolve within the same campaign. Use a path when titles repeat. Archive
filenames supply these paths; optional `source_path` front matter preserves a
different original vault path. An unresolved or ambiguous link remains readable
text, and import preview reports it as a warning. Article links do not establish
the campaign hierarchy: keep supplying `parent` or `parent_id`.

Saved bindings survive title changes and export/import. Player views resolve links
only against that party's published articles and headings in the published text;
they use the existing article previews. Publishing the source does not publish its
targets. Block references (`#^block`), note/image embeds (`![[...]]`) and external
`obsidian://` navigation are outside this first stage. Description images continue
to use ordinary Markdown HTTP(S) URLs.

Deployment requires installing the updated requirements and running `flask db upgrade`
through migration `336a01`.
