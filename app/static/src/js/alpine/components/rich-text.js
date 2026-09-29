import {MAX_CONTENT, markdownSource} from '../../rich-content.js';
import {formatMarkdown} from '../../markdown-editing.js';

export default function richText() {
  let form, onSubmit;
  return {
    value:'', previewing:false,
    get tooLong() {return new TextEncoder().encode(this.value).length>MAX_CONTENT || this.value.replace(/data:image\/[^\s)]+/g,'').length>50000;},
    init() {
      this.value=markdownSource(this.$refs.source.value);
      this.$refs.source.value=this.value;
      this.$watch('value',value=>{const source=markdownSource(value); if (value!==source) this.value=source; this.$refs.source.value=source;});
      form=this.$el.closest('form');
      onSubmit=event=>{if(this.tooLong){event.preventDefault();event.stopImmediatePropagation();}};
      form?.addEventListener('submit',onSubmit,true);
    },
    format(action) {this.previewing=false; this.$nextTick(()=>formatMarkdown(this.$refs.source,action));},
    destroy(){form?.removeEventListener('submit',onSubmit,true);}
  };
}
