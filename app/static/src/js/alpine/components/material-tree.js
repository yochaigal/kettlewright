export default function materialTree() {
  return {
    selected: [], query: '', matches: true, rootElement: null,
    init() {
      this.rootElement=this.$el;
      this.rootElement.querySelectorAll('details[data-tree-key]').forEach(details => {
        const key = `kw-tree:${location.pathname}:${details.dataset.treeKey}`;
        try {const saved=sessionStorage.getItem(key);if(saved!==null)details.open=saved==='true';} catch { /* Storage is optional. */ }
        details.addEventListener('toggle', () => {
          if (!this.query) try {sessionStorage.setItem(key,String(details.open));} catch { /* Storage is optional. */ }
        });
      });
    },
    expand(open) {this.rootElement.querySelectorAll('details[data-tree-key]').forEach(item => {item.open=open;});},
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
    }
  };
}
