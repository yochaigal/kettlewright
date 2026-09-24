import Alpine from 'https://cdn.jsdelivr.net/npm/alpinejs@3.17.4/dist/module.esm.js';
import itemEditor from './components/item-editor.js';
import collapseSection from './components/collapse-section.js';
import mobileMenu from './components/mobile-menu.js';

// Register every component before starting Alpine, including those in HTMX fragments.
Alpine.data('itemEditor', itemEditor);
Alpine.data('collapseSection', collapseSection);
Alpine.data('mobileMenu', mobileMenu);

window.Alpine = Alpine;
Alpine.start();
