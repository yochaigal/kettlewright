# Whiteboard

Whiteboard (formerly Shared Map) is an independent, collaborative Excalidraw canvas per party. The existing `/party/<id>/shared-map` URLs and drawings remain valid. All current party members can draw and edit; only the Warden can load a campaign map or change Fog of War. Leaving the party revokes read/write access.

## Access and deployment

`FEATURE_TEST_PARTY_IDS` continues to gate Whiteboard, including its scene, sources, import and fog APIs. `FEATURE_TEST_USER_IDS` alone does not enable a party's board. The local development feature override also remains supported. See [rollout configuration](campaigns.md#deployment-and-maintenance).

Apply `flask db upgrade` before starting the updated workers (revision `319a01`). The migration preserves existing drawings and initializes their fog as disabled. No frontend build is needed: Excalidraw 0.18.0 and React 18.3.1 load from esm.sh. The existing Socket.IO/Redis deployment serves board notifications.

## Editing and connection status

Drawings autosave after approximately 180 ms, with one drawing request at a time. Socket.IO uses the same WebSocket transport as the rest of the application. Confirmed drawing deltas and fog updates are pushed over Socket.IO and applied directly, without a GET per edit. Drawing deltas omit unchanged image data. Replacements send a complete new generation. Clients fetch the authoritative scene on first load, reconnect, missing base revisions, and tab visibility changes. Periodic HTTP refresh runs every 60 seconds with a connected socket and every 3 seconds without one. Updates arriving during a save or load are queued before applying them to the acknowledged base; pending local edits are rebased as usual. A socket outage alone does not report a save failure; HTTP errors and unsaved drawings retain their own state and retries.

Concurrent drawing saves use optimistic versions and reapply local changes to the latest acknowledged scene. Different-object changes are combined; the last saved local change wins for the same object. Remote drawings clear local undo history. Camera, selection and theme remain local. Whiteboard reads and updates the site's `localStorage.darkMode` preference, including cross-tab changes.

The five bundled libraries preload without adding items to the canvas: Architecture, Maps, Creatures (99 grouped Maffen tokens), Planning and Clocks. Attribution and MIT licensing remain in `app/static/vendor/excalidraw-libraries/`. Scenes support 2000 elements and 12 MB of validated PNG, JPEG, WebP or GIF data. Frames and background colors are saved; external embeds and links are disabled.

## Laser pointer

The native laser tool broadcasts transient scene coordinates through the authenticated Socket.IO connection, at most 25 updates/second per tab. Current party membership, experimental access, CSRF and board generation are checked on the server; a separate 40-event/second per-user limit bounds traffic. Other tabs render Excalidraw's fading laser above the fog, without adding drawing elements or save requests. Stale pointers expire after 1.5 seconds; disconnects and replacements clear them. Live laser sharing requires a working WebSocket; HTTP scene polling does not replay old laser trails.

## Party tokens

**Party tokens**, next to Library (in the header on small screens), lists current party characters in party order, their pets, party hirelings, and hirelings’ pets. Companion cards identify their type and parent and use initials because companion sheets have no portrait field. Click a portrait to add an 80-unit circular token in the center of your view. Tokens use an embedded 256px PNG, share the normal drawing queue, and remain editable by all members and covered by fog. Existing tokens remain independent copies when a portrait or party membership changes. The picker refreshes its roster whenever opened.

Built-in and uploaded portraits work directly; external portraits require browser CORS permission. Unavailable images use initials with a notice. The server never fetches external portrait URLs. The member/feature-gated `/party/<id>/shared-map/tokens` endpoint returns only token IDs, names, portrait URLs and companion type/parent labels, with no-store caching. This custom picker does not change the upstream Excalidraw library format.

## Load map

The Warden chooses a map from their campaigns or Unfiled and previews its visual snapshot. The snapshot contains the drawing, images, nodes with numbers/titles, and paths with their visual styles. It excludes material descriptions, links, and nested-map contents. Fresh IDs and remapped file/group/binding references turn graph glyphs into independent editable elements. The source is never modified or automatically synchronized.

**Replace whiteboard** confirms replacement of the current drawing and fog for the whole party. **Cover with fog** is selected by default. The server verifies source ownership, the preview digest, and current board revisions before replacing both atomically. A changed source or board requires a fresh preview.

Every replacement increments the board generation. Open clients must discard their old save queue rather than merging it into the replacement. Unsaved old drawings/fog are retained in a downloadable local `.excalidraw` draft until that tab is closed. Legacy clients without a generation can save only to generation 1; they must reload after a replacement.

## Fog of War v1

Fog is a separate canvas mask above the drawing and below Excalidraw controls. It covers the infinite canvas, including tokens and annotations. The Warden sees it at 45% opacity; players see an opaque mask. **Player view** gives the Warden an opaque, read-only preview.

The Warden can enable/disable fog, reveal or cover with a round brush, adjust its scene-space radius, undo the last fog stroke, hide all, or reveal all. Mass changes require confirmation. The same revealed areas apply to every player. Stroke coordinates follow pan, zoom, Fit and viewport resizing. In brush mode, space-drag or middle-drag pans the canvas.

Completed strokes enter an independent save queue with operation IDs and a fog revision. Retries are idempotent within the last 1000 acknowledged operations. The server accepts fog writes only from the current Warden and checks the board generation. Fog updates never overwrite drawings; drawing updates never overwrite fog. Invalid changes stay visible locally with a discard action. Fog payloads are limited to 2 MB, 5000 points per stroke, and finite bounded coordinates; reset an excessively complex mask before adding more strokes.

This is visual hiding, not server-side secrecy: the player's browser still receives the complete drawing. The ordinary player export menu is disabled while fog is active because it would omit the mask. Fog is independent of selection, erasing and drawing undo. There are no walls, lighting, automatic token vision or individual player visibility in v1.

## Focused checks

```sh
docker compose -f .devcontainer/docker-compose.yml exec -T \
  -e SQLALCHEMY_DATABASE_URI=sqlite:///:memory: -e USE_REDIS=False -e FLASK_DEBUG=0 \
  app python -m pytest -p no:flask tests/unit/test_shared_map.py tests/unit/test_whiteboard.py tests/unit/test_whiteboard_migration.py tests/unit/test_feature_access.py tests/unit/test_socket_events.py -q
node --test tests/js/shared_map*.test.mjs tests/js/whiteboard*.test.mjs tests/js/party_tokens.test.mjs
```

Library validation covers both Excalidraw v1 and v2 formats, including legacy freehand points with pressure values. Browser checks require independent Warden/player sessions and should cover imports, both themes, fog editing/undo, pan/zoom, player editing, replacement and reconnect.
