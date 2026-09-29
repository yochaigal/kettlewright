# Discord integration

Kettlewright handles Discord slash commands over HTTP in the existing Flask app. There is no Gateway connection or separate bot process. The integration is optional.

## Playing

Open the Discord page from the icon beside the language selector in Kettlewright. It also links to the [Cairn Discord server](https://discord.gg/T5Ykgw74DF). Each Warden and player connects their own Discord account there. Only Discord identity is requested; no email permission is needed. OAuth access tokens are not stored.

### Warden

1. [Install the Kettlewright app](https://discord.com/oauth2/authorize?client_id=1553017013016723556) on the Discord server.
2. Connect your Discord account on the Kettlewright Discord page. You must own the party in Kettlewright and have **Manage Channels** (or Administrator) in Discord.
3. Run `/kw bind party:…` in each channel you want to use, choosing one of your parties.

### Player

1. Connect your Discord account on the Kettlewright Discord page. Your character must be in the channel's bound party.
2. Run `/kw select character:…` in the bound channel. Autocomplete lists your characters there, with IDs to distinguish identical names. Exact unambiguous names also work.

### Other commands

- `/kw login` gives you a private link to the Kettlewright Discord page.
- `/kw character` shows your selected character's live stats, effective HP, armor, conditions and sheet link.
- `/kw party` shows the party roster and current stats; `/kw party page:2` pages through larger parties.
- `/kw roll dice:d20` rolls for your selected character. `2d6` and mixed dice such as `d6+d8` also work (at most two dice; d4, d6, d8, d10, d12, d20 and d100). Double rolls display the individual values, as on KW.
- `/kw roll` opens a private, reusable dice button panel for mobile play. Each click posts a public roll and records it in KW. Buttons belong to the player and selected character that opened them; after selecting a different character, open a new panel.
- `/kw unbind` removes the binding and all selections in the channel. It requires the current party's Warden and Manage Channels.

### Player sheet actions

All actions below affect **only your selected character** and return private confirmations. They save directly to KW. No Warden override is provided. Inventory and recipient autocomplete require a valid owned selection in the channel's current party.

| Command | Example / behavior |
| --- | --- |
| `/kw stat` | `/kw stat stat:hp value:-2` subtracts 2 HP; `stat:str value:7 mode:set` sets current STR to 7. Supports HP, STR, DEX and WIL. |
| `/kw condition` | `condition:deprived active:true` applies Deprived; `condition:panicked active:false` clears Panicked. |
| `/kw fatigue` | Adds one Fatigue to the main inventory; `amount:3` adds three. The entire request is rejected if it cannot fit. Clear Fatigue with `/kw remove`. |
| `/kw inventory` | Private item list with containers and remaining uses/charges, five items per page; `page:2` shows more. |
| `/kw add` | `name:Torch` uses the KW catalog's tags and uses. Custom names are supported, with optional `tags`, `uses`, `charges`, `description` and `container`. Does not charge gold. |
| `/kw use` | `item:Torch` spends one use; `amount:2` spends two. Use `resource:charges` for charges. `remove-empty:true` removes the item when the selected counter reaches zero; otherwise keep the exhausted item. |
| `/kw remove` | Permanently removes the selected item, including cleared Fatigue. |
| `/kw drop` | `item:Torch place:Beside the old bridge` moves the item into the party's **on the ground** container. The place is required (1–200 characters); description, uses and charges are preserved. |
| `/kw drop-container` | `container:Chest place:In the cellar` drops a container together with its contents and any containers it carries. The main inventory cannot be dropped. |
| `/kw ground` | Lists the party's dropped items and containers with their places; supports `page`. |
| `/kw pickup` | `item:…` picks a ground item up into your selected character's main inventory, or restores a whole dropped container and its contents. Autocomplete includes the place. Checks free slots, including a container's carrying load. |
| `/kw move` | Moves an item between your personal containers. |
| `/kw transfer` | Gives one of your items to another current character in this party, into their main inventory. Preserves the item and checks destination capacity before moving it. |
| `/kw note` | `text:Found a hidden passage.` appends a new line to existing character notes. The note is not echoed to Discord. Rejects additions exceeding the field's 2000-character limit. |

Choose items and containers from autocomplete, especially when names repeat. Item removal is permanent; use Drop for items you may recover. Fatigue cannot be dropped, moved or transferred through Discord, and carrying markers must be managed through their container in KW.

The same ground storage is available in the web interface. On your character sheet, use **Drop item** (the down-arrow button or the item dialog) or **Drop container** inside an extra container. Enter the place in the dialog. The party's Storage tabs and your inventory link open **on the ground**, where each entry shows its place and who dropped it; container entries also show their contents. Any current player can pick it up into one of their own characters in that party. This is a recorded location, not an automatic proximity check. Drop and pickup save immediately; an older full-editor Cancel cannot undo these shared changes.

Stat edits record the player's chosen changes; there is no automatic damage overflow into STR or save resolution. Values outside zero to the stat's maximum are rejected. HP edits change stored HP; panic or a full main inventory can still make effective HP zero. Maxima are unchanged. Already-open party views receive the existing KW refresh event; reload an individual sheet to see external edits.

Selection belongs to the **KW user + Discord server + channel** and survives app restarts. Selecting a character never changes another user's selection or another channel's context. There is no character override on `/kw roll`. The Warden can only select and roll their own characters, just like every other player. Ownership and party membership are checked on every command. A removed, deleted or transferred character cannot be rolled using an old selection.

Several channels can be bound to the same party. A channel has at most one party. Threads are independent channels in this version: bind and select inside each thread. There is no implicit inheritance from categories or parent channels.

Rebinding also clears selections. Both binding and unbinding require the current party's Warden and Manage Channels. Disconnecting in KW clears that user's selections and any bindings they created. A party ownership change invalidates its binding until the new Warden binds it.

Cards, party summaries and rolls are public to **everyone who can read that Discord channel**. Only linked party members (or its Warden) can request them. Private notes and party join codes are never included. Login, selection, binding responses, dice panels, inventory lists, sheet-action confirmations and errors are visible only to the invoking user. Mentions are disabled.

## Administrator setup

Create an application in the [Discord Developer Portal](https://discord.com/developers/applications). Configure **Guild Install** with `bot` and `applications.commands`. Use a dedicated test server first. Give the app access to the intended channel; View Channel and Send Messages are sufficient for this command surface. Privileged intents and Message Content access are not used. Users managing bindings need Manage Channels; the bot itself does not need that permission.

Set these variables in the server's private `.env` (never commit their values):

```dotenv
DISCORD_APPLICATION_ID=application_id
DISCORD_PUBLIC_KEY=application_public_key
DISCORD_CLIENT_SECRET=oauth_client_secret
DISCORD_BOT_TOKEN=bot_token
DISCORD_BASE_URL=https://kettlewright.com
```

`DISCORD_BASE_URL` must be the canonical externally reachable HTTPS URL, with no trailing path. The public key is used to verify interactions; the bot token is only used by the registration CLI. Account linking requires the client secret.

Install updated dependencies and run `flask db upgrade`, then restart the app using the deployment's existing process. For the existing local Dev Container, rebuilding the image installs dependencies and runs migrations on startup:

```bash
docker compose -f .devcontainer/docker-compose.yml up -d --build app
```

In the Developer Portal:

- Add the exact OAuth2 redirect: `https://your-kettlewright.example/account/discord/callback`.
- Set the Interactions Endpoint URL: `https://your-kettlewright.example/discord/interactions`. The running app must be reachable from Discord for its signed PING validation.
- Install the app into the test server using the application's installation link.

Register `/kw` in that server (immediate test scope):

```bash
flask discord register --guild YOUR_TEST_SERVER_ID
```

Inside the Dev Container, prefix Flask commands with `docker compose -f .devcontainer/docker-compose.yml exec app`. `flask discord register --dry-run` prints the definition without contacting Discord. Registration creates/updates only `/kw`; it does not bulk-delete other commands. After acceptance, register globally with `flask discord register`.

After deploying these player commands, **register `/kw` again** to update Discord's command picker and make the `dice` argument optional. This expansion adds no database migration or dependency. The existing PyNaCl dependency is still required for signed interactions.

Test with two players and a Warden: connect all three accounts, bind, select, switch characters, roll, verify KW history, and verify that the Warden cannot select another player's character. Test removal from a party and disconnection. Do not treat local mocked tests as proof of a working Discord installation.

For player-action acceptance, test on mobile: open `/kw roll`, click several dice, update HP, add/clear both conditions, add Fatigue and a Torch, spend uses, drop/pick up, transfer between two players, and append a note. Verify both sheets in KW, full-inventory rejection, old buttons after changing selection, and loss of access after leaving the party.

## Implementation and limits

- Ed25519 signatures cover the unmodified request body; timestamps must be within five minutes. Commands are guild-only and rate-limited per Discord user using the existing Redis/in-process limiter, with the same worker-scope behavior as KW.
- Commands do not call the Discord API during execution. They respond directly to the interaction. Keep the endpoint within Discord's three-second response limit.
- A unique interaction receipt is claimed before executing a command or button and committed in the same transaction as its effects. Retries reuse the response instead of rerolling, spending another use or moving/adding items again. Failed actions roll back their changes. Receipts expire after 24 hours and are cleaned during command handling.
- Both sheet and Discord dice are generated and validated by the same server service. Discord rolls appear in KW's existing party history and Socket.IO feed. Old browser tabs sending precomputed results must be refreshed after deployment.
- This version responds to Discord commands in their channel. It does **not** automatically forward rolls initiated on the website to Discord or update pinned messages. Reliable outbound forwarding would require delivery/retry handling.
- Player commands edit current stats, conditions, inventory and notes. Roll commands display dice values; they do not change stats or resolve saves automatically. Transfer targets are characters in the current party, not companions or party storage.

References: [HTTP interactions](https://docs.discord.com/developers/interactions/receiving-and-responding), [application commands](https://docs.discord.com/developers/interactions/application-commands), [button components](https://docs.discord.com/developers/components/reference), [OAuth2](https://docs.discord.com/developers/topics/oauth2).
