// The whiteboard's theme before its first paint (#470). The board's module (shared_map.js) waits for
// Excalidraw to download, so it cannot set dark mode early enough: the page showed light, then dark.
// A classic script, loaded first thing in <body>, runs before anything paints. It is a file, not inline
// script, because a Discord Activity runs none (docs/discord.md). shared_map.js keeps the theme after this.
try {
  if (localStorage.getItem('darkMode') === 'true') document.body.classList.add('dark-mode');
} catch (_) { /* Storage blocked: the board stays light. */ }
