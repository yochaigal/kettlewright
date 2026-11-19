// The first page Discord shows in the Activity (#423): sign in with the Embedded App SDK,
// then show the whiteboard of the party bound to this channel (/kw bind) in a frame.
// The SDK comes from esm.sh through Discord's /esm URL mapping (app/blueprints/activity.py).
import {DiscordSDK} from '/@discord/embedded-app-sdk@2.5.0';

// `show(message, link)` reports a problem; `frame(url)` shows the board.
export async function openBoard({sdk, config, post, show, frame}) {
  try {
    await sdk.ready();
    // Only "identify": Kettlewright needs to know who you are, nothing else from Discord.
    const {code} = await sdk.commands.authorize({client_id: config.clientId, response_type: 'code',
      state: '', prompt: 'none', scope: ['identify']});
    const response = await post(config.tokenUrl, {code, guild_id: sdk.guildId, channel_id: sdk.channelId});
    let data = {};
    try {data = await response.json();} catch (_) { /* Shown as a general failure below. */ }
    if (!response.ok || typeof data.board !== 'string') {
      show(data.message || config.messages.failed, data.link || '');
      return false;
    }
    frame(data.board, data.party || '');
    return true;
  } catch (_) {
    // Cancelled sign-in, a closed connection to Discord, or the network.
    show(config.messages.failed, '');
    return false;
  }
}

const configNode = globalThis.document?.getElementById('activity-config');
if (configNode) {
  const config = JSON.parse(configNode.textContent);
  const sdk = new DiscordSDK(config.clientId);
  const status = document.getElementById('activity-status');
  const link = document.getElementById('activity-link');
  openBoard({sdk, config,
    post: (url, body) => fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body), cache: 'no-store', signal: AbortSignal.timeout(20000)}),
    show(message, url) {
      document.getElementById('activity-message').textContent = message;
      link.hidden = !url;
      // Links leave Discord only through the SDK, which asks the player first.
      link.onclick = () => sdk.commands.openExternalLink({url});
    },
    frame(url, party) {
      const board = document.createElement('iframe');
      board.id = 'activity-board'; board.src = url; board.title = party;
      board.allow = 'clipboard-read; clipboard-write';
      document.body.append(board);
      status.hidden = true;
    }});
}
