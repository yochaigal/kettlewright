import {MAX_CONTENT, markdownSource} from '../../rich-content.js';
import {formatMarkdown} from '../../markdown-editing.js';
import {setupLinkCompletion} from '../../article-links.js';

export default function richText() {
  let form, onSubmit, cleanupLinks, context, sequence=0;
  return {
    value:'', previewing:false, previewHTML:'',
    get tooLong() {return new TextEncoder().encode(this.value).length>MAX_CONTENT || this.value.replace(/data:image\/[^\s)]+/g,'').length>50000;},
    init() {
      this.value=markdownSource(this.$refs.source.value);
      this.$refs.source.value=this.value;
      this.$watch('value',value=>{const source=markdownSource(value); if (value!==source) this.value=source; this.$refs.source.value=source;});
      form=this.$el.closest('form');
      onSubmit=event=>{if(this.tooLong){event.preventDefault();event.stopImmediatePropagation();}};
      form?.addEventListener('submit',onSubmit,true);
      const host=this.$el.closest('[data-reference-context]');
      if(host){
        context=JSON.parse(host.dataset.referenceContext);
        context.campaign_id=()=>form?.elements.campaign_id?.value ?? JSON.parse(host.dataset.referenceContext).campaign_id ?? '';
        cleanupLinks=setupLinkCompletion(this.$refs.source,context);
      }
      this.$watch('previewing',shown=>{if(shown)this.loadPreview();});
      this.$watch('value',()=>{if(this.previewing)this.loadPreview();});
      if(location.hash.startsWith('#kw-h-'))this.previewing=true;
    },
    async loadPreview(){
      const ticket=++sequence;
      this.previewHTML=this.$richHTML(this.value);
      if(!context)return;
      const data=new FormData();data.set('body',this.value);data.set('campaign_id',context.campaign_id());
      data.set('entry_id',this.$el.dataset.referenceEntryId || context.entry_id || '');
      const csrf=form?.querySelector('[name=csrf_token]');if(csrf)data.set('csrf_token',csrf.value);
      try{const response=await fetch(context.preview_url,{method:'POST',body:data,cache:'no-store'});
        if(response.ok){const result=await response.json();if(ticket===sequence){this.previewHTML=result.html;
          if(location.hash.startsWith('#kw-h-'))this.$nextTick(()=>this.$el.querySelector('#'+CSS.escape(decodeURIComponent(location.hash.slice(1))))?.scrollIntoView({block:'start'}));}}
      }catch{/* Local Markdown stays available while offline. */}
    },
    format(action) {this.previewing=false; this.$nextTick(()=>formatMarkdown(this.$refs.source,action));},
    destroy(){++sequence;cleanupLinks?.();form?.removeEventListener('submit',onSubmit,true);}
  };
}
