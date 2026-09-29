// Native selection, input events and form submission remain the source of truth.
export function markdownEdit(value, start, end, action) {
  const selected=value.slice(start,end);
  const wraps={bold:['**','**'],italic:['*','*'],strike:['~~','~~'],code:['`','`'],link:['[','](https://example.com)']};
  let from=start,to=end,replacement,selectionStart,selectionEnd;
  if(wraps[action]) {
    const [left,right]=wraps[action];
    const hasFormatting=(before,after)=>{
      if(action==='italic')return (before.match(/\*+$/)?.[0].length || 0)%2===1 && (after.match(/^\*+/)?.[0].length || 0)%2===1;
      return before.endsWith(left) && after.startsWith(right);
    };
    const selectedLeft=selected.match(/^[*~`]+/)?.[0] || '';
    const selectedRight=selected.match(/[*~`]+$/)?.[0] || '';
    if(action!=='link' && hasFormatting(selectedLeft,selectedRight) && selected.length>=left.length+right.length){
      replacement=selected.slice(left.length,-right.length);selectionStart=from;selectionEnd=from+replacement.length;
    } else if(action!=='link' && hasFormatting(value.slice(0,start),value.slice(end))){
      from-=left.length;to+=right.length;replacement=selected;selectionStart=from;selectionEnd=from+replacement.length;
    } else {replacement=left+selected+right;selectionStart=from+left.length;selectionEnd=selectionStart+selected.length;}
  } else {
    from=start===0?0:value.lastIndexOf('\n',start-1)+1;
    const next=value.indexOf('\n',end);to=next<0?value.length:next;
    replacement=value.slice(from,to).split('\n').map((line,i)=>
      ({heading:'## ',quote:'> ',bullet:'- ',ordered:`${i+1}. `}[action] || '')+line).join('\n');
    selectionStart=from;selectionEnd=from+replacement.length;
  }
  return {from,to,replacement,selectionStart,selectionEnd};
}
export function formatMarkdown(field, action) {
  const edit=markdownEdit(field.value,field.selectionStart,field.selectionEnd,action);
  field.focus();field.setSelectionRange(edit.from,edit.to);
  // insertText keeps the browser's undo history for typing and toolbar edits.
  if(!document.execCommand('insertText',false,edit.replacement))field.setRangeText(edit.replacement,edit.from,edit.to);
  field.setSelectionRange(edit.selectionStart,edit.selectionEnd);
  field.dispatchEvent(new Event('input',{bubbles:true}));
}
export const markdownTools=[['bold','Bold','bold'],['italic','Italic','italic'],['heading','Heading','heading'],['strike','Strikethrough','strikethrough'],['bullet','Bullet list','list-ul'],['ordered','Numbered list','list-ol'],['quote','Quote','quote-left'],['link','Link','link'],['code','Code','code']];
