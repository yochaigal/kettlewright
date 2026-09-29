import Alpine from 'https://cdn.jsdelivr.net/npm/alpinejs@3.17.4/dist/module.esm.js';
import itemEditor from './components/item-editor.js';
import collapseSection from './components/collapse-section.js';
import pointcrawl from './components/pointcrawl.js';
import {contentDraft, revealContent} from './components/content-draft.js';
import mobileMenu from './components/mobile-menu.js';
import richText from './components/rich-text.js';
import {richContentHTML, inlineContentHTML} from '../rich-content.js';

// Register every component before starting Alpine, including those in HTMX fragments.
Alpine.data('itemEditor', itemEditor);
Alpine.data('collapseSection', collapseSection);
Alpine.data('mobileMenu', mobileMenu);
Alpine.data('pointcrawl', pointcrawl);
Alpine.data('contentDraft', contentDraft);
Alpine.data('revealContent', revealContent);
Alpine.data('richText', richText);
Alpine.magic('richHTML', () => richContentHTML);
Alpine.magic('markdownInline', () => inlineContentHTML);

window.Alpine = Alpine;
Alpine.start();
