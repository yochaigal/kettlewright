// An article's own image (#476): pick a picture, see it, or remove it. The form sends it as `image`.
// Big photos are shrunk here (to 1600 px, WebP) so they fit the 2 MB upload limit; the server stores them.
const MAX_SIDE = 1600;
const MAX_FILE = 10 * 1024 * 1024;

export function shrinkSize(width, height, max = MAX_SIDE) {
  const scale = Math.min(1, max / Math.max(width, height));
  return {width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale))};
}

export default function articleImage() {
  return {
    value: '', preview: '', error: '',
    init() {
      this.value = this.$el.dataset.value || '';
      this.preview = this.$el.dataset.preview || '';
    },
    async pick(event) {
      const file = event.target.files?.[0];
      event.target.value = '';
      this.error = '';
      if (!file) return;
      if (file.size > MAX_FILE) {this.error = this.$el.dataset.tooBig; return;}
      const bitmap = await createImageBitmap(file);
      const size = shrinkSize(bitmap.width, bitmap.height);
      const canvas = document.createElement('canvas');
      canvas.width = size.width; canvas.height = size.height;
      canvas.getContext('2d').drawImage(bitmap, 0, 0, size.width, size.height);
      bitmap.close?.();
      this.value = this.preview = canvas.toDataURL('image/webp', 0.85);
    },
    clear() {this.value = ''; this.preview = ''; this.error = '';},
  };
}
