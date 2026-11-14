import test from 'node:test';
import assert from 'node:assert/strict';
import materialTree from '../../app/static/src/js/alpine/components/material-tree.js';

globalThis.location = {pathname: '/campaigns/'};
globalThis.sessionStorage = {getItem: () => null, setItem() {}};

function tree(openStates) {
  const details = openStates.map(open => ({open, dataset: {treeKey: 'k'}, addEventListener() {}}));
  const root = {
    querySelectorAll: selector => selector === 'details[data-tree-key]' ? details : [],
    addEventListener() {},
  };
  return {details, root};
}

function component(options, openStates) {
  const {details, root} = tree(openStates);
  const c = materialTree(options);
  c.$el = root;
  c.init();
  return {c, details};
}

test('collapsed pages close every branch and start on Expand all', () => {
  const {c, details} = component({collapsed: true}, [true, true]);
  assert.deepEqual(details.map(d => d.open), [false, false]);
  assert.equal(c.expanded, false);
});

test('toggle expands everything, then collapses everything', () => {
  const {c, details} = component({collapsed: true}, [false, false]);
  c.toggle();
  assert.deepEqual(details.map(d => d.open), [true, true]);
  assert.equal(c.expanded, true);
  c.toggle();
  assert.deepEqual(details.map(d => d.open), [false, false]);
  assert.equal(c.expanded, false);
});

test('pages without the collapsed option keep their open branches', () => {
  const {c} = component({}, [true, false]);
  assert.equal(c.expanded, true);
});
