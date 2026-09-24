export default function collapseSection(storageKey) {
  return {
    collapsed: false,
    init() {
      try {
        this.collapsed = localStorage.getItem(storageKey) === 'hidden';
      } catch (_) { /* Preferences are optional. */ }
    },
    toggle() {
      this.collapsed = !this.collapsed;
      try {
        localStorage.setItem(storageKey, this.collapsed ? 'hidden' : 'visible');
      } catch (_) { /* Preferences are optional. */ }
    },
  };
}
