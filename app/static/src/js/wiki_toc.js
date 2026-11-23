// "On this page" (#508): it scrolls on its own (CSS), and marks the section being read, keeping that
// link in view in a long list such as The Mansion's rooms.
export function currentHeading(tops, offset = 80) {
  // tops: each heading's distance from the top of the viewport, in page order.
  let current = 0;
  tops.forEach((top, index) => {if (top - offset <= 0) current = index;});
  return current;
}

const toc = typeof document === 'undefined' ? null : document.querySelector('.wiki-toc');
if (toc) {
  const links = [...toc.querySelectorAll('a[href^="#"]')];
  const headings = links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1))));
  const aside = toc.closest('.wiki-aside');
  let frame = 0, last = -1;
  const update = () => {
    frame = 0;
    const index = currentHeading(headings.map(heading => heading?.getBoundingClientRect().top ?? Infinity));
    if (index === last) return;
    last = index;
    links.forEach((link, i) => {if (i === index) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');});
    // Only the list scrolls, never the page.
    const link = links[index];
    if (aside && link && aside.scrollHeight > aside.clientHeight) {
      const top = link.offsetTop - aside.offsetTop, bottom = top + link.offsetHeight;
      if (top < aside.scrollTop || bottom > aside.scrollTop + aside.clientHeight) aside.scrollTop = top - aside.clientHeight / 3;
    }
  };
  addEventListener('scroll', () => {frame ||= requestAnimationFrame(update);}, {passive: true});
  update();
}
