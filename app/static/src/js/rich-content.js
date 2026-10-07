import TurndownService from '../../vendor/markdown/turndown.js';
import {renderArticleMarkdown, articleURL} from './article-links.js';
export const RICH_PREFIX = '<!--kw-rich-text:1-->';
export const MAX_CONTENT = 5*1024*1024;
export function remoteImageURL(value) {
  if (typeof value !== 'string' || /[\s\x00-\x1f\x7f\\]/.test(value) || !/^https?:\/\//.test(value)) return false;
  try {const url=new URL(value); return !!url.hostname && !url.username && !url.password;} catch {return false;}
}
export const imageURL = value => /^\/material-images\/[1-9][0-9]*\/[0-9a-f]{32}\.webp$/.test(value) || remoteImageURL(value) || /^data:image\/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$/.test(value);
const tags = new Set(['P','BR','STRONG','B','EM','I','U','S','H2','H3','BLOCKQUOTE','OL','UL','LI','A','IMG','DEL','H1','H4','H5','H6','PRE','CODE','HR','TABLE','THEAD','TBODY','TR','TH','TD']);

// Build a fresh allowlisted tree; never insert stored HTML directly into the page.
export function richContentHTML(value = '', references = {}) {
  const output = document.createElement('div');
  const template = document.createElement('template');
  template.innerHTML = value.startsWith(RICH_PREFIX) ? value.slice(RICH_PREFIX.length) : renderArticleMarkdown(value, references || {});
  function copy(source, target) {
    for (const node of source.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) {target.append(document.createTextNode(node.textContent)); continue;}
      if (node.nodeType !== Node.ELEMENT_NODE || ['SCRIPT','STYLE','IFRAME','OBJECT','SVG','MATH'].includes(node.tagName)) continue;
      if (!tags.has(node.tagName)) {copy(node,target); continue;}
      const element = document.createElement(node.tagName.toLowerCase());
      if (node.tagName === 'IMG') {
        const src=node.getAttribute('src') || '';
        if (!imageURL(src)) continue;
        element.setAttribute('src',src);
        element.setAttribute('alt',node.getAttribute('alt') || '');
      }
      if (node.tagName === 'A') {
        const href = node.getAttribute('href') || '';
        if (/^https?:\/\//i.test(href) || articleURL(href) && Object.values(references || {}).includes(href)) {
          element.setAttribute('href',href);
          element.setAttribute('rel','nofollow noopener noreferrer');
        }
      }
      if(/^H[1-6]$/.test(node.tagName) && /^kw-h-[\w\p{L}\p{N}-]+$/u.test(node.id))element.id=node.id;
      copy(node,element);
      target.append(element);
    }
  }
  copy(template.content,output);
  return output.innerHTML;
}

const converter = new TurndownService({headingStyle:'atx', bulletListMarker:'-', codeBlockStyle:'fenced'});
converter.addRule('strike', {filter:['s','del'], replacement:content=>`~~${content}~~`});
converter.keep(['u', 'table', 'thead', 'tbody', 'tr', 'th', 'td']);
export function markdownSource(value='') {
  return value.startsWith(RICH_PREFIX) ? converter.turndown(richContentHTML(value)) : value;
}
export function inlineContentHTML(value='') {
  const host=document.createElement('div');host.innerHTML=richContentHTML(value);
  for(const element of [...host.querySelectorAll('*')].reverse()) {
    if(element.tagName==='IMG')element.remove();
    else if(!['STRONG','B','EM','I','U','S','DEL','CODE'].includes(element.tagName))element.replaceWith(...element.childNodes);
  }
  return host.innerHTML.trim();
}
