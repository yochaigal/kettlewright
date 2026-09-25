# Discord integration

Kettlewright handles Discord slash commands over HTTP in the existing Flask app. There is no Gateway connection or separate bot process. The integration is optional.

## Playing

1. Open **Account Settings → Discord → Connect Discord** in KW. Each player and the Warden connects their own accounts. Only Discord identity is requested; no email permission is needed. OAuth access tokens are not stored.
2. The Warden runs `/kw bind party:…` in a server channel, choosing one of their own parties. They must also have **Manage Channels** (or Administrator) in Discord. This authorizes publishing requested cards, summaries and rolls in that channel.
3. Each player runs `/kw select character:Bran`. Autocomplete lists only that player's characters in this channel's party, with IDs to distinguish identical names. Exact unambiguous names also work.
4. `/kw character` shows the selected character's live stats, effective HP, armor, conditions and sheet link.
5. `/kw roll dice:d20` rolls for that character. `2d6` and mixed dice such as `d6+d8` also work (at most two dice; d4, d6, d8, d10, d12, d20 and d100). Double rolls display the individual values, as on KW.****
6. `/kw party` shows the party roster and current stats; `/kw party page:2` pages through larger parties. `/kw login` links to account connection settings.

Selection belongs to the **KW user + Discord server + channel** and survives app restarts. Selecting a character never changes another user's selection or another channel's context. There is no character override on `/kw roll`. The Warden can only select and roll their own characters, just like every other player. Ownership and party membership are checked on every command. A removed, deleted or transferred character cannot be rolled using an old selection.

Several channels can be bound to the same party. A channel has at most one party. Threads are independent channels in this version: bind and select inside each thread. There is no implicit inheritance from categories or parent channels.

`/kw unbind` removes the binding and all selections in that channel. Rebinding also clears selections. Both require the current party's Warden and Manage Channels. Disconnecting in KW clears that user's selections and any bindings they created. A party ownership change invalidates its binding until the new Warden binds it.

Cards, party summaries and rolls are public to **everyone who can read that Discord channel**. Only linked party members (or its Warden) can request them. Private notes and party join codes are never included. Login, selection, binding responses and errors are visible only to the invoking user. Mentions are disabled.

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

Test with two players and a Warden: connect all three accounts, bind, select, switch characters, roll, verify KW history, and verify that the Warden cannot select another player's character. Test removal from a party and disconnection. Do not treat local mocked tests as proof of a working Discord installation.

## Implementation and limits

- Ed25519 signatures cover the unmodified request body; timestamps must be within five minutes. Commands are guild-only and rate-limited per Discord user using the existing Redis/in-process limiter, with the same worker-scope behavior as KW.
- Commands do not call the Discord API during execution. They respond directly to the interaction. Keep the endpoint within Discord's three-second response limit.
- A unique interaction receipt is claimed before executing a command and committed in the same transaction as its effects. Retries reuse the response instead of rerolling. Receipts expire after 24 hours and are cleaned during command handling.
- Both sheet and Discord dice are generated and validated by the same server service. Discord rolls appear in KW's existing party history and Socket.IO feed. Old browser tabs sending precomputed results must be refreshed after deployment.
- This version responds to Discord commands in their channel. It does **not** automatically forward rolls initiated on the website to Discord or update pinned messages. Reliable outbound forwarding would require delivery/retry handling.
- Character editing, save-resolution rules and inventory commands are outside this first version. Roll commands display dice values; they do not change stats.

References: [HTTP interactions](https://docs.discord.com/developers/interactions/receiving-and-responding), [application commands](https://docs.discord.com/developers/interactions/application-commands), [OAuth2](https://docs.discord.com/developers/topics/oauth2).
