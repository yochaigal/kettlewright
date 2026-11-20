# Module format

A module is a package of **parts**: maps, articles and backgrounds today, and more
later (items, missions…). Each part has its own section on the module page, its own
folder in an archive and its own Markdown `type`. The parts are listed once, in
`MODULE_PARTS` (`app/lib/modules.py`).

Modules are exported and imported as **Markdown files only** (format 2). Upload one
`.md` file, or a ZIP/TAR of several. **Export** (on a module's card in the campaign
lobby) writes the same format, so an export imports again.

```text
module.md                    type: Module      the front page
maps/the-ashen-marches.md    type: Map         a drawing with its points and paths
articles/alderbridge.md      type: Settlement  any article type
articles/mara-the-ferryman.md type: NPC
backgrounds/tidewatcher.md   type: Background  character options
```

The import page offers this example as a download (`/materials/import-example.zip`,
from `app/static/examples/module/`).

## Front matter

Every file starts with YAML front matter: `layout: default`, `title` and `type`.
Values are plain strings, except `links` (a list) and `references` (a mapping).
Folders keep the parts tidy; the `type` says what a file is.

| Key | Where | Meaning |
| --- | --- | --- |
| `id` | any | An id used only inside this module, to refer to the file. |
| `parent_id` | articles, maps | The parent, by id. Or `parent`: an exact, unique title. |
| `links` | articles | Related articles, by id. |
| `references` | articles | `[[link text]]: id`, keeping links right after renames. |
| `heart` | articles | `true` for the Heart settlement. |
| `path_type` | articles | `hidden` or `conditional` (paths). |
| `map_type` | maps | `realm`, `dungeon`, `forest` or `freeform`. |
| `article` | maps | The map belongs to this article (a dungeon point and its rooms). |
| `map` | maps | A drawing file to load, e.g. `maps/world.excalidraw`. |
| `format`, `version` | module.md | `kettlewright-module`, `2`. |

## The parts

**module.md** (`type: Module`) names the module. Its text is the module's front
page: it becomes an Overview article with the module's title.

**Maps** (`type: Map`) have no text of their own: a title, a type, and one fenced
`kettlewright-map` block with the drawing, the points (each an article, by id, with
its number and position) and the paths (each a Path article joining two points).
Kettlewright writes this block when exporting; write a map file without it for an
empty map to draw, or with `map:` to load a hand-drawn `.excalidraw` scene (see
`docs/examples/hand-drawn-module/`). A point that has a map of its own (a dungeon on a
realm) is an article; its map is a map file with `article: <its id>`.

**Articles** are any article type (NPC, Settlement, Dungeon, Lore, Note…). Without
front matter, the title comes from the first `# heading` (or the file name) and the
type is Note; the preview lets you fix both. Articles link to each other with
`[[Title]]`, `[[Title|label]]`, `[[Title#Heading]]` or relative Markdown links.

**Backgrounds** (`type: Background`) are character options; see
[Campaigns: module format](campaigns.md#module-format) for their Markdown. JSON
backgrounds are not imported.

## Importing

Nothing is added until you review the preview and confirm. The preview lists the
module's parts apart: its maps (points, paths, drawing elements), its articles as a
tree, and its backgrounds. Everything becomes one module of a campaign (or is added
to an existing module with **Add files**), privately: nothing is revealed to a party.
Ids never refer to existing records.

**Older archives** still import: `campaign.md` (`type: Campaign`), `maps/*.json`
sidecars, `manifest.json`, and `map:` on a Realm, Dungeon, Forest or Freeform
article. In those, every such article is a map; in format 2, only map files are.

## Limits

50 MB archive, 500 files, 512 KB per Markdown file (16 MB for files in `maps/` and
for `.excalidraw`/JSON drawings), 100 MB unpacked, 64 KB of front matter, 50,000
description characters, 20 hierarchy levels. A map holds 200 points, 800 paths and a
12 MB drawing of 2000 elements. Image URLs stay as references and are not fetched.
Archive entries are read without extracting paths; links and special TAR members
are rejected. A preview expires after one hour.

## Adding a part

A new part (say, items) needs: an entry in `MODULE_PARTS`; its storage; a section
on the module page (list, **New …**, edit); its Markdown type, read in
`campaign_import.preview_files` and written in `campaign_export.export_archive`
under its folder; and its count in `module_counts`/`preview_counts`.
