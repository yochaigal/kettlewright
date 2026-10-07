# Exporting a campaign

Open a campaign and choose **Export campaign** to download `campaign-<id>.zip`.
The export contains the Warden's private originals. It excludes party connections,
party publications, characters, accounts and articles from other campaigns or Unfiled.

```text
campaign.md                 Campaign name, type and archive-local ID
articles/The Realm.md        One Markdown file per original article
articles/Alderbridge.md
maps/article-0001.json       Canvas kind, nodes, edges and private drawing
manifest.json               Format version, file lists and article links
```

Article filenames preserve their stable source paths; IDs are generated within this
archive, independent of database IDs. `parent_id` refers to another file's `id`, including `campaign` for
top-level articles. Duplicate titles, punctuation and Unicode are supported without
renaming articles. The importer continues to accept the older `parent: Exact title`
syntax; `parent_id` takes precedence when supplied. IDs must be unique in the batch.

```markdown
---
layout: default
id: article-0002
title: Alderbridge
type: settlement
parent_id: article-0001
heart: 'true'
path_type: standard
source_path: articles/Alderbridge.md
---
# Alderbridge

A village built around an old stone bridge.

Its ruler lives in [[The Realm#Court|the court]].
```

All existing Overview articles are exported individually. The exported Campaign
file has no body, preventing an extra Overview from being created on reimport.
Descriptions retain their stored source, including the version marker and sanitized
HTML for legacy rich text; normal descriptions remain editable Markdown.

`manifest.json` uses `format: kettlewright-campaign` and `version: 1`. Map sidecars
refer to articles by archive-local `article_id`, nodes by map-local IDs, and nested
maps by their article ID. Node numbers, positions, geometry and the private Excalidraw
drawing (including embedded drawing image data) are retained. Related-article links
are included only when both articles belong to this exported campaign. External
parents are omitted and recorded in `warnings`. Description images remain HTTP(S)
Markdown references and are never downloaded or packaged. Legacy local description
uploads are not part of this archive format.

The manifest's `references` list preserves saved article bindings with archive-local
`source`, `token` and `target` values. This keeps links working after a target has
been renamed, without rewriting the readable Markdown or exposing database IDs.
Import remaps those bindings to the new articles. See [article link syntax and
limits](campaign-import.md#article-links).

## Restoring an export

**Import archive** previews and restores Markdown articles, titles, descriptions,
types, hierarchy, Heart flags, path types, map geometry, nested maps, private drawings
and related-article links as a new private campaign. Each map's article has a
`map: maps/article-0001.json` front matter field. The manifest's `maps` list is also
accepted, including archives exported before that front matter field was added.
References are validated against this batch and remapped to new database IDs;
they never point to records in the existing library. The whole import is committed
once after explicit preview confirmation. Imported maps remain private.

This export is not a complete application backup. The existing archive importer
limits still apply (50 MB archive, 500 members, 512 KB per Markdown/attachment,
16 MB per JSON/.excalidraw map file, 100 MB unpacked, 20 hierarchy levels). Drawings
must satisfy the editor's 12 MB / 2000-element limits; maps allow 200 points and
800 paths. Large exports can exceed archive limits.

## Example

[`examples/campaign/`](examples/campaign/) contains a campaign, a Realm, a Heart
settlement, an NPC nested under the settlement, a Dungeon and a conditional Path.
The Realm sidecar shows the settlement and Dungeon connected by that Path.

Create an importable ZIP without a build:

```sh
python3 -m zipfile -c /tmp/kettlewright-campaign-example.zip docs/examples/campaign
```

Upload the ZIP through **Campaigns → Import archive**, review the tree and explicitly
confirm the import. Both the article tree and map geometry will be restored.

For a hand-drawn campaign from Obsidian or another Excalidraw editor, see
[the preparation guide](campaign-import.md#hand-drawn-maps-and-obsidian). You do
not need to write Excalidraw element JSON or Kettlewright graph JSON by hand.
