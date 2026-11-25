import test from 'node:test';
import assert from 'node:assert/strict';
import {confirmMessage} from '../../app/static/src/js/confirm-dialog.js';

const form = (boxes) => ({dataset: {confirm: 'Delete? Its parties are kept.'},
  querySelectorAll: selector => selector === '[data-confirm-unchecked]' ? boxes : []});

test('the confirmation follows a checkbox that changes what happens (Delete campaign: Keep its parties)', () => {
  const keep = {checked: true, dataset: {confirmUnchecked: 'Delete? Its parties are deleted too.'}};
  assert.equal(confirmMessage(form([keep])), 'Delete? Its parties are kept.');
  keep.checked = false;
  assert.equal(confirmMessage(form([keep])), 'Delete? Its parties are deleted too.');
  assert.equal(confirmMessage(form([])), 'Delete? Its parties are kept.');  // Forms without such a box ask as before.
});
