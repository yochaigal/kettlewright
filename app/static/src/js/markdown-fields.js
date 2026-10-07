import {richContentHTML} from './rich-content.js';
import {formatMarkdown, markdownTools} from './markdown-editing.js';

// Enhance ordinary forms too, including HTMX replacements. Never change field names,
// submitted source, Alpine models, validation, or credential/number controls.
// SweetAlert2 builds every popup with a hidden .swal2-textarea, so skip its dialogs.
const enhanced=new WeakSet();
function enhance(root) {
  const fields=[...(root.matches?.('textarea,input[type=text]') ? [root] : []),...root.querySelectorAll('textarea,input[type=text]')];
  for(const field of fields) {
    if(enhanced.has(field) || field.closest('.rich-editor, .swal2-container') || field.hidden || field.readOnly || field.closest('[data-no-markdown]') || /json|password|username|email|url|search|filter|token/i.test(field.name || field.id)) continue;
    enhanced.add(field);
    if(field.tagName==='INPUT') {
      const preview=document.createElement('div'); preview.className='rich-content markdown-inline-preview';preview.hidden=true;preview.setAttribute('aria-hidden','true');field.after(preview);
      const update=()=>{preview.hidden=!/[*_`~]|\[[^\]]+\]\(/.test(field.value); if(!preview.hidden) preview.innerHTML=richContentHTML(field.value);};
      field.addEventListener('input',update);update();continue;
    }
    const wrapper=document.createElement('div');wrapper.className='markdown-field';
    field.before(wrapper);wrapper.append(field);
    if(document.querySelector('.view-character-sheet') || field.closest('.character-inline-form')) {
      wrapper.classList.add('markdown-compact');
      const hint=document.createElement('small');hint.className='markdown-hint';hint.textContent='Markdown supported';wrapper.append(hint);
      continue;
    }
    const toolbar=document.createElement('div');toolbar.className='markdown-toolbar';toolbar.setAttribute('role','toolbar');toolbar.setAttribute('aria-label','Text formatting');
    const preview=document.createElement('div');preview.className='rich-content markdown-preview';preview.hidden=true;
    const toggle=document.createElement('button');toggle.type='button';toggle.className='markdown-mode';toggle.textContent='Preview';toggle.setAttribute('aria-pressed','false');
    function write(){field.hidden=false;preview.hidden=true;toggle.textContent='Preview';toggle.setAttribute('aria-pressed','false');}
    for(const [action,title,glyph] of markdownTools){const button=document.createElement('button');button.type='button';const icon=document.createElement('i');icon.className=`fa-solid fa-${glyph}`;icon.setAttribute('aria-hidden','true');button.append(icon);button.title=title;button.setAttribute('aria-label',title);button.className=`markdown-${action}`;button.addEventListener('mousedown',e=>e.preventDefault());button.addEventListener('click',()=>{write();formatMarkdown(field,action);});toolbar.append(button);}
    toggle.addEventListener('click',()=>{if(field.hidden)write();else{preview.innerHTML=richContentHTML(field.value);field.hidden=true;preview.hidden=false;toggle.textContent='Write';toggle.setAttribute('aria-pressed','true');}});
    field.addEventListener('input',()=>{if(!preview.hidden)preview.innerHTML=richContentHTML(field.value);});
    toolbar.append(toggle);wrapper.prepend(toolbar);wrapper.append(preview);
  }
}
enhance(document);
new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes)if(node.nodeType===1)enhance(node);}).observe(document.body,{childList:true,subtree:true});

// Match physical keys as well as letters, including non-Latin keyboard layouts.
document.addEventListener('keydown',event=>{
  const field=event.target;
  if(!(event.ctrlKey || event.metaKey) || event.altKey || event.shiftKey || field.readOnly || field.disabled)return;
  if(!field.matches?.('textarea,input[type=text]') || !(enhanced.has(field) || field.closest('.rich-editor')))return;
  const action=event.code==='KeyB' || event.key.toLowerCase()==='b' ? 'bold'
    : event.code==='KeyI' || event.key.toLowerCase()==='i' ? 'italic' : null;
  if(!action)return;
  event.preventDefault();formatMarkdown(field,action);
});
