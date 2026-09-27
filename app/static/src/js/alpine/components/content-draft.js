export function contentDraft() {
  return {
    title:'', body:'', formElement:null,
    init() {
      this.formElement=this.$el;
      if (this.$el.dataset.import !== 'true' || !new URLSearchParams(location.search).has('from_tools') && !location.pathname.endsWith('/import')) return;
      try {
        const result = JSON.parse(sessionStorage.getItem('kw-content-result'));
        if (!result) return;
        this.$el.elements.title.value = result.title;
        this.$el.elements.body.value = result.body;
        if (this.$el.elements.category) this.$el.elements.category.value = result.category;
      } catch { /* A manual form remains usable if storage is unavailable. */ }
    },
    preview() {this.title=this.formElement.elements.title.value; this.body=this.formElement.elements.body.value;}
  };
}

export function revealContent() {
  return {
    rows:[], original:{},
    init() {
      this.rows = JSON.parse(this.$el.dataset.rows);
      this.original = JSON.parse(this.$el.dataset.original);
    },
    copyOriginal(row) {Object.assign(row, this.original);},
    copySelected(source) {
      for (const row of this.rows) if (row.selected) {
        row.title=source.title; row.body=source.body; row.path_type=source.path_type;
      }
    }
  };
}
