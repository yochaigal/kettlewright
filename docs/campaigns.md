# Campaigns and party knowledge

Open **Campaigns** to prepare a world. Each campaign belongs to one Warden and can be connected to several of that Warden's parties. Its overview, NPCs, locations, lore, factions, relics, notes and maps begin private.

**Reveal to party** opens a separate title and description for each connected party. Copying the private original is an explicit action. Select the parties, review their previews, then publish. Later changes to an original do not change published versions. **Revoke publication** hides a version without deleting its text, and **View as party** shows only that party's published knowledge.

A party's **Materials → Create and show** action creates a published material without requiring a campaign or a private description. Its private original can be filled in later. To organize it, open **Private original** and choose a campaign; existing party versions stay intact. **Unfiled materials** lists originals that have not been assigned to a campaign.

Descriptions use Markdown with a native text area, formatting toolbar and Write/Preview switch. This also applies to character notes, traits, bonds, omens, scars, background answers, party descriptions, companion notes and item descriptions; short names and titles support inline formatting. Character-sheet editors use a compact “Markdown supported” overlay without a toolbar. Ctrl/Cmd+B and Ctrl/Cmd+I toggle bold and italic in both editor layouts. The source stays editable Markdown. Credentials, numeric fields, URLs and JSON stay native fields. Markdown supports headings, emphasis, strikethrough, lists, quotes, links, code blocks, tables and images. Both browser previews and server output are sanitized. Marked 15.0.12 and Turndown 7.2.0 are vendored locally with their licenses; the Python renderer uses Mistune 3.2.0. There is no Quill or editor CDN dependency and no frontend build.

**Insert image** inserts `![]()` (or `![selected text]()`), with the cursor in the URL parentheses. Enter an HTTP(S) image URL directly in Markdown, just as for a link. Description editors have no file picker, upload/compression flow or image-file paste/drop handling. Existing uploaded images continue to render from `instance/material-images/<owner-id>/` (override `MATERIAL_IMAGE_UPLOAD_FOLDER`); back up this folder alongside portraits and the database. External URLs are never fetched by the server. Image access, publication boundaries, reference cleanup and transaction rollback remain the same for legacy HTML and Markdown.

Existing embedded descriptions are externalized when saved, or all at once with `flask campaigns migrate-images`. This command covers description fields, not Excalidraw's separate drawing snapshots. The description limit remains 5 MB and 50,000 text characters. SVG uploads are not accepted. Images follow the same private/publication boundary as text; changing an original never silently changes a party's published copy.

Existing versioned Quill HTML still renders and converts to Markdown when opened in the editor, preserving formatting and image links. Saving persists Markdown. Existing unmarked text is now interpreted as Markdown, with allowed legacy HTML sanitized. No database migration is needed. Related cards only appear to players when both cards have been published to their party. Players can read articles, but cannot edit originals or versions.

## Article generators

Choose **Campaign**, then **Top Category**, then an optional **Sub Category**. **None** creates the top category itself (for example People); Realm has no subcategory selector. Overview and Geography are absent from new choices. Legacy originals remain readable and editable.

The UI calls materials **Articles**; existing `/materials/` URLs and database records remain compatible. **New article** and a party's **Create and show** offer the same category generators, without requiring a campaign. Generation opens a separate draft to review; **Use this draft** replaces the form content, while **Discard** preserves it. Nothing is saved or published until the form is submitted. **Custom** starts with a blank editor.

