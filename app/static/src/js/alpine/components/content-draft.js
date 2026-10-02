import {parentTypes, draftPreview} from '../../setting_articles.js';
import {generateArticle} from '../../content_generators.js';

export function contentDraft() {
  return {
    title:'', body:'', category:'custom', variant:'', formElement:null, tables:null,
    categoryGroups:[], topCategory:'',
    generating:false, generated:null, status:'', children:[], generateChildren:true, forestChance:50, dungeonChance:25, isHeart:false,
    get canGenerateChildren(){return parentTypes.has(this.category);},
    preview(draft){return draftPreview(draft);},
    resetDraft(){this.variant='';this.generated=null;this.children=[];this.isHeart=false;},
    get subCategories(){return this.categoryGroups.find(group=>group.value===this.topCategory)?.choices || [];},
    syncTopCategory(){this.topCategory=this.categoryGroups.find(group=>group.choices.some(choice=>choice.value===this.category))?.value || '';},
    changeTopCategory(){this.category=this.subCategories[0]?.value || 'custom';this.resetDraft();},
    init() {
      this.formElement=this.$el;
      this.title=this.$el.elements.title.value;
      this.body=this.$el.elements.body.value;
      const picker=this.$el.querySelector('[data-category-groups]');
      this.categoryGroups=JSON.parse(picker?.dataset.categoryGroups || '[]');
      this.category=picker?.dataset.selectedCategory || this.$el.elements.category?.value || this.$el.dataset.category || 'custom';
      this.syncTopCategory();
      this.isHeart=this.$el.elements.is_heart?.checked || false;
      if(this.$el.dataset.import !== 'true' || !new URLSearchParams(location.search).has('from_tools') && !location.pathname.endsWith('/import'))return;
      try {
        const result=JSON.parse(sessionStorage.getItem('kw-content-result'));
        if(!result)return;
        this.title=result.title; this.body=result.body;this.category=result.category;this.children=result.children || [];
        this.syncTopCategory();
        this.$el.elements.title.value=this.title; this.$el.elements.body.value=this.body;
        if(this.$el.elements.category)this.$el.elements.category.value=this.category;
      } catch { /* Manual editing remains available. */ }
    },
    get variants() {
      return {terrain:['Random','Easy','Tough','Perilous','Forest'],bestiary:['Random Monster','Custom Monster'],item:['Gear','Armor','Weapons'],
        note:['Wilderness Events','Dungeon Events']}[this.category] || [];
    },
    async generate() {
      if(this.generating || this.category==='custom')return;
      this.generating=true;this.status='';
      try {
        if(!this.tables){const response=await fetch('/articles/tables');if(!response.ok)throw new Error();this.tables=await response.json();}
        this.generated=generateArticle(this.tables,this.category,this.variant || this.variants[0],Math.random,{generateChildren:this.generateChildren,forestChance:this.forestChance,dungeonChance:this.dungeonChance,isHeart:this.isHeart,terrainDifficulty:this.category==='terrain' && this.variant && this.variant!=='Random'?(this.variant==='Forest'?'Tough':this.variant):undefined,forestTerrain:this.category==='terrain' && this.variant==='Forest'});
      }catch{this.status=this.$el.dataset.generateError;}finally{this.generating=false;}
    },
    useGenerated() {
      if(!this.generated)return;
      if(this.generated.mapKind){
        this.generated.generateChildren=this.generateChildren;this.generated.forestChance=this.forestChance;this.generated.dungeonChance=this.dungeonChance;
        sessionStorage.setItem('kw-content-result',JSON.stringify(this.generated));
        const params=new URLSearchParams({from_tools:'1'});
        for(const key of ['party_id','campaign_id']){const value=this.formElement.elements[key]?.value;if(value)params.set(key,value);}
        location.href='/materials/generate?'+params;return;
      }
      this.title=this.generated.title; this.body=this.generated.body;
      this.children=this.generated.children || [];this.isHeart=this.generated.is_heart || false;
      if(this.formElement.elements.path_type)this.formElement.elements.path_type.value=this.generated.path_type || 'standard';
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
