export default function mobileMenu() {
  return {
    menuOpen: false,
    toggle() {
      this.menuOpen = !this.menuOpen;
    },
  };
}
