import test from 'node:test';
import assert from 'node:assert/strict';
import {setTimeout as pause} from 'node:timers/promises';
import {initMonsterPreviews} from '../../app/static/src/js/monster-previews.js';

function node(values = {}) {
  return {...values, listeners: {}, attrs: {}, style: {}, children: [],
    addEventListener(event, listener) {this.listeners[event] = listener;},
    fire(event, value = {}) {this.listeners[event]?.(value);},
    append(child) {this.children.push(child);},
    contains(child) {return this === child || this.children.includes(child);},
    setAttribute(name, value) {this.attrs[name] = value;},
    matches() {return !!this.hovered;},
    focus() {document.activeElement = this; this.fire('focus');},
    getBoundingClientRect() {return {left: 50, right: 82, top: 100, bottom: 132};},
  };
}

function setup() {
  const saved = Object.fromEntries(['document', 'window', 'innerWidth', 'innerHeight'].map(key => [key, globalThis[key]]));
  const selectedOnly = node(), doc = node({body: node()}), win = node();
  doc.getElementById = () => selectedOnly;
  Object.assign(globalThis, {document: doc, window: win, innerWidth: 800, innerHeight: 600});
  const trigger = node({dataset: {preview: 'wolf'}}), closeButton = node();
  const panel = node({hidden: true, offsetWidth: 360, offsetHeight: 200});
  panel.children.push(closeButton);
  const renders = [];
  initMonsterPreviews({triggers: [trigger], panel, closeButton, render: key => renders.push(key)});
  return {trigger, panel, closeButton, doc, win, renders, restore() {
    closeButton.fire('click');
    Object.assign(globalThis, saved);
  }};
}

test('hover preview escapes the catalog and remains open while reading it', async () => {
  const ui = setup();
  try {
    ui.trigger.fire('pointerenter', {pointerType: 'mouse'});
    assert.equal(ui.panel.hidden, true);
    await pause(220);
    assert.equal(ui.panel.hidden, false);
    assert.equal(ui.doc.body.children[0], ui.panel);
    assert.equal(ui.panel.style.top, '138px');
    ui.trigger.fire('pointerleave');
    ui.panel.hovered = true;
    ui.panel.fire('pointerenter');
    await pause(220);
    assert.equal(ui.panel.hidden, false);
    ui.panel.hovered = false;
    ui.panel.fire('pointerleave');
    await pause(220);
    assert.equal(ui.panel.hidden, true);
  } finally {ui.restore();}
});

test('touch, keyboard dismissal and catalog scrolling keep preview state consistent', () => {
  const ui = setup();
  try {
    ui.trigger.fire('pointerenter', {pointerType: 'touch'});
    assert.equal(ui.panel.hidden, true);
    ui.trigger.focus();
    assert.equal(ui.panel.hidden, false);
    ui.trigger.fire('click');
    assert.equal(ui.doc.activeElement, ui.closeButton);
    ui.doc.fire('keydown', {key: 'Escape'});
    assert.equal(ui.panel.hidden, true);
    assert.equal(ui.doc.activeElement, ui.trigger);
    assert.equal(ui.trigger.attrs['aria-expanded'], 'false');
    ui.trigger.fire('click');
    ui.win.fire('scroll', {target: ui.panel});
    assert.equal(ui.panel.hidden, false);
    ui.win.fire('scroll', {target: ui.doc});
    assert.equal(ui.panel.hidden, true);
    assert.deepEqual(ui.renders, ['wolf', 'wolf']);
  } finally {ui.restore();}
});
