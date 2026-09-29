import {MAX_CONTENT, remoteImageURL, markdownSource} from '../../rich-content.js';
import {formatMarkdown} from '../../markdown-editing.js';
import {optimizeUpload} from '../../image-upload.js';

export default function richText() {
  let form, onSubmit, disposed=false, imageIndex;
  return {
    value:'', previewing:false, imagePanel:false, imageLink:'', imageError:'', uploading:false,
    get tooLong() {return new TextEncoder().encode(this.value).length>MAX_CONTENT || this.value.replace(/data:image\/[^\s)]+/g,'').length>50000;},
    init() {
      this.value=markdownSource(this.$refs.source.value);
      this.$refs.source.value=this.value;
      this.$watch('value',value=>{const source=markdownSource(value); if (value!==source) this.value=source; this.$refs.source.value=source;});
      form=this.$el.closest('form');
      onSubmit=event=>{if(this.uploading || this.tooLong){event.preventDefault();event.stopImmediatePropagation();}};
      form?.addEventListener('submit',onSubmit,true);
    },
    format(action) {this.previewing=false; this.$nextTick(()=>formatMarkdown(this.$refs.source,action));},
    openImages() {imageIndex=this.$refs.source.selectionStart; this.imagePanel=!this.imagePanel;},
    paste(event) {if(event.clipboardData.files.length){event.preventDefault();this.insertImages(event.clipboardData.files);}},
    drop(event) {if(event.dataTransfer.files.length){event.preventDefault();this.insertImages(event.dataTransfer.files);}},
    insertImage(url) {
      if(this.value.length+url.length>MAX_CONTENT) throw new Error('Too large');
      const field=this.$refs.source, position=imageIndex ?? field.selectionStart;
      const image=`![Image](${url})`;
      field.setRangeText(image,position,position,'end');
      field.dispatchEvent(new Event('input',{bubbles:true}));
      imageIndex=position+image.length;
    },
    insertLink() {
      const url=this.imageLink.trim(); this.imageError='';
      if(!remoteImageURL(url)){this.imageError=this.$el.dataset.urlError;return;}
      try{this.insertImage(url);this.imagePanel=false;this.imageLink='';this.previewing=true;imageIndex=undefined;}
      catch{this.imageError=this.$el.dataset.imageError;}
    },
    async insertImages(files) {
      if(this.uploading)return;
      this.uploading=true; this.imageError=''; imageIndex ??= this.$refs.source.selectionStart;
      try{for(const file of files){const url=await optimizeUpload(file);if(disposed)return;this.insertImage(url);} this.imagePanel=false;this.previewing=true;}
      catch{this.imageError=this.$el.dataset.imageError;}
      finally{this.uploading=false;this.$refs.file.value='';imageIndex=undefined;}
    },
    destroy(){disposed=true;form?.removeEventListener('submit',onSubmit,true);}
  };
}
