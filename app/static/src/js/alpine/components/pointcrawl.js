import {generateResult, graphFromResult, nestedMapDraft, suggestedMapKind} from '../../content_generators.js';
import {emptyDrawing} from '../../maps/scene.js';

export default function pointcrawl() {
  return {
    graph:{nodes:[],edges:[]}, editing:false, creating:false, dirty:false, saving:false,
    status:'', selected:'', saveUrl:'', serial:0, canvasReady:false, generating:false, nestedKind:'dungeon',
    edgeSource:'', edgeTarget:'', kind:'dungeon', tables:null, labels:{}, locationId:'', draftBody:'',
    init() {
      this.graph=JSON.parse(this.$el.dataset.graph || '{"nodes":[],"edges":[]}');
      this.editing=this.$el.dataset.editing === 'true';
      this.saveUrl=this.$el.dataset.saveUrl;
      this.creating=this.$el.dataset.creating === 'true';
      this.labels=JSON.parse(this.$el.dataset.labels || '{}');
      this.$watch('graph', () => {this.dirty=true;this.syncCanvas();});
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
      this.onLeave = event => {if (this.editing && this.dirty) {event.preventDefault();event.returnValue='';}};
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
    },
    startCanvas() {
      this.onCanvasMessage = event => {
        if (event.source !== this.$refs.canvas.contentWindow || event.origin !== location.origin || event.data?.channel !== 'kw-map') return;
        const data=event.data;
        if (data.type === 'ready') this.syncCanvas();
        if (data.type === 'mounted') {this.canvasReady=true;clearTimeout(this.canvasTimer);this.status='';}
        if (data.type === 'select' && this.node(data.id) && this.selected!==String(data.id)) {
          this.selectionFromCanvas=true;this.selected=String(data.id);
        }
        if (data.type === 'change' && this.editing && !this.saving) {
          for (const move of data.moves || []) {
            const node=this.node(move.id);
            if (node) {node.x=move.x;node.y=move.y;}
          }
          this.graph.drawing=data.drawing;
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
        selected:this.selected,dark:document.body.classList.contains('dark-mode'),lang:this.$el.dataset.lang || 'en'});
    },
    node(id) {return this.graph.nodes.find(node => String(node.id)===String(id));},
    get selectedNode() {return this.node(this.selected);},
    newId(type) {return `new-${type}-${Date.now()}-${++this.serial}`;},
    isNew(item) {return String(item.id).startsWith('new-');},
    fit() {this.sendCanvas('fit');},
    addNode() {
      const number=Math.max(0,...this.graph.nodes.map(n=>Number(n.number)))+1;
      const node={id:this.newId('node'),number,title:`${this.labels.location} ${number}`,body:'',
        x:100+(number-1)%5*160,y:100+Math.floor((number-1)/5)*120,nested_map_id:null};
      if (this.locationId) {
        const option=this.$refs.locationPicker.selectedOptions[0];
        if (this.graph.nodes.some(n=>String(n.entry_id)===String(this.locationId))) {this.status=this.labels.duplicate;return;}
        node.entry_id=Number(this.locationId);node.title=option.textContent;
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
      this.graph=graphFromResult(result,Math.random,await this.loadTables());this.kind=result.mapKind;
      this.$refs.title.value=result.title;this.draftBody=this.graph.body;
      this.selected='';this.$nextTick(()=>this.fit());
    },
    async generate() {
      if (this.generating) return;
      this.generating=true;
      try {
        await this.loadTables();
        const subcategory={dungeon:'Dungeon',forest:'Forest',realm:'Realm'}[this.kind];
        await this.useResult(generateResult(this.tables,'Worldbuilding',subcategory));
        this.status='';
      } catch {this.status=this.labels.error;}
      finally {this.generating=false;}
    }
  };
}