Setting articles use the existing [Setting Seeds](https://cairnrpg.com/second-edition/wardens-guide/setting-seeds/), [Forest Seeds](https://cairnrpg.com/second-edition/wardens-guide/forest-seeds/) and Dungeon Seeds tables. **Realm** creates People (Culture, Resources, NPC), a Faction (Types, Traits, Advantages, Agendas), Topography (Terrain with Water and Weather), POIs and Paths. The same types can be generated individually. **Generate all child articles** is enabled by default for parent types; turning it off creates only the selected article. Draft previews include every child; Use this draft retains the rolled results, and saving persists the tree atomically. Child articles remain private, including when the root is created for a party.

**Locations** is no longer an article category. POIs have explicit types: Settlement, Waypoint, Curiosity, Lair or Dungeon. Forest contents retain their own types (Monster encounter, Ruins, Shelter, Hazard); dungeon contents retain Lore, Trap and Special types. **Heart** is a checkbox on Settlement articles and map points. A generated Realm starts with a Heart settlement. The POI table uses the Setting Seeds d6 weights, with an equal choice between Settlement and Waypoint on a 1; forests come from terrain instead of an extra POI-table outcome. Faction advantages are sampled without duplicates.

Terrain offers Random, Easy, Tough, Perilous and Forest generator choices. Forest terrain has a configurable **Forest contents chance**, default 50%; a generated forest may contain one additional Dungeon, with a configurable default chance of 25%. These percentages, the River/Lake/Sea choice, one NPC and one faction per Realm, and path counts/types are application defaults, not probabilities or counts prescribed by Cairn. Water descriptions retain the rules' guidance about connecting high and low ground. Weather rolls each season. Dungeon POIs also use the Setting Seeds type/feature table.

Articles have a **Parent article** selector, and existing articles offer **Add child article**. Parents must belong to the same owner and campaign (or both be Unfiled); cycles are rejected. Moving or deleting an article follows its descendants. Each descendant remains independently editable and publishable. Campaign and Unfiled trees include Paths as well as other article types.

NPCs, Bestiary, Relics, Spellbooks and Notes reuse Tools tables. Items use Marketplace gear, armor or weapons. Lore uses Dungeon Seeds room types and clues. Map and Geography are not authoring categories. Generated map points have explicit types and editable Heart flags. New Realm maps save People, Factions and Topography branches alongside grouped POIs and Paths; existing map geometry supplies containment for older records.

## Article drawings

Every spatial article's canvas appears directly inside its article editor and is created with the same original. Setting Seeds rolls **1d6 terrain regions**, with difficulty **1–3 Easy, 4–5 Tough, 6 Perilous**. Each terrain rolls its terrain and landmark columns separately; the landmark is also a child article under that Terrain, represented by a triangle on the Realm map. This applies to article generation and the existing Tools Realm generator.

Terrain seeds are scattered across the map. The canvas partitions the available area around their landmarks into adjoining polygons (a digital approximation of drawing borders around dropped dice). Dragging a landmark reshapes neighbouring regions after release; its position is saved with the map. Water, forest entrances, other POIs and paths remain independently editable. Interior dungeon/forest contents stay on their own article maps. The layout does not simulate elevation or river flow. Existing terrain without landmark children uses its saved position as the region seed; no legacy content is rewritten. A party sees a terrain–landmark association only when both articles are published to it.

Terrain uses a hatched region, Water a blue oval, Waypoints amber diamonds, Settlements orange squares, Forests green diamonds and Dungeons purple squares. Lairs and Curiosities have their own colours and labels. Labels are compact; selecting a marker opens the full title and description. Type names and shapes supplement colour. Paths retain solid/dashed/dotted styles. Only published articles appear on a party's canvas; generated shapes never enter the separately published freehand drawing snapshot.

On an empty Realm, **Prepare realm geography** previews Topography, POIs and Paths sections. It is hidden once the article has children, drawing objects or strokes. Nested generation controls likewise stay hidden for articles that already have contents. **Apply geography** saves the reviewed sections privately and places their articles on the map. Existing sections, positions, drawing and map contents are preserved; repeating the action does not duplicate articles or map objects. Map and article version checks reject stale requests.


Campaign workspaces and Unfiled materials display map contents hierarchically. A Dungeon or Forest point is the article that owns its map; its contents appear directly below it without another map article. Reused points remain navigable from every containing map. Editors link back to their parent and campaign. Removing a point from its last map retains the original as a standalone article.

Campaign workspaces and Unfiled materials support selecting individual materials
or **Select all**, followed by **Delete selected…**. A confirmation page lists
every original to be removed, including paths and nested contents. Selection is
limited to the current workspace. Cancel leaves all records intact.

Deleting a map (including Dungeon, Forest and Realm) deletes its descendant
locations, paths and nested maps, together with published party versions.
Deleting a location also deletes its linked nested map and connected paths.
This applies to both single and bulk deletion. Reused descendants are removed
from all containing maps; arbitrary related-material links do not cascade.
Campaign containers, parties, characters and Whiteboard drawings are preserved.
The preview expires after 30 minutes; changes to originals or affected map
geometry require a new preview. Existing standalone leftovers from maps deleted
before this behavior can be selected and deleted from Unfiled materials.

Spatial articles own their canvases: Realm, Topography, Terrain, Water, Forest, Settlement, Waypoint, Curiosity, Lair, Dungeon, Dungeon room, Ruins and Shelter. Creating one attaches a canvas to the same original and uses its direct points (including the POIs group) as map nodes without copying articles. Existing spatial originals offer **Add drawing**, which attaches the canvas on demand. Existing canvases are preserved. No database migration or automatic merging/deletion of legacy duplicates is performed.

Generate an Article using the existing Dungeon, Forest or Realm tables. Tools has one **Save or reveal** action, preserving the rolled content and opening an article draft with an embedded drawing. Saving opens the Article, including for party versions. Legacy standalone editor URLs redirect to their owning Article. Article descriptions and drawing edits are saved atomically with **Save private original**; a stale drawing or article version rejects the entire operation. There are no separate Map entries or actions in campaign navigation.

Generating a Dungeon or Forest from a point saves the map on that same article. **Generate article contents** previews private contents before saving. The original description is retained, generated detail is appended, and existing map contents are never overwritten. Publishing an entrance also makes its own map accessible, but drawing snapshots and child articles remain independently published. The legacy direct-publish endpoint preserves only the original entrance description in its party snapshot.

**Related materials** automatically includes a map's locations and linked maps; location cards also include their linked map. These structural relations work for older maps and disappear when the corresponding geometry link is removed. Players still see only independently published materials and their party-specific titles.

Forest paths retain their rolled trail types. Dungeon and realm paths without a trail table use random types: 4/6 standard, 1/6 hidden, 1/6 conditional. These weights are an application choice, not probabilities prescribed by the rules. Regenerating a draft rolls new types; saving preserves the draft's types.

Maps use Excalidraw with Preact in an isolated iframe. No npm install or frontend build is required: the iframe imports pinned modules from esm.sh, using the Excalidraw 0.18.0 production browser entrypoint and Preact 10.29.8 compatibility aliases. React imports, including JSX runtime, resolve to Preact. Editor styles and fonts are also loaded from the CDN; it must be reachable to open the editor. The rest of the application continues to use Alpine and HTMX. Map contents are saved through the existing authenticated Flask routes, not a hosted drawing room.

Drag location circles on the canvas or select them in the list and edit their coordinates. Connect locations with standard, hidden or conditional paths. Click a circle or path on the canvas to highlight its row below and open its details. Edit names, descriptions and path types directly below the map; saving uses the private card's version as well as the map version. Published party versions remain unchanged. Locations can link to another map in the same campaign (or another unfiled map). The editor supports up to 200 locations and 800 paths.

Publish the map, locations and paths separately. A party sees a path only when that path, both endpoints and the map have been revealed. Linked maps must also be revealed independently. Location names, descriptions and known path types may differ between parties; coordinates are shared. Removing a location from a map keeps its standalone card. Removing a path also removes its publications.

The drawing tools support freehand marks, text, shapes, images and erasing, with a square grid enabled initially. Images can serve as tokens. Drawings support up to 2000 elements and 12 MB, including PNG, JPEG, WebP and GIF images. SVG uploads, embeds and external element links are not persisted. Use the lists below the canvas to rename or remove graph locations and paths.

Drawings are private by default. On the map's **Reveal to party** page, explicitly check **Also publish the entire saved drawing to selected parties** to replace those parties' drawing snapshots. This publishes every freehand annotation and image, independently of the separately revealed location/path cards. Leaving it unchecked preserves each party's existing drawing. Later private edits do not change those snapshots. **Create and show map** includes the drawing in its initial publication. Players receive only their published snapshot and permitted graph cards, in view-only mode. Concurrent multi-user drawing is not implemented.

## Tools

Each result can be saved privately or immediately shown to a party. Results are structured objects shared by Tools and map generation, with the existing JSON tables as their source. Handoff between these pages uses sessionStorage in the same browser tab; save a result to retain it across sessions.

## Deployment and maintenance

`FEATURE_TEST_USER_IDS` and `FEATURE_TEST_PARTY_IDS` are reusable tester allowlists for current and future experimental features, not settings specific to campaigns or maps. The first identifies users eligible for individual-user testing; the second identifies parties eligible for party-level testing under existing owner/member permissions. New features should use these same audiences during testing and stop checking them when released to everyone. The lists remain available for the next experimental features.

Features restricted to these audiences are disabled by default outside local development. The dev-container Compose configuration sets `LOCAL_FEATURE_ACCESS=True`, which ignores both allowlists (including malformed values) and enables feature navigation and party selection for local accounts. Authentication, ownership, party membership, CSRF and publication checks still apply. Normal deployments leave this flag unset or false and continue to use the allowlists. Set the two environment variables to positive database IDs separated by commas or whitespace, then restart all application workers:

```dotenv
FEATURE_TEST_USER_IDS=12,34
FEATURE_TEST_PARTY_IDS=56,78
```

The current campaign/map rollout uses `FEATURE_TEST_USER_IDS` for personal campaigns, material authoring, map creation and the new Tools generator/save actions. Other users and guests retain the previous Tools generator. It uses `FEATURE_TEST_PARTY_IDS` for shared maps and published materials for the listed parties' owners and current members. Shared-map editing remains owner-only. Material creation/publication requires a tester Warden and a listed party; players need only membership in that listed party, not a personal tester ID. These lists are independent: a tester does not enable features in their other parties, and membership in a test party does not unlock personal authoring. Existing ownership, membership, publication and CSRF checks still apply.

Empty or unset lists grant no access to features still restricted to testers; generally released features are unaffected. Invalid IDs stop application startup with the variable name in the error. There is no wildcard or administrator bypass. The explicit local development flag is the only allowlist bypass. In the current rollout, disabled features disappear from navigation, and direct requests to their pages, data, saves and protected images are rejected. Removing an ID hides access without deleting stored materials/maps; hidden party connections are preserved when saving campaign settings. Campaign notifications skip disabled parties. The lists affect feature access, not schema migrations: apply all migrations even when both lists are empty.

Run `flask db upgrade` before serving this version. Revision `321a01` adds the Heart flag and converts old `location` records using explicit generated title prefixes. Unknown titles become Custom without changing their content; existing map roots take their map kind as their article type. It does not split or regenerate old descriptions. Revision `133a01` adds tables; it does not create campaigns for existing parties. Revision `297a01` adds private drawing and published-snapshot JSON columns; existing maps open with an empty drawing and retain their locations and paths. Deleting a party removes its knowledge and campaign connections, while retaining campaign originals. Disconnecting a party from a campaign revokes that campaign's publications. Deleting a campaign permanently deletes all materials assigned to it, including maps, nested maps, locations, paths, drawings and published party versions. Connected parties and their characters remain. Related materials belonging to other campaigns or **Unfiled materials** remain; their links to deleted content are removed. Move any material you want to retain out of the campaign first.

Map geometry and content originals use separate optimistic version checks. Conflicting saves return HTTP 409 instead of overwriting another tab. Published views are built on the server without original prose. Socket.IO notifications contain only party IDs; the browser fetches an authorized projection again. Open views also recheck access on focus and every 30 seconds while visible.

Originals, campaign membership, party presentations and graph geometry are separate tables so future campaign copying can omit party knowledge. Campaign sharing, co-Wardens, player editing, general file attachments and inventory transfers are outside this version.

## Validation

```sh
python -m pytest -p no:flask
node --experimental-default-type=module --test tests/js/content_generators.test.mjs
```

The campaign tests cover disclosure isolation, direct publication, adoption, current party membership, CSRF, safe text, notification payloads, map graph validation and concurrent updates. A separate migration test upgrades a database with an existing party and checks downgrade compatibility. Generator tests use seeded random sources to verify connectivity, loops and preservation of results.

Map editors preload the ready-made Excalidraw libraries **Architecture floor plan symbols** (Arqtangeles), **Maps** (swissarmysam), **DnD/TTRPG battle map creature tokens** (Maffen) and **DnD 5e planning** (DemonDarakna). Open **Library** to place an item on the canvas. Library assets are served locally and do not populate the drawing until selected. Upstream sources and MIT attribution are in `app/static/vendor/excalidraw-libraries/README.md`.

Terrain borders can be moved, resized, rotated and edited point by point. A manual shape overrides the initial landmark-based polygon until **Reset shape**; moving a landmark does not overwrite it. The article list separates Topography (including Terrain, Landmark and Water) from POIs. **Draw this watercourse** is available only for a selected Water article and replaces its marker with the next stroke, with selectable width, preserving its article link and publication visibility. Linked shapes use live geometry like marker positions; independent strokes use the existing drawing publication snapshot. Both are saved with the article.

Generated Realm, Faction, POI, Terrain, Landmark, Water and Path names use the formulas in [Cairn Naming Procedures](https://cairnrpg.com/second-edition/wardens-guide/naming-procedures/); forests use its dedicated adjective/noun tables. The copied tables in `names.json` retain source order and are licensed CC-BY-SA 4.0 by Cairn / Yochai Gal. Terrain names use matching terrain synonyms; POI names use their rolled site type. Applying the place formula to water, landmarks and paths is the application’s interpretation of the naming guidance. Culture, resources, traits, advantages and agendas keep descriptive headings; they are not named locations. Names are rolled once with the draft, retain the descriptive fields, and are preserved on save. Existing saved articles are not randomly renamed.
