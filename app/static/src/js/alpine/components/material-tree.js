export default function materialTree() {
  return {
    selected: [], query: '', matches: true, rootElement: null,
    init() {
      this.rootElement=this.$el;
      // Campaign groups remember whether they were open for this browser session.
      this.rootElement.querySelectorAll('details[data-tree-key]').forEach(details => {
        const key = `kw-tree:${location.pathname}:${details.dataset.treeKey}`;
        try {const saved=sessionStorage.getItem(key);if(saved!==null)details.open=saved==='true';} catch { /* Storage is optional. */ }
        details.addEventListener('toggle', () => {
          if (!this.filtering) try {sessionStorage.setItem(key,String(details.open));} catch { /* Storage is optional. */ }
        });
      });
    },
    get filtering() {return Boolean(this.query.trim());},
    clearFilters() {this.query='';this.filter();},
    filter() {
      const query=this.query.toLocaleLowerCase().trim();
      let matches=0;
      [...this.rootElement.querySelectorAll('[data-tree-row]')].reverse().forEach(row => {
        const own=(row.dataset.search || '').toLocaleLowerCase().includes(query);
        const descendant=[...row.querySelectorAll('[data-tree-row]')].some(child=>!child.hidden);
        row.hidden=Boolean(this.filtering && !own && !descendant);
        if (!row.hidden) matches++;
        // Open a collapsed campaign group when the search finds something inside it.
        if (this.filtering && descendant && row.tagName === 'DETAILS') row.open=true;
      });
      this.matches=matches>0;
    }
  };
}
