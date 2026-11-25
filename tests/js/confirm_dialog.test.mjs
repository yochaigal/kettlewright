import test from 'node:test';
import assert from 'node:assert/strict';
import {confirmMessage, applyChoices} from '../../app/static/src/js/confirm-dialog.js';

const form = (boxes) => ({dataset: {confirm: 'Delete? Its parties are kept.'},
  querySelectorAll: selector => selector === '[data-confirm-unchecked]' ? boxes : []});

test('the confirmation follows a checkbox that changes what happens (Delete campaign: Keep its parties)', () => {
  const keep = {checked: true, dataset: {confirmUnchecked: 'Delete? Its parties are deleted too.'}};
  assert.equal(confirmMessage(form([keep])), 'Delete? Its parties are kept.');
  keep.checked = false;
  assert.equal(confirmMessage(form([keep])), 'Delete? Its parties are deleted too.');
  assert.equal(confirmMessage(form([])), 'Delete? Its parties are kept.');  // Forms without such a box ask as before.
});

test('a choice in the confirmation reaches the form as a hidden field, or leaves it', () => {
  const fields = [];
  const form = {
    querySelectorAll: () => fields.filter(f => f.name === 'keep_parties'),
    append: field => { field.remove = () => fields.splice(fields.indexOf(field), 1); fields.push(field); },
  };
  const doc = {createElement: () => ({})};
  form.append({type: 'hidden', name: 'keep_parties', value: '1'});  // The form's default: keep them.
  const keep = {name: 'keep_parties', value: '1', checked: false, dataset: {}};
  applyChoices(form, [keep], doc);
  assert.deepEqual(fields, []);
  keep.checked = true;
  applyChoices(form, [keep], doc);
  assert.deepEqual(fields.map(f => [f.name, f.value]), [['keep_parties', '1']]);
  // Choices in the dialog count as much as ones in the form.
  assert.equal(confirmMessage({dataset: {confirm: 'kept'}, querySelectorAll: () => []},
    [{checked: false, dataset: {confirmUnchecked: 'deleted'}}]), 'deleted');
});
