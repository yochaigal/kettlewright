# Whiteboard

Whiteboard is a collaborative Excalidraw canvas for a party, with saved scenes, controlled actor tokens, presence, encounters and campaign material markers. The existing `/party/<id>/shared-map` page remains the entry point. All current party members can draw; only the Warden manages scenes, imports, fog, token visibility, encounters and material markers. Leaving the party revokes access, including already-open tabs.

## Deployment and compatibility

Stop the old workers, apply `flask db upgrade`, then start all updated workers together; mixed v1/v2 workers are unsupported. The new migration is revision `375a01`, following `296a02`. Existing boards become the first active scene, preserving their drawing, images, token geometry, versions and fog. Recognized actor images become managed token placements; orphan images remain ordinary drawings. Existing monster placements keep their previous visible state. Migration tests exercise upgrade and downgrade. Downgrade restores only the active scene to the old board format; retain a database backup to recover the other scenes and v2 features.

There is no frontend build: Excalidraw 0.18.0 and React 18.3.1 load from esm.sh. Reload existing Whiteboard tabs after deployment. Writes without the v2 scene context return `409 reload_required` instead of guessing which scene to overwrite. The existing Socket.IO/Redis deployment serves notifications and shared presence leases; development without Redis uses local presence and requires one worker.

## Scenes

The Warden can create, name, rename, duplicate and delete scenes. The scene selector changes only that Warden tab's view. **Show to party** activates the scene for all players. **Preparing privately** identifies a scene that is not active. Players cannot list or read private scenes, including by guessing their IDs. The active and last remaining scene cannot be deleted.

There is always one active scene. Its action reads **Shown to party** and is disabled; activation is an action, not a visibility toggle. Players stay there until the Warden shows another scene. To hide the current map, show a different scene, such as an empty scene. A visible explanation beside the scene controls describes this behavior before and after activation. Repeating activation of the current scene leaves the activation revision and player views unchanged.

Each scene retains drawing, token placements, fog, markers and encounter state. Actor HP and conditions remain in the ordinary Character/Companion records and are shared across scenes. Duplication copies placements, fog and links, preserving actor identities; encounter participants are copied with round 1 and all action marks cleared.

Local scene changes wait for drawing, fog and token queues to save. A forced player transition retains unsaved visual work in a downloadable `.excalidraw` draft and invalidates old queues. Both scene ID and the activation revision protect writes, including an A → B → A transition. Replacement of a scene also increments its generation.

## Editing and synchronization

Drawings autosave after approximately 400 ms, with one drawing request at a time. Socket.IO pushes confirmed drawing deltas without resending unchanged embedded images. Missing revisions, reconnects and visibility changes trigger authoritative HTTP refreshes. Repair polling runs every 60 seconds with a connected socket and every 15 seconds without one; background tabs skip HTTP refreshes. Drawing, fog, tokens, encounter and markers have independent revisions. Conditional reads also check viewer permissions and material publication revisions, so a revoked publication cannot survive an unchanged-drawing `204` response.

Concurrent free drawings rebase local changes onto the latest acknowledged state. Different objects are combined; same-object conflicts favor the local save. Camera, selection and theme stay local. The site's `localStorage.darkMode` preference remains shared across tabs. Warden-locked background objects remain protected on the server; free drawing stays collaborative.

Managed tokens never enter free-drawing saves. Each token operation verifies actor membership, current permissions, scene generation and token revision. Foreign token movement/deletion and forged actor elements in a free-drawing request are rejected or restored locally. A scene supports up to 2000 drawing elements and tokens, with up to 12 MB of validated PNG, JPEG, WebP or GIF image data. Frames and background colors are saved; executable links and embeds are disabled.

The bundled Architecture, Maps, Creatures, Planning and Clocks libraries preload without adding items to the canvas. Attribution and MIT licensing remain in `app/static/vendor/excalidraw-libraries/`.

## Presence and laser

The upper-right strip shows one icon per user viewing the same scene, including oneself. The first character in Party order supplies the portrait, with initials as a fallback; the Warden uses **W**. Tooltips identify the user, their characters and whether the tab is visible. Multiple tabs are combined: any visible tab in the scene makes the user active. A background tab is dimmed. Closing/disconnecting removes its connection; crashed worker leases expire within 60 seconds. A Warden preparing another scene is absent from the players' scene strip. Small screens show three icons followed by `+N`.

Presence is authenticated and CSRF-protected. Server workers renew their live socket leases every 15 seconds, so browser timer throttling does not remove an otherwise connected background tab. Redis makes leases visible across workers; Redis errors do not silently fall back to inaccurate worker-local state.

