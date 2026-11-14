export default function materialTree(options = {}) {
  return {
    selected: [], query: '', matches: true, rootElement: null, expanded: false,
    init() {
      this.rootElement=this.$el;
      const collapsed=Boolean(options.collapsed);
      this.rootElement.querySelectorAll('details[data-tree-key]').forEach(details => {
        if (collapsed) {details.open=false;return;}
        const key = `kw-tree:${location.pathname}:${details.dataset.treeKey}`;
        try {const saved=sessionStorage.getItem(key);if(saved!==null)details.open=saved==='true';} catch { /* Storage is optional. */ }
        details.addEventListener('toggle', () => {
          if (!this.query) try {sessionStorage.setItem(key,String(details.open));} catch { /* Storage is optional. */ }
        });
      });
      this.rootElement.addEventListener('toggle', () => this.sync(), true);
      this.sync();
    },
    sync() {this.expanded=[...this.rootElement.querySelectorAll('details[data-tree-key]')].some(item => item.open);},
    toggle() {this.expand(!this.expanded);},
    expand(open) {this.rootElement.querySelectorAll('details[data-tree-key]').forEach(item => {item.open=open;});this.sync();},
    filter() {
      const query=this.query.toLocaleLowerCase().trim();
      let matches=0;
      [...this.rootElement.querySelectorAll('[data-tree-row]')].reverse().forEach(row => {
        const own=(row.dataset.search || '').toLocaleLowerCase().includes(query);
        const descendant=[...row.querySelectorAll('[data-tree-row]')].some(child=>!child.hidden);
        row.hidden=Boolean(query && !own && !descendant);
        if (!row.hidden) matches++;
        if (query && descendant) row.querySelectorAll('details[data-tree-key]').forEach(item=>{item.open=true;});
      });
      this.matches=matches>0;
      this.sync();
    }
  };
}
