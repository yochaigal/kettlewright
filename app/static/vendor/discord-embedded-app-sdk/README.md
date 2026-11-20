# discord-embedded-app-sdk

[@discord/embedded-app-sdk](https://github.com/discord/embedded-app-sdk) 2.5.0 (MIT, see `LICENSE`),
esm.sh's single-file browser build (`https://esm.sh/@discord/embedded-app-sdk@2.5.0/es2022/embedded-app-sdk.mjs`),
with its dependencies bundled in and no imports.

Used by `src/js/activity/launch.js` to sign in inside a Discord Activity (#423). It is served by
Kettlewright because Discord's proxy follows redirects itself, so the Activity cannot be sent
to Discord's `/esm` URL mapping (docs/discord.md).
