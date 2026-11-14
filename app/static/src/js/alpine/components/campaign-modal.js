// A Bulma modal opened by its own trigger button. Focus moves into the dialog
// on open and returns to the trigger on close; Escape and the backdrop close it.
export default function campaignModal(initiallyOpen = false) {
  return {
    open: false,
    init() {
      if (initiallyOpen) this.show();
    },
    show() {
      this.open = true;
      this.$nextTick(() => {
        const field = this.$refs.dialog?.querySelector(
          'input:not([type=hidden]):not([disabled]), select, textarea, button:not(.delete)');
        field?.focus();
      });
    },
    hide() {
      if (!this.open) return;
      this.open = false;
      this.$nextTick(() => this.$refs.trigger?.focus());
    },
  };
}
