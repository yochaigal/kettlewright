import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const launchSource = readFileSync(new URL('../../app/static/src/js/activity/launch.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const boardSource = readFileSync(new URL('../../app/static/src/js/activity/board.js', import.meta.url), 'utf8');

function launcher() {
  const context = vm.createContext({globalThis: {}});
  vm.runInContext(launchSource + '\nthis.openBoard = openBoard;', context);
  return context.openBoard;
}
const config = {clientId: '900', tokenUrl: '/activity/token', messages: {failed: 'Failed'}};
function sdk({authorize = async () => ({code: 'abc'}), ready = async () => {}} = {}) {
  const calls = [];
  return {calls, guildId: '10', channelId: '20', ready,
    commands: {authorize: async options => {calls.push(options); return authorize(options);}}};
}

test('the Activity signs in with identify only and opens the board of the channel (#423)', async () => {
  const discord = sdk(), posts = [], frames = [], shown = [];
  const opened = await launcher()({sdk: discord, config, show: (...args) => shown.push(args), frame: (...args) => frames.push(args),
    post: async (url, body) => {posts.push([url, body]); return {ok: true, json: async () => ({board: '/activity/board/1?ticket=t', party: 'Party'})};}});
  assert.equal(opened, true);
  assert.deepEqual(JSON.parse(JSON.stringify(discord.calls)), [{client_id: '900', response_type: 'code', state: '', prompt: 'none', scope: ['identify']}]);
  assert.deepEqual(JSON.parse(JSON.stringify(posts)), [['/activity/token', {code: 'abc', guild_id: '10', channel_id: '20'}]]);
  assert.deepEqual(frames, [['/activity/board/1?ticket=t', 'Party']]);
  assert.deepEqual(shown, []);
});

test('a refusal shows its reason and a link to Kettlewright', async () => {
  const shown = [], frames = [];
  const opened = await launcher()({sdk: sdk(), config, show: (...args) => shown.push(args), frame: (...args) => frames.push(args),
    post: async () => ({ok: false, json: async () => ({reason: 'not_linked', message: 'Connect first', link: 'https://kw.example/account/discord'})})});
  assert.equal(opened, false);
  assert.deepEqual(shown, [['Connect first', 'https://kw.example/account/discord']]);
  assert.deepEqual(frames, []);
});

test('a cancelled sign-in or a broken response shows the general failure', async () => {
  for (const options of [{authorize: async () => {throw new Error('cancelled');}}, {ready: async () => {throw new Error('closed');}}]) {
    const shown = [];
    assert.equal(await launcher()({sdk: sdk(options), config, show: (...args) => shown.push(args), frame() {},
      post: async () => assert.fail('no request after a failed sign-in')}), false);
    assert.deepEqual(shown, [['Failed', '']]);
  }
  const shown = [];
  await launcher()({sdk: sdk(), config, show: (...args) => shown.push(args), frame() {},
    post: async () => ({ok: true, json: async () => {throw new SyntaxError('html');}})});
  assert.deepEqual(shown, [['Failed', '']]);
});

function boardPage() {
  const sent = [], faces = [];
  class FontFace {constructor(family, source) {faces.push([family, source]);}}
  const window = {fetch: async request => {sent.push(request); return {ok: true};}, FontFace, addEventListener() {}};
  const context = vm.createContext({window, Request, Headers, URL, HTMLScriptElement: class {}, location: {href: 'https://900.discordsays.com/activity/board/1', origin: 'https://900.discordsays.com'},
    document: {currentScript: {dataset: {assetPath: '/esm/@excalidraw/excalidraw@0.18.0/dist/prod/'}},
      getElementById: id => ({textContent: id === 'shared-map-config' ? JSON.stringify({activityToken: 'board-token', messages: {}}) : ''})}});
  vm.runInContext(boardSource, context);
  return {window, sent, faces};
}

test('inside Discord every Kettlewright request carries the board token, and only those', async () => {
  const {window, sent} = boardPage();
  await window.fetch('/party/1/shared-map/scene?version=1', {cache: 'no-store', headers: {Accept: 'application/json'}});
  await window.fetch(new URL('https://900.discordsays.com/party/1/shared-map/roll'), {method: 'POST', body: 'x=1'});
  await window.fetch('https://elsewhere.example/data.json');
  assert.equal(sent[0].headers.get('Authorization'), 'Bearer board-token');
  assert.equal(sent[0].headers.get('Accept'), 'application/json');
  assert.equal(sent[0].cache, 'no-store');
  assert.equal(sent[1].method, 'POST');
  assert.equal(await sent[1].text(), 'x=1');
  assert.equal(sent[1].headers.get('Authorization'), 'Bearer board-token');
  assert.equal(sent[2].headers.get('Authorization'), null);
});

test('Excalidraw loads its fonts through the proxy, never from esm.sh itself', () => {
  const {window, faces} = boardPage();
  assert.equal(window.EXCALIDRAW_ASSET_PATH, 'https://900.discordsays.com/esm/@excalidraw/excalidraw@0.18.0/dist/prod/');
  new window.FontFace('Excalifont', "url(https://900.discordsays.com/esm/a.woff2) format('woff2'), url(https://esm.sh/a.woff2) format('woff2')");
  new window.FontFace('Only', "url(https://esm.sh/b.woff2) format('woff2')");
  assert.deepEqual(faces, [['Excalifont', "url(https://900.discordsays.com/esm/a.woff2) format('woff2')"],
    ['Only', "url(https://esm.sh/b.woff2) format('woff2')"]]);
});
