import {RICH_PREFIX, MAX_CONTENT, imageURL, remoteImageURL, richContentHTML} from '../../rich-content.js';

import {optimizeUpload} from '../../image-upload.js';

let loading;
function loadQuill() {
  if (window.Quill) return Promise.resolve(window.Quill);
  if (!loading) loading = new Promise((resolve,reject) => {
    const script = document.createElement('script');
    const timeout = setTimeout(() => fail(),20000);
    function fail() {clearTimeout(timeout); script.remove(); loading=null; reject(new Error('Editor unavailable'));}
    script.src='https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.js';
    script.onload=()=>{clearTimeout(timeout); resolve(window.Quill);};
    script.onerror=fail;
    document.head.append(script);
  });
  return loading;
}

export default function richText() {
  // Keep the editor instance outside Alpine's reactive proxy.
  let editor, lastValue, change, paste, drop, onSubmit, form, disposed=false, imageIndex;
  return {
    imagePanel:false, imageLink:'', value:'', ready:false, failed:false, imageError:'', uploading:false, textLength:0, maxContent:MAX_CONTENT, richContentHTML,
    get isRich() {return this.value.startsWith(RICH_PREFIX);},
    get tooLong() {return this.value.length > MAX_CONTENT || this.textLength > 50000;},
    init() {
      this.value=this.$refs.source.value;
      form=this.$el.closest('form');
      onSubmit=event=>{
        if (this.uploading || this.tooLong) {
          event.preventDefault(); event.stopImmediatePropagation(); editor?.focus();
        }
      };
      form?.addEventListener('submit',onSubmit,true);
      this.$watch('value', value => {
        this.$refs.source.value=value;
        if (!editor || value===lastValue) return;
        lastValue=value;
        if (value.startsWith(RICH_PREFIX)) editor.setContents(editor.clipboard.convert({html:richContentHTML(value)}),'silent');
        else editor.setText(value,'silent');
        this.textLength=editor.getText().length-1;
        editor.history.clear();
      });
      this.$nextTick(()=>this.start());
    },
    async start() {
      this.failed=false;
      try {
        const Quill = await loadQuill();
        if (disposed || editor) return;
        const ImageBlot=Quill.import('formats/image');
        ImageBlot.sanitize=value=>imageURL(value) ? value : '';
        editor=new Quill(this.$refs.host.firstElementChild, {
          theme:'snow', formats:['bold','italic','underline','strike','header','list','blockquote','link','image'],
          modules:{toolbar:[[{header:[2,3,false]}],['bold','italic','underline','strike'],
            [{list:'ordered'},{list:'bullet'}],['blockquote','link','image'],['clean']], history:{userOnly:true}}
        });
        editor.root.setAttribute('role','textbox');
        editor.root.setAttribute('aria-multiline','true');
        editor.root.setAttribute('aria-label',this.$el.dataset.label);
        const toolbar=editor.getModule('toolbar').container;
        editor.getModule('toolbar').addHandler('image',()=>{imageIndex=editor.getSelection(true)?.index; this.imagePanel=!this.imagePanel; this.imageError='';});
        toolbar.setAttribute('role','toolbar');
        toolbar.setAttribute('aria-label',this.$el.dataset.label);
        const labels=JSON.parse(this.$el.dataset.toolbar);
        for (const button of toolbar.querySelectorAll('button')) {
          const format=button.className.replace('ql-','');
          const label=labels[button.value || format] || format;
          button.setAttribute('aria-label',label); button.title=label;
        }
        lastValue=this.value;
        if (this.isRich) editor.setContents(editor.clipboard.convert({html:richContentHTML(this.value)}),'silent');
        else editor.setText(this.value,'silent');
        this.textLength=editor.getText().length-1;
        editor.history.clear();
        change=()=>{
          lastValue=editor.getLength() <= 1 ? '' : RICH_PREFIX+editor.getSemanticHTML();
          this.value=lastValue;
          this.textLength=editor.getText().length-1;
          // Update native forms immediately, including submit without losing focus.
          this.$refs.source.value=lastValue;
          this.$refs.source.dispatchEvent(new Event('input',{bubbles:true}));
        };
        editor.on('text-change',change);
        paste=event=>{
          const files=[...event.clipboardData.files];
          if (files.length) {event.preventDefault(); event.stopImmediatePropagation(); this.insertImages(files);}
        };
        drop=event=>{
          const files=[...event.dataTransfer.files];
          if (files.length) {event.preventDefault(); event.stopImmediatePropagation(); this.insertImages(files);}
        };
        editor.root.addEventListener('paste',paste,true);
        editor.root.addEventListener('drop',drop,true);
        this.ready=true;
      } catch {if (!disposed) this.failed=true;}
    },
    insertImage(url) {
      if (this.value.length+url.length > MAX_CONTENT) throw new Error();
      const index=Math.min(imageIndex ?? editor.getSelection(true)?.index ?? editor.getLength()-1,editor.getLength()-1);
      editor.insertEmbed(index,'image',url,'user');
      editor.setSelection(index+1,0,'silent');
      imageIndex=index+1;
    },
    insertLink() {
      const url=this.imageLink.trim();
      this.imageError='';
      if (!remoteImageURL(url)) {this.imageError=this.$el.dataset.urlError; return;}
      try {this.insertImage(url); this.imagePanel=false; this.imageLink=''; imageIndex=undefined;}
      catch {this.imageError=this.$el.dataset.imageError;}
    },
    async insertImages(files) {
      if (this.uploading || !editor) return;
      this.imageError=''; this.uploading=true;
      try {
        // Capture the caret before decoding, since the user can move focus meanwhile.
        imageIndex=editor.getSelection()?.index ?? imageIndex ?? editor.getLength()-1;
        for (const file of files) {
          const url=await optimizeUpload(file);
          if (disposed) return;
          this.insertImage(url);
        }
        this.imagePanel=false;
      } catch {this.imageError=this.$el.dataset.imageError;}
      finally {this.uploading=false; this.$refs.file.value=''; imageIndex=undefined;}
    },
    destroy() {disposed=true; form?.removeEventListener('submit',onSubmit,true); if (editor) {editor.off('text-change',change); editor.root.removeEventListener('paste',paste,true); editor.root.removeEventListener('drop',drop,true); editor.disable();}}
  };
}
