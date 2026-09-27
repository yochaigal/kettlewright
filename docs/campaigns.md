# Campaigns and party knowledge

Open **Campaigns** to prepare a world. Each campaign belongs to one Warden and
can be connected to several of that Warden's parties. Its overview, NPCs,
locations, lore, factions, relics, notes and maps begin private.

**Reveal to party** opens a separate title and description for each connected
party. Copying the private original is an explicit action. Select the parties,
review their previews, then publish. Later changes to an original do not change
published versions. **Revoke publication** hides a version without deleting its
text, and **View as party** shows only that party's published knowledge.

A party's **Materials → Create and show** action creates a published material
without requiring a campaign or a private description. Its private original
can be filled in later. **Create and show map** similarly publishes an entire
new map draft to the selected party in one save; its later versions remain
independent of private edits. To organize it, open **Private original** and choose a
campaign; existing party versions stay intact. **Unfiled materials** lists
originals that have not been assigned to a campaign.

Descriptions are plain text with line breaks and clickable HTTP(S) links.
Related cards only appear to players when both cards have been published to
their party. Players can read materials, but cannot edit originals or versions.

## Pointcrawl maps

Create an empty map or generate a draft using the existing Dungeon, Forest or
Realm tables. Inspect the draft before saving; generating another draft replaces
only the unsaved draft. Tools results also offer **Create map**, which preserves
the already-rolled content and adds a connected layout with loops.

Drag locations on the SVG canvas or select them in the list and edit their
coordinates. Connect locations with standard, hidden or conditional paths.
Descriptions and conditions are edited through the location/path's private
card. Locations can link to another map in the same campaign (or another
unfiled map). The editor supports up to 200 locations and 800 paths.

Publish the map, locations and paths separately. A party sees a path only when
that path, both endpoints and the map have been revealed. Linked maps must also
be revealed independently. Location names, descriptions and known path types
may differ between parties; coordinates are shared. Removing a location from a
map keeps its standalone card. Removing a path also removes its publications.

## Tools

Each result can be saved privately or immediately shown to a party. Results are
structured objects shared by Tools and map generation, with the existing JSON
tables as their source. Handoff between these pages uses sessionStorage in the
same browser tab; save a result to retain it across sessions.

## Deployment and maintenance

Run `flask db upgrade` before serving this version. Revision `133a01` adds tables;
it does not create campaigns for existing parties. Deleting a party removes its
knowledge and campaign connections, while retaining campaign originals.
Disconnecting a party from a campaign revokes that campaign's publications.
Deleting a campaign moves its materials to **Unfiled materials** and retains
existing party versions.

Map geometry and content originals use separate optimistic version checks.
Conflicting saves return HTTP 409 instead of overwriting another tab. Published
views are built on the server without original prose. Socket.IO notifications
contain only party IDs; the browser fetches an authorized projection again.
Open views also recheck access on focus and every 30 seconds while visible.

Originals, campaign membership, party presentations and graph geometry are
separate tables so future campaign copying can omit party knowledge. Campaign
sharing, co-Wardens, player editing, uploads and inventory transfers are outside
this version.

## Validation

```sh
python -m pytest -p no:flask
node --experimental-default-type=module --test tests/js/content_generators.test.mjs
```

The campaign tests cover disclosure isolation, direct publication, adoption,
current party membership, CSRF, safe text, notification payloads, map graph
validation and concurrent updates. A separate migration test upgrades a database
with an existing party and checks downgrade compatibility. Generator tests use
seeded random sources to verify connectivity, loops and preservation of results.
