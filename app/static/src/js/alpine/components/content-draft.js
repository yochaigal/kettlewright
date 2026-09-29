import {generateArticle} from '../../content_generators.js';

export function contentDraft() {
  return {
    title:'', body:'', category:'custom', variant:'', formElement:null, tables:null,
    generating:false, generated:null, status:'',
    init() {
      this.formElement=this.$el;
      this.title=this.$el.elements.title.value;
      this.body=this.$el.elements.body.value;
      this.category=this.$el.elements.category?.value || 'custom';
      if(this.$el.dataset.import !== 'true' || !new URLSearchParams(location.search).has('from_tools') && !location.pathname.endsWith('/import'))return;
      try {
        const result=JSON.parse(sessionStorage.getItem('kw-content-result'));
        if(!result)return;
        this.title=result.title; this.body=result.body;this.category=result.category;
        this.$el.elements.title.value=this.title; this.$el.elements.body.value=this.body;
        if(this.$el.elements.category)this.$el.elements.category.value=this.category;
      } catch { /* Manual editing remains available. */ }
    },
    get variants() {
      return {bestiary:['Random Monster','Custom Monster'],item:['Gear','Armor','Weapons'],
        note:['Wilderness Events','Dungeon Events'],map:['Realm','Dungeon','Forest','Freeform']}[this.category] || [];
    },
    get freeform() {return this.category==='map' && this.variant==='Freeform';},
    openFreeform() {
      const params=new URLSearchParams({kind:'freeform'});
      for(const key of ['party_id','campaign_id']){const value=this.formElement.elements[key]?.value;if(value)params.set(key,value);}
      location.href='/maps/new?'+params;
    },
    async generate() {
      if(this.generating || this.category==='custom' || this.freeform)return;
      this.generating=true;this.status='';
      try {
        if(!this.tables){const response=await fetch('/articles/tables');if(!response.ok)throw new Error();this.tables=await response.json();}
        this.generated=generateArticle(this.tables,this.category,this.variant || this.variants[0]);
      }catch{this.status=this.$el.dataset.generateError;}finally{this.generating=false;}
    },
    useGenerated() {
      if(!this.generated)return;
      if(this.generated.mapKind){
        sessionStorage.setItem('kw-content-result',JSON.stringify(this.generated));
        const params=new URLSearchParams({from_tools:'1'});
        for(const key of ['party_id','campaign_id']){const value=this.formElement.elements[key]?.value;if(value)params.set(key,value);}
        location.href='/maps/new?'+params;return;
      }
      this.title=this.generated.title; this.body=this.generated.body;
      this.formElement.elements.title.value=this.title;
      this.formElement.elements.body.value=this.body;
      this.formElement.elements.body.dispatchEvent(new Event('input',{bubbles:true}));
      this.generated=null;
    }
  };
}
export function revealContent() {
  return {
    rows:[], original:{},
    init(){this.rows=JSON.parse(this.$el.dataset.rows);this.original=JSON.parse(this.$el.dataset.original);},
    copyOriginal(row){Object.assign(row,this.original);},
    copySelected(source){for(const row of this.rows)if(row.selected){row.title=source.title;row.body=source.body;row.path_type=source.path_type;}}
  };
}
