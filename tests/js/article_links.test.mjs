import test from 'node:test';
import assert from 'node:assert/strict';
import {renderArticleMarkdown, articleURL, headingID, wikiQuery, linkSuggestions} from '../../app/static/src/js/article-links.js';
globalThis.document={documentElement:{lang:'en'},addEventListener(){}};
const {previewURL}=await import('../../app/static/src/js/article-preview.js');

test('wiki and relative Markdown links resolve only through supplied audience bindings',()=>{
  const html=renderArticleMarkdown('[[Village|home]] [history](places/Village.md#History) [[Hidden]] `[[Village]]` ![[Village]]',{
    Village:'/party/1/materials/2','places/Village.md#History':'/party/1/materials/2#kw-h-history'});
  assert.match(html,/<a href="\/party\/1\/materials\/2">home<\/a>/);
  assert.match(html,/#kw-h-history/);assert.match(html,/<code>\[\[Village\]\]<\/code>/);
  assert.match(html,/!\[\[Village\]\]/);assert.doesNotMatch(html,/href="Hidden"/);
  assert.doesNotMatch(renderArticleMarkdown('[[Village]]',{Village:'javascript:alert(1)'}),/<a /);
});
test('Unicode heading anchors match server convention, including duplicate headings',()=>{
  assert.equal(headingID('Зима и снег'),'kw-h-зима-и-снег');
  const html=renderArticleMarkdown('## Зима и **снег**\n\n## Зима и **снег**');
  assert.match(html,/id="kw-h-зима-и-снег-2"/);
});
test('article fragment links retain existing previews',()=>{
  assert.equal(articleURL('/party/1/materials/2#kw-h-history'),true);
  assert.equal(previewURL('/party/1/materials/2#kw-h-history','https://example.com'),'/party/1/materials/2/preview');
});
test('completion supports paths for duplicate titles and heading choices',()=>{
  const entries=[{title:'Village',path:'north/Village.md',headings:[{title:'History'}]},
    {title:'Village',path:'south/Village.md',headings:[]}];
  assert.equal(linkSuggestions('Vill',entries)[0].target,'north/Village.md');
  assert.equal(linkSuggestions('Vill',entries)[0].label,'Village');
  assert.equal(linkSuggestions('Vill',entries)[0].path,'north/Village.md');
  assert.equal(linkSuggestions('north/Village.md#Hi',entries)[0].target,'north/Village.md#History');
  assert.deepEqual(wikiQuery('See [[Vill',10),{start:4,end:10,query:'Vill'});
  assert.equal(wikiQuery('![[Vill',7),null);
  assert.equal(wikiQuery('`[[Vill',7),null);
  assert.equal(wikiQuery('```md\n[[Vill',12),null);
});