The native laser broadcasts transient scene coordinates, scoped to the authorized scene and generation. It does not create drawing elements or save requests. Membership, CSRF and rate limits are checked on the server. Private-scene lasers reach only Warden connections. Trails expire after 1.5 seconds and clear on disconnect or scene replacement.

## Tokens and actor actions

**Tokens** lists current party actors with the existing picker permissions: players see their own characters/pets and companions they can manage; the Warden also sees monsters. Placement uses an 80-unit circular image in the center of the view, or the drop location when dragged from **Party**. External portraits are loaded by the browser with CORS; the server never fetches user-controlled portrait URLs.

Players control their own characters and companions allowed by existing rules. The Warden can move every token. Stat editing and rolls retain sheet permissions. Selecting a token opens HP, sheet access and, for characters, the existing Deprived, Panicked and Dead controls. Dice use the shared modal; Warden rolls remain private by default. Live stats and portraits continue to refresh from the ordinary sheets.

Token visibility belongs to the placement. New monster tokens start hidden; the Warden sees them dimmed until **Show token**. Monster stat publication remains the existing creature-wide setting, independent of placement visibility and preserving public notes. Hidden placements, coordinates and artwork are omitted from player snapshots; private sheet notes never enter the shared drawing. Visible monsters with private stats use a neutral **Monster** label and cannot open a private sheet. Numbering is optional and changes displayed labels without renaming sheets.

Use Party's bulk monster creation to create independent creatures. Placing the same creature twice uses the same HP; separate Party monster records retain independent HP. Scene duplication never creates duplicate actor sheets.

## Encounter

Each scene has an independent, collapsible tracker with a round and an acted checkbox per actor. The Warden adds/removes participants, corrects marks, resets the encounter round or starts the next round. Players mark only actors they can control. There is no enforced initiative order or combat automation. Multiple placements of an actor still use one encounter row. Selecting a participant focuses an available token or opens the permitted sheet.

Hidden creatures are excluded from the player tracker. Visible monsters with private stats use neutral labels. Returning to a scene restores its round and marks.

## Maps and campaign materials

**Load map** previews a visual snapshot from the Warden's campaigns or Unfiled. Import defaults to a new, privately prepared scene. **Replace current scene** explicitly replaces drawing, tokens, encounter, markers and fog; the source remains unchanged. **Cover with fog** defaults on. Replacement checks all revisions, and both modes verify the source preview digest.

New imports preserve location links as separate markers. Original location titles and material bodies are not baked into the shared drawing. Players see only markers whose materials have published Party presentations, using the published titles and text. Warden-only markers retain the original title. Old independent imports have no link metadata and can be linked manually using **Add material marker**. Drag markers to reposition them.

Selecting a marker opens its material or, for the Warden, **Review and reveal**. The existing publication form preselects the current Party, allowing review/editing before publication. Creating a marker or importing a map never publishes an original automatically. Revocation or deletion removes the player-facing marker and closes access to the material.

## Fog of War

Fog remains a separate visual mask above drawings, tokens, annotations and markers. Warden controls include reveal/cover brushes, brush size, undo, hide all, reveal all and an opaque read-only player preview. The mask follows pan, zoom and viewport resizing. Fog saves are independent and operation IDs make retries idempotent.

Fog is visual hiding: player browsers receive the common background drawing. Server-side secrecy applies to private scenes, explicitly hidden tokens, private actor data and unpublished material markers. There are no walls, lighting, automatic token vision or individual player visibility. Player export remains disabled while fog is active.

## Focused checks

```sh
docker compose -f .devcontainer/docker-compose.yml exec -T \
  -e SQLALCHEMY_DATABASE_URI=sqlite:///:memory: -e USE_REDIS=False -e FLASK_DEBUG=0 \
  app python -m pytest -p no:flask tests/unit/test_shared_map.py \
  tests/unit/test_whiteboard*.py tests/unit/test_monsters.py tests/unit/test_socket_events.py -q
node --experimental-default-type=module --test tests/js/shared_map*.test.mjs \
  tests/js/whiteboard*.test.mjs tests/js/party_tokens.test.mjs \
  tests/js/token_stats.test.mjs tests/js/token_portraits.test.mjs \
  tests/js/actor_updates.test.mjs tests/js/board_rolls.test.mjs
```

Use Node 22. Redis integration additionally runs `test_whiteboard_presence.py` with `WHITEBOARD_TEST_REDIS_URL` set to an isolated Redis instance. Browser acceptance uses separate Warden/two-player sessions and covers private preparation, activation, token reload/persistence, ownership, HP, encounters, marker publication/revocation, both themes and mobile layout.
