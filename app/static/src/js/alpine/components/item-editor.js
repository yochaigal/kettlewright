import {armorTags, itemTagGroups, itemTags} from '#kettlewright';

// The game system's item vocabulary (kettlewright): an item has at most one tag of each group.

export default function itemEditor() {
  return {
    tags: [],
    extraTags: [],
    name: '',
    description: '',
    uses: '',
    charges: '',
    maxCharges: '',
    armorActive: false,

    init() {
      const fields = this.$el.elements;
      this.tags = JSON.parse(this.$el.dataset.itemTags);
      this.extraTags = JSON.parse(this.$el.querySelector('#item-extra-tags').dataset.labels);
      this.name = fields.edit_item_name.value;
      this.description = fields.edit_item_description.value;
      this.uses = fields.edit_item_uses.value;
      this.charges = fields.edit_item_charges.value;
      this.maxCharges = fields.edit_item_max_charges.value;
      this.armorActive = this.hasArmor && fields.edit_item_armor_active.checked;
    },

    get hasArmor() {
      return this.tags.some(tag => armorTags().includes(tag));
    },

    toggleTag(tag) {
      if (this.tags.includes(tag)) {
        this.tags = this.tags.filter(value => value !== tag);
      } else {
        const group = itemTagGroups().find(values => values.includes(tag)) || [];
        this.tags = [...this.tags.filter(value => !group.includes(value)), tag];
      }
      if (!this.hasArmor) this.armorActive = false;
    },

    selectLibraryItem(value, options) {
      const option = Array.from(options).find(option =>
        option.value.toLocaleLowerCase() === value.toLocaleLowerCase());
      if (!option) return;
      const item = JSON.parse(option.dataset.item);
      this.name = option.value;
      this.description = item.description;
      this.uses = item.uses;
      this.charges = item.charges;
      this.maxCharges = item.max_charges;
      this.tags = [...item.tags];
      this.extraTags = this.tags.filter(tag => !itemTags().includes(tag))
        .map(tag => ({ value: tag, label: tag }));
      this.armorActive = this.hasArmor;
    },
  };
}
