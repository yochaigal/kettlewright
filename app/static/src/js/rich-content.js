export const RICH_PREFIX = '<!--kw-rich-text:1-->';
export const MAX_CONTENT = 5*1024*1024;
export function remoteImageURL(value) {
  if (typeof value !== 'string' || /[\s\x00-\x1f\x7f\\]/.test(value) || !/^https?:\/\//.test(value)) return false;
  try {const url=new URL(value); return !!url.hostname && !url.username && !url.password;} catch {return false;}
}
export const imageURL = value => /^\/material-images\/[1-9][0-9]*\/[0-9a-f]{32}\.webp$/.test(value) || remoteImageURL(value) || /^data:image\/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$/.test(value);
const tags = new Set(['P','BR','STRONG','B','EM','I','U','S','H2','H3','BLOCKQUOTE','OL','UL','LI','A','IMG']);

// Build a fresh allowlisted tree; never insert stored HTML directly into the page.
export function richContentHTML(value = '') {
  const output = document.createElement('div');
  if (!value.startsWith(RICH_PREFIX)) {
    for (const [index, line] of value.split('\n').entries()) {
      if (index) output.append(document.createElement('br'));
      output.append(document.createTextNode(line));
    }
    return output.innerHTML;
  }
  const template = document.createElement('template');
  template.innerHTML = value.slice(RICH_PREFIX.length);
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
        if (/^https?:\/\//i.test(href)) {
          element.setAttribute('href',href);
          element.setAttribute('rel','nofollow noopener noreferrer');
        }
      }
      copy(node,element);
      target.append(element);
    }
  }
  copy(template.content,output);
  return output.innerHTML;
}
