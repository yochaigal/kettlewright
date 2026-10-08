import {draftPreview, generateSettingArticle} from '../../setting_articles.js';
import {generateResult, graphFromResult, nestedMapDraft, suggestedMapKind} from '../../content_generators.js';
import {emptyDrawing} from '../../maps/scene.js';

export default function pointcrawl() {
  return {
    graph:{nodes:[],edges:[]}, editing:false, creating:false, dirty:false, saving:false, receivingCanvas:false,
    geographyDraft:null, geographyTables:null, geographyUrl:'', submitting:false, articleForm:null,
    waterBrushWidth:4,
    status:'', selectedEdge:'', selected:'', saveUrl:'', serial:0, canvasReady:false, generating:false, nestedKind:'dungeon',
    edgeSource:'', edgeTarget:'', kind:'dungeon', tables:null, labels:{}, locationId:'', draftBody:'', poiCount:'', generateChildren:true, forestChance:50, dungeonChance:25,
    init() {
      this.componentElement=this.$el;
      this.graph=JSON.parse(this.$el.dataset.graph || '{"nodes":[],"edges":[]}');
      this.kind=this.graph.kind || this.$el.dataset.kind || 'realm';
      this.editing=this.$el.dataset.editing === 'true';
      this.saveUrl=this.$el.dataset.saveUrl;
      this.geographyUrl=this.$el.dataset.geographyUrl;
      this.creating=this.$el.dataset.creating === 'true';
      this.labels=JSON.parse(this.$el.dataset.labels || '{}');
      this.$watch('graph', () => {this.dirty=true;if(!this.receivingCanvas)this.syncCanvas();});
      this.$watch('selected', () => {
        this.nestedKind=suggestedMapKind(this.selectedNode || {}) || 'dungeon';
        if (this.selectionFromCanvas) {this.selectionFromCanvas=false;return;}
        this.syncCanvas();
      });
      this.$nextTick(() => {this.startCanvas();this.dirty=false;});
      if (this.creating && new URLSearchParams(location.search).has('from_tools')) {
        try {
          const result=JSON.parse(sessionStorage.getItem('kw-content-result'));
          if (result?.mapKind) {
            this.generating=true;
            this.useResult(result).catch(()=>{this.status=this.labels.error;}).finally(()=>{this.generating=false;});
          }
        } catch {this.status=this.labels.error;}
      }
      this.onRefresh = event => {
        if (this.editing || !event.detail?.graph) return;
        this.graph=event.detail.graph;
        if (!this.node(this.selected)) this.selected='';
      };
      this.onAccessLost = () => {if (!this.editing) {
        this.graph={nodes:[],edges:[],drawing:emptyDrawing()};this.selected='';
        this.$refs.canvas.src='about:blank';this.canvasReady=false;
      }};
      this.articleForm=this.editing && !this.creating ? document.getElementById('article-form') : null;
      this.onArticleSubmit=event=>{
        if(this.saving || this.generating || this.dirty && !this.canvasReady || this.componentElement.querySelector('.rich-editor[data-pending="true"]')) {
          event.preventDefault();this.status=this.labels.error;return;
        }
        if(!event.defaultPrevented)this.submitting=true;
      };
      this.articleForm?.addEventListener('submit',this.onArticleSubmit);
      this.onLeave = event => {if (this.editing && this.dirty && !this.submitting) {event.preventDefault();event.returnValue='';}};
      window.addEventListener('campaign-refresh',this.onRefresh);
      window.addEventListener('campaign-access-lost',this.onAccessLost);
      window.addEventListener('beforeunload',this.onLeave);
    },
    destroy() {
      clearTimeout(this.canvasTimer);
      this.themeObserver?.disconnect();
      window.removeEventListener('message',this.onCanvasMessage);
      window.removeEventListener('campaign-refresh',this.onRefresh);
      window.removeEventListener('campaign-access-lost',this.onAccessLost);
      window.removeEventListener('beforeunload',this.onLeave);
      this.articleForm?.removeEventListener('submit',this.onArticleSubmit);
    },
    startCanvas() {
      this.onCanvasMessage = event => {
        if (event.source !== this.$refs.canvas.contentWindow || event.origin !== location.origin || event.data?.channel !== 'kw-map') return;
        const data=event.data;
        if (data.type === 'ready') this.syncCanvas();
        if (data.type === 'mounted') {this.canvasReady=true;clearTimeout(this.canvasTimer);this.status='';}
        if (data.type === 'select') {
          if(data.kind==='path' && this.graph.edges.some(edge=>String(edge.id)===String(data.id))) {
            this.selected='';this.selectedEdge=String(data.id);this.syncCanvas();
          } else if(this.node(data.id)) {this.selectedEdge='';this.selected=String(data.id);this.syncCanvas();}
          if(data.scroll !== false)this.$nextTick(()=>{
            const attribute=data.kind==='path'?'data-map-edge':'data-map-node';
            const row=[...this.$el.querySelectorAll(`[${attribute}]`)].find(row=>row.getAttribute(attribute)===String(data.id));
            row?.scrollIntoView({behavior:'smooth',block:'nearest'});
          });
        }
        if (data.type === 'change' && this.editing && !this.saving) {
          // Do not echo an in-progress stroke back to the iframe. A delayed
          // snapshot would replace the newer points still being drawn there.
          this.receivingCanvas=true;
          for (const move of data.moves || []) {
            const node=this.node(move.id);
            if (node) {node.x=move.x;node.y=move.y;if('geometry' in move)node.geometry=move.geometry;}
          }
          this.graph.drawing=data.drawing;
          this.$nextTick(()=>{this.receivingCanvas=false;});
        }
      };
      window.addEventListener('message',this.onCanvasMessage);
      this.themeObserver=new MutationObserver(()=>this.syncCanvas());
      this.themeObserver.observe(document.body,{attributes:true,attributeFilter:['class']});
      this.loadCanvas();
    },
    loadCanvas() {
      this.canvasReady=false;
      this.$refs.canvas.src=this.$refs.canvas.dataset.src;
      clearTimeout(this.canvasTimer);
      this.canvasTimer=setTimeout(()=>{if (!this.canvasReady) this.status=this.labels.loadError;},20000);
    },
    sendCanvas(type,detail={}) {
      this.$refs.canvas?.contentWindow?.postMessage({channel:'kw-map',type,...detail},location.origin);
    },
    syncCanvas() {
      this.sendCanvas('state',{graph:JSON.parse(JSON.stringify(this.graph)),editing:this.editing,
        selected:this.selected,selectedEdge:this.selectedEdge,dark:document.body.classList.contains('dark-mode'),
        lang:this.$el.dataset.lang || document.documentElement.lang || 'en',
        libraryError:this.$refs.canvas?.dataset.libraryError});
    },
    childrenPreview(){return draftPreview({body:'',children:this.graph.children || []});},
    node(id) {return this.graph.nodes.find(node => String(node.id)===String(id));},
    get selectedNode() {return this.node(this.selected);},
    get hasContents() {return Boolean(this.graph.has_contents || this.graph.nodes.length || this.graph.edges.length || this.graph.drawing?.elements?.length);},
    nodesForGroup(group) {
      const topography=['terrain','landmark','water','forest','weather','topography'];
      const pois=['settlement','waypoint','curiosity','lair','dungeon'];
      return this.graph.nodes.filter(node=>group==='topography'?topography.includes(node.category)
        :group==='pois'?pois.includes(node.category):!topography.includes(node.category) && !pois.includes(node.category));
    },
    waterBrush() {
      if(!this.canvasReady || this.selectedNode?.category!=='water')return;
      this.sendCanvas('water-brush',{width:Number(this.waterBrushWidth),nodeId:this.selected});
      this.$refs.canvas.scrollIntoView({block:'center'});
      this.$refs.canvas.focus({preventScroll:true});
    },
    selectTool() {
      this.sendCanvas('select-tool');this.$refs.canvas.scrollIntoView({block:'center'});
      this.$refs.canvas.focus({preventScroll:true});
    },
    resetGeometry() {if(this.selectedNode)this.selectedNode.geometry=null;},
    setNodeCoordinate(axis,value) {
      const node=this.selectedNode;if(!node || !Number.isFinite(value))return;
      if(node.geometry)node.geometry[axis]+=value-node[axis];
      node[axis]=value;
    },
    get showLocations() {return this.kind!=='freeform' || this.graph.nodes.length>0;},
    newId(type) {return `new-${type}-${Date.now()}-${++this.serial}`;},
    isNew(item) {return String(item.id).startsWith('new-');},
    fit() {this.sendCanvas('fit');this.$refs.canvas.focus({preventScroll:true});},
    addNode() {
      const number=Math.max(0,...this.graph.nodes.map(n=>Number(n.number)))+1;
      const node={id:this.newId('node'),number,title:`${this.labels.location} ${number}`,body:'',
        category:'custom',is_heart:false,x:100+(number-1)%5*160,y:100+Math.floor((number-1)/5)*120,nested_map_id:null};
      if (this.locationId) {
        const option=this.$refs.locationPicker.selectedOptions[0];
        if (this.graph.nodes.some(n=>String(n.entry_id)===String(this.locationId))) {this.status=this.labels.duplicate;return;}
        node.entry_id=Number(this.locationId);node.title=option.textContent;
        node.category=option.dataset.category || 'custom';
      }
      this.graph.nodes.push(node);this.selected=String(node.id);this.locationId='';
    },
    removeNode() {
      const id=this.selected;
      this.graph.edges=this.graph.edges.filter(e=>String(e.source)!==id && String(e.target)!==id);
      this.graph.nodes=this.graph.nodes.filter(n=>String(n.id)!==id);
      this.selected='';
    },
    addEdge() {
      if (!this.node(this.edgeSource) || !this.node(this.edgeTarget) || this.edgeSource===this.edgeTarget) return;
      if (this.graph.edges.some(e=>[String(e.source),String(e.target)].includes(this.edgeSource) &&
          [String(e.source),String(e.target)].includes(this.edgeTarget))) {this.status=this.labels.duplicate;return;}
      this.graph.edges.push({id:this.newId('edge'),source:this.edgeSource,target:this.edgeTarget,
        title:`${this.node(this.edgeSource).number} – ${this.node(this.edgeTarget).number}`,body:'',path_type:'standard'});
    },
    removeEdge(id) {this.graph.edges=this.graph.edges.filter(edge=>edge.id!==id);},
    async save() {
      if (this.saving || !this.canvasReady || this.generating) return;
      if (this.$el.querySelector('.rich-editor[data-pending="true"]')) return;
      this.saving=true;this.status='';
      const submitted=JSON.stringify(this.graph);
      try {
        const data=new FormData(this.$refs.saveForm);
        data.set('graph',submitted);
        const response=await fetch(this.saveUrl,{method:'POST',body:data});
        if (!response.ok || response.redirected) throw new Error(response.status===409 ? this.labels.conflict : this.labels.error);
        this.graph=await response.json();this.selected='';
        this.$nextTick(()=>{this.dirty=false;});this.status=this.labels.saved;
      } catch (error) {this.status=error.message || this.labels.error;}
      finally {this.saving=false;}
    },
    previewGeography(){return draftPreview({body:'',children:this.geographyDraft || []});},
    async prepareGeography() {
      if(this.hasContents || this.dirty || this.generating || this.saving)return;
      this.generating=true;this.status='';
      try {
        if(!this.geographyTables){
          const response=await fetch('/articles/tables');
          if(!response.ok)throw new Error(this.labels.error);
          this.geographyTables=await response.json();
        }
        const existing=new Set(this.graph.realm_sections || []);
        this.geographyDraft=['topography','pois'].filter(kind=>!existing.has(kind))
          .map(kind=>generateSettingArticle(this.geographyTables,kind));
        if(!existing.has('paths')) {
          const poiCount=this.geographyDraft.find(section=>section.category==='pois')?.children.length
            || this.graph.nodes.filter(node=>['settlement','waypoint','curiosity','lair','dungeon'].includes(node.category)).length || 3;
          this.geographyDraft.push(generateSettingArticle(this.geographyTables,'paths',Math.random,{poiCount}));
        }
      }catch(error){this.status=error.message || this.labels.error;}
      finally{this.generating=false;}
    },
    async applyGeography() {
      if(this.geographyDraft===null || this.dirty || this.saving)return;
      this.saving=true;this.status='';
      try {
        const data=new FormData(this.$refs.saveForm);
        data.set('version',this.graph.version);data.set('article_version',this.graph.article_version);
        data.set('children',JSON.stringify(this.geographyDraft));
        const response=await fetch(this.geographyUrl,{method:'POST',body:data});
        if(!response.ok || response.redirected)throw new Error(response.status===409?this.labels.conflict:this.labels.error);
        this.graph=await response.json();this.geographyDraft=null;this.selected='';
        this.$nextTick(()=>{this.dirty=false;this.fit();});this.status=this.labels.saved;
      }catch(error){this.status=error.message || this.labels.error;}
      finally{this.saving=false;}
    },
    async loadTables() {
      if (!this.tables) {
        const response=await fetch('/maps/tables');
        if (!response.ok) throw new Error(this.labels.error);
        this.tables=await response.json();
      }
      return this.tables;
    },
    async generateNested() {
      const node=this.selectedNode, kind=this.nestedKind;
      if (!node || node.nested_map_id || node.nested_draft || this.generating) return;
      this.generating=true;
      try {
        await this.loadTables();
        node.nested_draft=nestedMapDraft(node,kind,this.tables);
        this.status='';
      } catch {this.status=this.labels.error;}
      finally {this.generating=false;}
    },
    async useResult(result) {
      this.graph=graphFromResult(result,Math.random,await this.loadTables(),{generateChildren:result.generateChildren ?? this.generateChildren,forestChance:result.forestChance ?? this.forestChance,dungeonChance:result.dungeonChance ?? this.dungeonChance});this.kind=result.mapKind;
      this.$refs.title.value=result.title;this.draftBody=this.graph.body;
      this.selected='';this.$nextTick(()=>this.fit());
    },
    async generate() {
      if (this.generating || this.kind==='freeform') return;
      this.generating=true;
      try {
        await this.loadTables();
        const subcategory={dungeon:'Dungeon',forest:'Forest',realm:'Realm'}[this.kind];
        await this.useResult(generateResult(this.tables,'Worldbuilding',subcategory,Math.random,
          this.poiCount ? {poiCount:Number(this.poiCount)} : {}));
        this.status='';
      } catch {this.status=this.labels.error;}
      finally {this.generating=false;}
    }
  };
}
