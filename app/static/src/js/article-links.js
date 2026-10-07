import {Marked} from '../../vendor/markdown/marked.js';

export const articleURL = value => /^(?:\/materials\/[1-9]\d*\/edit|\/party\/[1-9]\d*\/materials\/[1-9]\d*)(?:#kw-h-[\w\p{L}\p{N}-]+)?$/u.test(value || '');
export const linkKey = value => {try {return decodeURIComponent(value).trim();} catch {return value.trim();}};
export const headingID = value => 'kw-h-' + value.normalize('NFKC').toLowerCase()
  .replace(/[^\p{L}\p{N}_\s-]/gu,'').replace(/[\s_]+/g,'-').replace(/^-+|-+$/g,'');
const escape = text => String(text).replace(/[&<>"']/g, char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

export function renderArticleMarkdown(value, references={}) {
  const counts = new Map();
  const parser = new Marked();
  parser.use({extensions:[{
    name:'wikiLink', level:'inline', start:src=>src.indexOf('[['),
    tokenizer(src) {
      const match=/^\[\[([^\]\n]+)\]\]/.exec(src);
      if(!match)return;
      const [target,...labels]=match[1].split('|');
      return {type:'wikiLink',raw:match[0],target:linkKey(target),label:labels.join('|').trim() || target.trim()};
    },
    renderer(token) {
      const url=references[token.target];
      return articleURL(url) ? `<a href="${escape(url)}">${escape(token.label)}</a>` : escape(token.label);
    }
  }],renderer:{
    link({href,tokens,title}) {
      const text=this.parser.parseInline(tokens), key=linkKey(href);
      if(!/^[a-zA-Z][a-zA-Z0-9+.-]*:|^\/\//.test(key)) {
        const url=references[key];
        return articleURL(url) ? `<a href="${escape(url)}">${text}</a>` : text;
      }
      return `<a href="${escape(href)}"${title ? ` title="${escape(title)}"` : ''}>${text}</a>`;
    },
    heading({tokens,depth}) {
      const text=this.parser.parseInline(tokens), plain=text.replace(/<[^>]*>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'");
      const slug=headingID(plain), count=(counts.get(slug)||0)+1;counts.set(slug,count);
      return `<h${depth} id="${escape(slug+(count>1 ? '-'+count : ''))}">${text}</h${depth}>\n`;
    }
  }});
  // Keep embeds literal until note/file transclusion is implemented.
  parser.use({extensions:[{name:'wikiEmbed',level:'inline',start:src=>src.indexOf('![['),
    tokenizer(src){const match=/^!\[\[[^\]\n]+\]\]/.exec(src);if(match)return {type:'wikiEmbed',raw:match[0]};},
    renderer:token=>escape(token.raw)}]});
  return parser.parse(value,{gfm:true,breaks:true});
}

export function wikiQuery(value, caret) {
  const before=value.slice(0,caret), match=/(?<!!)\[\[([^\]\n|]*)$/.exec(before);
  if(!match || before[before.length-match[0].length-1]==='\\')return null;
  let fence='', inline='';
  for(const line of before.split('\n')) {
    const marker=/^\s{0,3}(`{3,}|~{3,})/.exec(line)?.[1];
    if(marker){if(!fence)fence=marker;else if(marker[0]===fence[0] && marker.length>=fence.length)fence='';continue;}
    if(!fence)for(const run of line.match(/`+/g)||[]){if(!inline)inline=run;else if(run===inline)inline='';}
  }
  if(fence || inline)return null;
  return {start:caret-match[0].length, end:caret, query:match[1]};
}

export function linkSuggestions(query, articles) {
  const [name,...fragments]=query.split('#');
  const heading=fragments.length ? fragments.join('#') : undefined;
  const lower=name.toLocaleLowerCase();
  if(heading!==undefined) {
    const entry=articles.find(item=>item.title===name || item.path===name || item.path?.replace(/\.md$/,'')===name);
    return (entry?.headings || []).filter(item=>(item.path || item.title).toLocaleLowerCase().includes(heading.toLocaleLowerCase()))
      .slice(0,12).map(item=>({label:`${entry.title}#${item.path || item.title}`,path:entry.path || '',target:`${name}#${item.path || item.title}`}));
  }
  return articles.filter(item=>(item.title+' '+item.path).toLocaleLowerCase().includes(lower)).slice(0,12).map(item=>{
    const duplicate=articles.filter(other=>other.title===item.title).length>1;
    const target=duplicate && item.path ? item.path : item.title;
    return {label:item.title,path:item.path || '',target};
  });
}

let completionId=0;
function caretPosition(field) {
  const mirror=document.createElement('div'), style=getComputedStyle(field);
  for(const property of ['boxSizing','fontFamily','fontSize','fontWeight','fontStyle','lineHeight',
    'letterSpacing','textTransform','textIndent','textAlign','direction','tabSize',
    'paddingTop','paddingRight','paddingBottom','paddingLeft','borderTopWidth','borderRightWidth',
    'borderBottomWidth','borderLeftWidth','borderStyle'])mirror.style[property]=style[property];
  Object.assign(mirror.style,{position:'fixed',visibility:'hidden',pointerEvents:'none',
    left:'0',top:'0',width:(field.clientWidth+parseFloat(style.borderLeftWidth)+parseFloat(style.borderRightWidth))+'px',height:'auto',
    whiteSpace:'pre-wrap',overflowWrap:'break-word',overflow:'hidden'});
  mirror.textContent=field.value.slice(0,field.selectionStart);
  const marker=document.createElement('span');
  marker.textContent=field.value.slice(field.selectionStart) || '\u200b';mirror.append(marker);
  document.body.append(mirror);
  const point=marker.getClientRects()[0] || marker.getBoundingClientRect(), origin=mirror.getBoundingClientRect(), bounds=field.getBoundingClientRect();
  const lineHeight=parseFloat(style.lineHeight) || parseFloat(style.fontSize)*1.2;
  const result={x:bounds.left+point.left-origin.left-field.scrollLeft,
    y:bounds.top+point.top-origin.top-field.scrollTop,height:lineHeight};
  mirror.remove();return result;
}

export function setupLinkCompletion(field, context) {
  let articles, pending, query, selected=0;
  const menu=document.createElement('div');menu.className='article-link-completion';menu.hidden=true;
  menu.id=`article-link-options-${++completionId}`;
  field.setAttribute('aria-controls',menu.id);field.setAttribute('aria-autocomplete','list');
  menu.setAttribute('role','listbox');menu.setAttribute('aria-label','Article links');document.body.append(menu);
  const hide=()=>{menu.hidden=true;field.setAttribute('aria-expanded','false');field.removeAttribute('aria-activedescendant');};
  const position=()=>{
    if(menu.hidden)return;
    const caret=caretPosition(field), bounds=field.getBoundingClientRect(), margin=8;
    if(caret.y+caret.height<bounds.top || caret.y>bounds.bottom || bounds.bottom<0 || bounds.top>innerHeight){hide();return;}
    menu.style.maxHeight='256px';
    const below=Math.max(0,innerHeight-caret.y-caret.height-margin-4), above=Math.max(0,caret.y-margin-4);
    const upwards=below<Math.min(menu.scrollHeight,160) && above>below;
    menu.style.maxHeight=Math.min(256,upwards ? above : below)+'px';
    const size=menu.getBoundingClientRect();
    menu.style.left=Math.max(margin,Math.min(caret.x,innerWidth-size.width-margin))+'px';
    menu.style.top=Math.max(margin,upwards ? caret.y-size.height-4 : caret.y+caret.height+4)+'px';
  };
  const choose=target=>{
    if(!query)return;
    let end=query.end;
    if(field.value.slice(end,end+2)===']]')end+=2;
    field.focus();field.setSelectionRange(query.start,end);
    const text=`[[${target}]]`;
    if(!document.execCommand('insertText',false,text))field.setRangeText(text,query.start,end,'end');
    hide();field.dispatchEvent(new Event('input',{bubbles:true}));
  };
  const paint=()=>{[...menu.children].forEach((button,i)=>{button.setAttribute('aria-selected',String(i===selected));});
    if(!menu.hidden && menu.children[selected]){
      const option=menu.children[selected];
      field.setAttribute('aria-activedescendant',option.id);
      const bounds=menu.getBoundingClientRect(), item=option.getBoundingClientRect();
      const top=bounds.top+menu.clientTop, bottom=top+menu.clientHeight;
      if(item.top<top)menu.scrollTop-=top-item.top;
      else if(item.bottom>bottom)menu.scrollTop+=item.bottom-bottom;
    }};
  const update=async()=>{
    query=wikiQuery(field.value,field.selectionStart);if(!query){hide();return;}
    const campaign=context.campaign_id();
    const key=String(campaign);
    if(articles?.key!==key) {
      const url=new URL(context.catalog_url,location.origin);if(campaign)url.searchParams.set('campaign_id',campaign);
      if(!pending || pending.key!==key) {const promise=fetch(url,{cache:'no-store'}).then(response=>response.ok ? response.json() : Promise.reject()).then(data=>({key,items:data.articles}));pending={key,promise};}
      try{articles=await pending.promise;}catch{hide();return;}
    }
    query=wikiQuery(field.value,field.selectionStart);if(!query || String(context.campaign_id())!==key){hide();return;}
    const suggestions=linkSuggestions(query.query,articles.items);menu.replaceChildren();selected=0;
    for(const item of suggestions){const button=document.createElement('button');button.type='button';button.id=`${menu.id}-${menu.children.length}`;button.setAttribute('role','option');button.dataset.target=item.target;
      const title=document.createElement('span');title.className='article-link-title';title.textContent=item.label;button.append(title);
      if(item.path){const path=document.createElement('span');path.className='article-link-path';path.textContent=item.path;button.append(path);}
      const index=menu.children.length;
      button.addEventListener('pointermove',()=>{if(selected!==index){selected=index;paint();}});
      button.addEventListener('mousedown',event=>event.preventDefault());button.onclick=()=>choose(item.target);menu.append(button);}
    menu.hidden=!suggestions.length;field.setAttribute('aria-expanded',String(!menu.hidden));position();paint();
  };
  const keydown=event=>{
    if(menu.hidden)return;
    if(event.key==='Escape'){event.preventDefault();hide();}
    else if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();selected=(selected+(event.key==='ArrowDown'?1:-1)+menu.children.length)%menu.children.length;paint();}
    else if(['Enter','Tab'].includes(event.key)){event.preventDefault();choose(menu.children[selected].dataset.target);}
  };
  field.addEventListener('input',update);field.addEventListener('click',update);field.addEventListener('keydown',keydown);
  const scroll=event=>{if(!menu.contains(event.target))position();};
  document.addEventListener('scroll',scroll,true);window.addEventListener('resize',position);
  const resize=new ResizeObserver(position);resize.observe(field);
  const blur=()=>hide();field.addEventListener('blur',blur);
  return ()=>{field.removeEventListener('input',update);field.removeEventListener('click',update);field.removeEventListener('keydown',keydown);field.removeEventListener('blur',blur);
    document.removeEventListener('scroll',scroll,true);window.removeEventListener('resize',position);resize.disconnect();menu.remove();};
}
