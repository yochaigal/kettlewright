# Whiteboard

Whiteboard (formerly Shared Map) is an independent, collaborative Excalidraw canvas per party. The existing `/party/<id>/shared-map` URLs and drawings remain valid. All current party members can draw and edit; only the Warden can load a campaign map or change Fog of War. Only the Warden has **Reset the canvas** and **Open** in the menu. The server also refuses a player's save that would remove every unlocked object from a board with 10 or more; the player's page then puts the board back and says why (#437). The same happens to a player's change to locked objects. Leaving the party revokes read/write access.

## Access and deployment

Whiteboard is available to all current party members without tester lists. Its scene, tokens and laser require current membership; map sources, previews, imports and fog changes require the party Warden. Map sources also require ownership of the source map. See [access and deployment](campaigns.md#deployment-and-maintenance).

Apply `flask db upgrade` before starting the updated workers (revision `319a01`). The migration preserves existing drawings and initializes their fog as disabled. No frontend build is needed: Excalidraw 0.18.0 and React 18.3.1 load from esm.sh. The existing Socket.IO/Redis deployment serves board notifications.

## Editing and connection status

Drawings autosave after approximately 180 ms, with one drawing request at a time. Socket.IO uses the same WebSocket transport as the rest of the application. Confirmed drawing deltas and fog updates are pushed over Socket.IO and applied directly, without a GET per edit. Drawing deltas omit unchanged image data. Replacements send a complete new generation. Clients fetch the authoritative scene on first load, reconnect, missing base revisions, and tab visibility changes. Periodic HTTP refresh runs every 60 seconds with a connected socket and every 3 seconds without one. Updates arriving during a save or load are queued before applying them to the acknowledged base; pending local edits are rebased as usual. A socket outage alone does not report a save failure; HTTP errors and unsaved drawings retain their own state and retries.

Every scene read (including the 204 revision check) returns a fresh CSRF token in `X-CSRF-Token`, and the page uses it for saves, fog, rolls and the laser. The token embedded in the page expires after an hour, and boards stay open for whole sessions (#399, #400). A save or fog change refused with `{"reason": "csrf"}` renews the token with a read and is sent again. Other refusals carry `{"reason": "invalid", "message": …}`, and the status line shows that message, such as too many shapes, more than 12 MB, or an unsupported image (#386).

Concurrent drawing saves use optimistic versions and reapply local changes to the latest acknowledged scene. Different-object changes are combined; the last saved local change wins for the same object. Remote drawings clear local undo history. Camera, selection and theme remain local. Whiteboard reads and updates the site's `localStorage.darkMode` preference, including cross-tab changes.

The five bundled libraries preload without adding items to the canvas: Architecture, Maps, Creatures (99 grouped Maffen tokens), Planning and Clocks. Attribution and MIT licensing remain in `app/static/vendor/excalidraw-libraries/`. Scenes support 2000 elements and 12 MB of validated PNG, JPEG, WebP or GIF data. A new image larger than about 450 KB of PNG or JPEG, and every SVG, is redrawn as WebP (up to 1440 px) before it is saved; the save waits until it is done. A copy that is not smaller is not used, and images already on the board are left alone (#386). Frames and background colors are saved; external embeds and links are disabled.

## Laser pointer

The native laser tool broadcasts transient scene coordinates through the authenticated Socket.IO connection, at most 25 updates/second per tab. Current party membership, CSRF and board generation are checked on the server; a separate 40-event/second per-user limit bounds traffic. Other tabs render Excalidraw's fading laser above the fog, without adding drawing elements or save requests. Stale pointers expire after 1.5 seconds; disconnects and replacements clear them. Live laser sharing requires a working WebSocket; HTTP scene polling does not replay old laser trails.

## Party tokens

**Party tokens**, next to Library (in the header on small screens), lists all current party characters, their pets, hirelings and monsters for the Warden. Players see only their own characters and pets, plus hirelings they can manage and those hirelings’ pets. Monsters never appear in a player’s picker, even when their stats are public. These restrictions are enforced by the token-list endpoint. Companion cards identify their type and parent and use initials because companion sheets have no portrait field. Click a portrait to add an 80-unit circular token in the center of your view. Tokens use an embedded 256px PNG, share the normal drawing queue, and remain editable by all members and covered by fog. Existing tokens remain independent copies when a portrait or party membership changes. The picker refreshes its roster whenever opened.

Built-in and uploaded portraits work directly; external portraits require browser CORS permission. Unavailable images use initials with a notice. The server never fetches external portrait URLs. The member/feature-gated `/party/<id>/shared-map/tokens` endpoint returns only token IDs, names, portrait URLs and companion type/parent labels, with no-store caching. This custom picker does not change the upstream Excalidraw library format.

Current stats appear below each placed party token with known stats: characters, pets, hirelings and monsters. Maximum values are omitted. The compact block uses a two-column stat grid, a shield icon for armor, and minimal spacing. The entire block scales proportionally with the token’s scene size and camera zoom, including at small sizes. The viewer-specific `/party/<id>/shared-map/stats` endpoint omits private monsters for players, and never includes sheet notes or inventory. Overlays follow token movement, resizing, rotation, pan and zoom, sit beneath fog, and are not stored in the shared drawing or its exports. Stats refresh on roster/visibility events, reconnect, returning to the tab, and every five seconds; a failed read clears stale stats. Warden player-preview hides private stats and visibility controls.

The Warden can toggle monster stats with the eye beside them. Revealing requires a confirmation dialog; cancellation makes no request. Visibility belongs to the creature, so all copies of its token update together. This toggle preserves existing public notes. The single lock icon toggles background locking without locking party tokens.

**Party**, after the back-to-party arrow, opens the main party page beside the map for both roles, with the normal server-enforced permissions. Its highlight is active only while the panel is open. Theme, Fit map and Load map follow as a group of icons with tooltips. **Roll Dice** uses the shared player/Warden modal; Warden special rolls and the default-private public-roll opt-in are preserved. **Public roll** starts off each time the board opens; once switched on it stays on whichever token is selected, and the roller and dice-modal switches are one setting. A private roll still refreshes the Warden's own roll history (#399). History remains on the party page.

## Load map

**Load map** is turned off for now (#438): there are no campaign maps worth loading yet. Set `WHITEBOARD_LOAD_MAP=true` in the environment to show it again; the routes below stay in place, for the Warden only.

The Warden chooses a map from their campaigns or Unfiled and previews its visual snapshot. The snapshot contains the drawing, images, nodes with numbers/titles, and paths with their visual styles. It excludes material descriptions, links, and nested-map contents. Fresh IDs and remapped file/group/binding references turn graph glyphs into independent editable elements. The source is never modified or automatically synchronized.

**Replace whiteboard** confirms replacement of the current drawing and fog for the whole party. **Cover with fog** is selected by default. The server verifies source ownership, the preview digest, and current board revisions before replacing both atomically. A changed source or board requires a fresh preview.

Every replacement increments the board generation. Open clients must discard their old save queue rather than merging it into the replacement. Unsaved old drawings/fog are retained in a downloadable local `.excalidraw` draft until that tab is closed. Legacy clients without a generation can save only to generation 1; they must reload after a replacement.

## Fog of War v1

Fog is a separate canvas mask above the drawing and below Excalidraw controls. It covers the infinite canvas, including tokens and annotations. The Warden sees it at 45% opacity, as a dark tint, or a light one in dark mode, where a dark tint barely shows on the inverted board (#453); players see an opaque dark mask. **Player view** gives the Warden an opaque, read-only preview.

The Warden can enable/disable fog, reveal or cover with a round brush, adjust its scene-space radius, undo the last fog stroke, hide all, or reveal all. Mass changes require confirmation. The same revealed areas apply to every player. Stroke coordinates follow pan, zoom, Fit and viewport resizing. In brush mode, space-drag or middle-drag pans the canvas.

Completed strokes enter an independent save queue with operation IDs and a fog revision. Retries are idempotent within the last 1000 acknowledged operations. The server accepts fog writes only from the current Warden and checks the board generation. Fog updates never overwrite drawings; drawing updates never overwrite fog. Invalid changes stay visible locally with a discard action. Fog payloads are limited to 2 MB, 5000 points per stroke, and finite bounded coordinates; reset an excessively complex mask before adding more strokes.

This is visual hiding, not server-side secrecy: the player's browser still receives the complete drawing. The ordinary player export menu is disabled while fog is active because it would omit the mask. Fog is independent of selection, erasing and drawing undo. There are no walls, lighting, automatic token vision or individual player visibility in v1.

## Dungeon brush

For the Warden, the island at the top of the board holds the **Dungeon** tools (left) and the **Fog** tools (right); less frequent actions are in each group's ⋯ menu. Excalidraw's drawing tools and the laser pointer move to a rail on the left. Players keep Excalidraw's usual layout, and on narrow screens the Warden tools sit in a row above the board. The Dungeon tools draw grid dungeons quickly, like a wet-erase marker on a battle mat (#439):

- **Draw**: drag over the grid to draw floor. Walls appear wherever floor meets empty space and move as the floor grows. Hold Alt to erase.
- **Erase**: drag to remove squares; the walls close up behind.
- **Doors**: click an outer wall to make it a door, then an opening, then a wall again. Click between two floor squares to add an inner wall, then a door.
- **Clear dungeon** in the ⋯ menu removes the whole dungeon.
- **Floor color** (the swatch, #453): Stone, Slate, Sand, Wood, Moss, Water, Lava or Arcane. Choosing a color switches to Draw; painting over floor gives it the new color, and walls and doors stay as they are. The choice is remembered on that device.

Each square is one token wide (80 px).

The dungeon is saved as ordinary, locked Excalidraw rectangles and lines underneath everything else, so saving, live sync, undo (Ctrl+Z) and export work as for any drawing. Their IDs (`dungeon-<size>-floor|wall|door-…`) encode the geometry, so the brush reads the dungeon back from the board and stores nothing extra. Floors are merged into rectangles and walls into long lines to stay within the board's 2000 shapes; the brush refuses a change that would exceed it. **Lock map** unlocks dungeon shapes along with the rest of the map; the next brush stroke redraws any that were moved. Fog of War is drawn above the dungeon. Squares of one color merge into rectangles, and each floor's fill is its color, so colors need no extra data either; floors drawn before colors existed read back as Stone.

## Focused checks

```sh
docker compose -f .devcontainer/docker-compose.yml exec -T \
  -e SQLALCHEMY_DATABASE_URI=sqlite:///:memory: -e USE_REDIS=False -e FLASK_DEBUG=0 \
  app python -m pytest -p no:flask tests/unit/test_shared_map.py tests/unit/test_whiteboard.py tests/unit/test_whiteboard_migration.py tests/unit/test_feature_access.py tests/unit/test_socket_events.py -q
node --test tests/js/shared_map*.test.mjs tests/js/whiteboard*.test.mjs tests/js/party_tokens.test.mjs tests/js/token_stats.test.mjs
```

Library validation covers both Excalidraw v1 and v2 formats, including legacy freehand points with pressure values. Browser checks require independent Warden/player sessions and should cover imports, both themes, fog editing/undo, pan/zoom, player editing, replacement and reconnect.
