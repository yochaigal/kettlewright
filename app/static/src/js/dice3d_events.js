// Plays 3D dice for rolls the server made outside the dice modal (app/lib/dice_feedback.py):
// a 'dice3d' event from an htmx response's HX-Trigger header, or dice queued before a redirect.
import dice3d from "./dice3d.js";

document.body.addEventListener("dice3d", (event) => {
  dice3d.show(event.detail);
});

const pending = document.getElementById("dice3d-pending");
if (pending) {
  try {
    dice3d.show(JSON.parse(pending.textContent));
  } catch (_) { /* A malformed payload only skips the animation. */ }
  pending.remove();
}
