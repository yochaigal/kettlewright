# Shared Map

`FEATURE_TEST_USER_IDS` and `FEATURE_TEST_PARTY_IDS` are reusable tester allowlists for current and future experimental features. Shared maps currently use the party list: while this feature is in testing, it is available only for party IDs in `FEATURE_TEST_PARTY_IDS` (comma- or whitespace-separated). An empty/unset value disables access, including direct scene reads and writes. Existing owner/member permissions remain required; `FEATURE_TEST_USER_IDS` alone does not enable a party's map. Once shared maps are released to everyone, their allowlist check should be removed while the variables remain for testing other features. Restart application workers after changes. See [rollout configuration](campaigns.md#deployment-and-maintenance).

The top-right Shared Map link on a party page opens that party's independent
Excalidraw canvas, initially empty with the grid enabled. The Warden edits;
current party members can pan and zoom in view mode. Every change is public to
the party immediately. Campaign originals and published pointcrawl maps are
independent of this canvas.

Changes autosave after approximately 180 ms (one request at a time). Socket.IO
sends revision notifications through existing authenticated user rooms; clients
fetch the authoritative scene. Reconnects, tab visibility and a 10-second
fallback refresh recover missed updates and recheck access. The Warden's camera,
selection and cursors are never broadcast. Concurrent Warden tabs use optimistic
version checks; a conflict preserves local work for export and requires reload.

Creature tokens (Maffen), progress clocks (Nemeki) and adventure planning icons
(DemonDarakna) preload into the Warden's library on every page load. Open
Excalidraw's Library to insert individual items; the canvas remains untouched.
The creature sheet has been split into 99 independent, grouped tokens.
Their MIT license and attribution are under
`app/static/vendor/excalidraw-libraries/`.

Scenes support up to 2000 elements and 12 MB, including validated PNG, JPEG,
WebP and GIF images. Frames and canvas background colors are saved. External
embeds and element links are disabled. Grid, zoom and theme are local preferences.
Excalidraw 0.18.0 and React 18.3.1 load from esm.sh, without a frontend build.
Map data is stored in the application database, not an Excalidraw room.

Apply the migration with `flask db upgrade` (revision `298a01`). The existing
Socket.IO/Redis deployment configuration also serves map notifications.

Focused checks:

```sh
docker compose -f .devcontainer/docker-compose.yml exec -T \
  -e SQLALCHEMY_DATABASE_URI=sqlite:///:memory: -e USE_REDIS=False \
  app python -m pytest -p no:flask tests/unit/test_shared_map.py tests/unit/test_socket_events.py tests/unit/test_party_overview.py tests/unit/test_campaigns.py -q
node --test tests/js/shared_map.test.mjs
```
