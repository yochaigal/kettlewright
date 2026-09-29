import test from 'node:test';
import assert from 'node:assert/strict';
import {markdownEdit} from '../../app/static/src/js/markdown-editing.js';
const apply=(value,start,end,action)=>{const edit=markdownEdit(value,start,end,action);return {value:value.slice(0,edit.from)+edit.replacement+value.slice(edit.to),...edit};};
test('bold and italic wrap selected text and keep the words selected',()=>{
  const bold=apply('a word here',2,6,'bold');assert.equal(bold.value,'a **word** here');assert.equal(bold.selectionStart,4);assert.equal(bold.selectionEnd,8);
  const italic=apply('word',0,4,'italic');assert.equal(italic.value,'*word*');
});
test('repeating a shortcut removes formatting, including selected markers',()=>{
  assert.equal(apply('**word**',2,6,'bold').value,'word');
  assert.equal(apply('*word*',0,6,'italic').value,'word');
});
test('empty selection places the caret between markers',()=>{
  const edit=apply('',0,0,'bold');assert.equal(edit.value,'****');assert.equal(edit.selectionStart,2);assert.equal(edit.selectionEnd,2);
});
test('bold and italic combine and toggle independently',()=>{
  assert.equal(apply('**word**',2,6,'italic').value,'***word***');
  assert.equal(apply('**word**',0,8,'italic').value,'***word***');
  assert.equal(apply('***word***',3,7,'italic').value,'**word**');
  assert.equal(apply('***word***',3,7,'bold').value,'*word*');
});
test('lists apply to whole selected lines',()=>{
  assert.equal(apply('one\ntwo\nthree',0,7,'bullet').value,'- one\n- two\nthree');
});
