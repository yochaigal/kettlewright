import {generateResult, graphFromResult} from '../../content_generators.js';

export default function pointcrawl() {
  return {
    graph:{nodes:[],edges:[]}, editing:false, creating:false, dirty:false, saving:false,
    status:'', selected:'', saveUrl:'', pan:{x:0,y:0}, scale:1, drag:null, serial:0,
    edgeSource:'', edgeTarget:'', kind:'dungeon', tables:null, labels:{}, locationId:'',
    init() {
      this.graph=JSON.parse(this.$el.dataset.graph || '{"nodes":[],"edges":[]}');
      this.editing=this.$el.dataset.editing === 'true';
      this.saveUrl=this.$el.dataset.saveUrl;
      this.creating=this.$el.dataset.creating === 'true';
      this.labels=JSON.parse(this.$el.dataset.labels || '{}');
      this.$watch('graph', () => {this.dirty=true;this.renderSvg();});
      this.$watch('selected', () => this.renderSvg());
      this.$nextTick(() => {this.fit();this.renderSvg();this.dirty=false;});
      if (this.creating && new URLSearchParams(location.search).has('from_tools')) {
        try {
          const result=JSON.parse(sessionStorage.getItem('kw-content-result'));
          if (result?.mapKind) this.useResult(result);
        } catch {this.status=this.labels.error;}
      }
      this.onRefresh = event => {
        if (this.editing || !event.detail?.graph) return;
        this.graph=event.detail.graph;
        if (!this.node(this.selected)) this.selected='';
      };
      this.onAccessLost = () => {if (!this.editing) {this.graph={nodes:[],edges:[]};this.selected='';}};
      this.onLeave = event => {if (this.editing && this.dirty) {event.preventDefault();event.returnValue='';}};
      window.addEventListener('campaign-refresh',this.onRefresh);
      window.addEventListener('campaign-access-lost',this.onAccessLost);
      window.addEventListener('beforeunload',this.onLeave);
    },
    destroy() {
      window.removeEventListener('campaign-refresh',this.onRefresh);
      window.removeEventListener('campaign-access-lost',this.onAccessLost);
      window.removeEventListener('beforeunload',this.onLeave);
    },
    renderSvg() {
      const drawing=this.$refs.canvas?.querySelector('[data-map-drawing]');
      if (!drawing) return;
      const make=(tag,attrs={},text=null) => {
        const element=document.createElementNS('http://www.w3.org/2000/svg',tag);
        for (const [key,value] of Object.entries(attrs)) element.setAttribute(key,String(value));
        if (text!==null) element.textContent=text;
        return element;
      };
      const fragment=document.createDocumentFragment();
      for (const edge of this.graph.edges) {
        const source=this.node(edge.source),target=this.node(edge.target);
        if (!source || !target) continue;
        const line=make('line',{x1:source.x,y1:source.y,x2:target.x,y2:target.y,
          class:edge.path_type==='hidden' ? 'hidden-path' : edge.path_type==='conditional' ? 'conditional-path' : ''});
        line.append(make('title',{},edge.title));fragment.append(line);
      }
      for (const item of this.graph.nodes) {
        const group=make('g',{'class':`map-node ${String(item.id)===this.selected ? 'selected' : ''}`,
          transform:`translate(${item.x} ${item.y})`,'data-node-id':item.id,
          tabindex:0,role:'button','aria-label':item.title});
        group.append(make('circle',{r:24}),
          make('text',{'text-anchor':'middle','dominant-baseline':'central'},item.number),
          make('text',{y:44,'text-anchor':'middle'},item.title.length>28 ? item.title.slice(0,28)+'…' : item.title));
        fragment.append(group);
      }
      drawing.replaceChildren(fragment);
    },
    selectFromEvent(event) {
      const element=event.target.closest('[data-node-id]');
      if (element) this.selected=element.dataset.nodeId;
    },
    node(id) {return this.graph.nodes.find(node => String(node.id)===String(id));},
    get selectedNode() {return this.node(this.selected);},
    get transform() {return `translate(${this.pan.x} ${this.pan.y}) scale(${this.scale})`;},
    newId(type) {return `new-${type}-${Date.now()}-${++this.serial}`;},
    isNew(item) {return String(item.id).startsWith('new-');},
    fit() {
      if (!this.graph.nodes.length) {this.pan={x:0,y:0};this.scale=1;return;}
      const xs=this.graph.nodes.map(n=>n.x), ys=this.graph.nodes.map(n=>n.y);
      const minX=Math.min(...xs)-90, minY=Math.min(...ys)-80;
      const width=Math.max(...xs)-minX+160, height=Math.max(...ys)-minY+100;
      this.scale=Math.min(1.8,900/width,500/height);
      this.pan={x:(1000-width*this.scale)/2-minX*this.scale,y:(600-height*this.scale)/2-minY*this.scale};
    },
    zoom(factor) {this.scale=Math.max(.1,Math.min(5,this.scale*factor));},
    point(event) {
      const point=new DOMPoint(event.clientX,event.clientY);
      return point.matrixTransform(this.$refs.canvas.getScreenCTM().inverse());
    },
    pointerDown(event) {
      if (event.button !== 0) return;
      const element=event.target.closest('[data-node-id]');
      const node=element ? this.node(element.dataset.nodeId) : null;
      if (node) this.selected=String(node.id);
      const p=this.point(event);
      this.drag={id:this.editing && node ? node.id:null, x:p.x,y:p.y,
        startX:node?.x,startY:node?.y,panX:this.pan.x,panY:this.pan.y};
      this.$refs.canvas.setPointerCapture(event.pointerId);
    },
    pointerMove(event) {
      if (!this.drag) return;
      const p=this.point(event), dx=p.x-this.drag.x,dy=p.y-this.drag.y;
      if (this.drag.id!==null) {
        const node=this.node(this.drag.id);
        node.x=Math.round(this.drag.startX+dx/this.scale);
        node.y=Math.round(this.drag.startY+dy/this.scale);
      } else this.pan={x:this.drag.panX+dx,y:this.drag.panY+dy};
    },
    addNode() {
      const number=Math.max(0,...this.graph.nodes.map(n=>Number(n.number)))+1;
      const node={id:this.newId('node'),number,title:`${this.labels.location} ${number}`,body:'',
        x:Math.round((500-this.pan.x)/this.scale),y:Math.round((300-this.pan.y)/this.scale),nested_map_id:null};
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
      if (this.saving) return;
      this.saving=true;this.status='';
      try {
        const data=new FormData(this.$refs.saveForm);
        data.set('graph',JSON.stringify(this.graph));
        const response=await fetch(this.saveUrl,{method:'POST',body:data});
        if (!response.ok || response.redirected) throw new Error(response.status===409 ? this.labels.conflict : this.labels.error);
        this.graph=await response.json();this.selected='';
        this.$nextTick(()=>{this.dirty=false;});this.status=this.labels.saved;
      } catch (error) {this.status=error.message || this.labels.error;}
      finally {this.saving=false;}
    },
    useResult(result) {
      this.graph=graphFromResult(result);this.kind=result.mapKind;
      this.$refs.title.value=result.title;this.$refs.body.value=this.graph.body;
      this.selected='';this.$nextTick(()=>this.fit());
    },
    async generate() {
      try {
        if (!this.tables) {
          const response=await fetch('/maps/tables');
          if (!response.ok) throw new Error(this.labels.error);
          this.tables=await response.json();
        }
        const subcategory={dungeon:'Dungeon',forest:'Forest',realm:'Realm'}[this.kind];
        this.useResult(generateResult(this.tables,'Worldbuilding',subcategory));
        this.status='';
      } catch {this.status=this.labels.error;}
    }
  };
}
