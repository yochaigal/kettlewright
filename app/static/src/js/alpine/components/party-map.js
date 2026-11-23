// A party's map (#467): what it was shown, under its fog, with its pins.
// Members place pins (party notes with a position); the Warden also uncovers the fog.
// The drawing is the same map iframe (maps/editor.html) as the article pages, in view mode.
import {imageAspect} from '../../maps/viewport.js';
import {readCanvasUI, writeCanvasUI} from '../../maps/canvas_ui.js';

export default function partyMap() {
  return {
    graph: {nodes: [], edges: []}, pins: [], fog: null, fogVersion: 0, warden: false, labels: {},
    selected: '', selectedEdge: '', selectedPin: '', canvasReady: false, status: '',
    picking: false, draft: null, saving: false, fogTool: '', fogRadius: 60, preview: false,
    // Clean view (Discord feedback): the map's own controls, shown or hidden, as on every map.
    canvasUI: readCanvasUI('kw-map-ui'), isFullscreen: false,
    init() {
      const data = this.$el.dataset;
      this.graph = JSON.parse(data.graph);
      const state = JSON.parse(data.state);
      this.pins = state.pins; this.fog = state.fog; this.fogVersion = state.fog_version;
      this.warden = data.warden === 'true';
      this.labels = JSON.parse(data.labels || '{}');
      this.urls = {state: data.stateUrl, fog: data.fogUrl, pins: data.pinsUrl};
      this.csrf = data.csrf;
      this.onMessage = event => this.receive(event);
      window.addEventListener('message', this.onMessage);
      // An image map (#506): the frame takes the picture's shape, so the picture fills it.
      const aspect = this.graph.kind === 'image' ? imageAspect(this.graph.drawing) : null;
      this.$refs.canvas.classList.toggle('is-image-map', Boolean(aspect));
      if (aspect) this.$refs.canvas.style.aspectRatio = String(aspect);
      this.$refs.canvas.src = this.$refs.canvas.dataset.src;
      this.onFullscreen = () => {this.isFullscreen = Boolean(this.$refs.frame) && document.fullscreenElement === this.$refs.frame;};
      document.addEventListener('fullscreenchange', this.onFullscreen);
      // Players see new pins and newly uncovered fog without reloading.
      this.poll = setInterval(() => this.refresh(), 20000);
    },
    destroy() {
      window.removeEventListener('message', this.onMessage); clearInterval(this.poll);
      document.removeEventListener('fullscreenchange', this.onFullscreen);
    },
    send(type, detail = {}) {
      this.$refs.canvas.contentWindow?.postMessage({channel: 'kw-map', type, ...detail}, location.origin);
    },
    sync() {
      this.send('state', {graph: JSON.parse(JSON.stringify(this.graph)), editing: false, ui: {...this.canvasUI},
        selected: this.selected, selectedEdge: this.selectedEdge, selectedPin: this.selectedPin,
        pins: this.pins.map(({id, x, y, title, movable}) => ({id, x, y, title, movable})),
        fog: this.fog && JSON.parse(JSON.stringify(this.fog)), fogWarden: this.warden, dark: document.body.classList.contains('dark-mode'),
        lang: document.documentElement.lang || 'en'});
    },
    receive(event) {
      if (event.source !== this.$refs.canvas.contentWindow || event.origin !== location.origin || event.data?.channel !== 'kw-map') return;
      const data = event.data;
      if (data.type === 'ready') this.sync();
      if (data.type === 'mounted') this.canvasReady = true;
      if (data.type === 'select') {
        this.selectedPin = '';
        if (data.kind === 'path') {this.selected = ''; this.selectedEdge = String(data.id);}
        else {this.selectedEdge = ''; this.selected = String(data.id);}
        this.sync();
      }
      if (data.type === 'select-pin') {this.selected = ''; this.selectedEdge = ''; this.selectedPin = String(data.id); this.sync();}
      if (data.type === 'picked') {
        this.picking = false;
        if (document.fullscreenElement) document.exitFullscreen().catch(() => {});  // The pin dialog is on the page.
        this.draft = {x: data.x, y: data.y, title: '', body: ''};
        this.$nextTick(() => {this.$refs.pinDialog.showModal(); this.$refs.pinTitle?.focus();});
      }
      if (data.type === 'fog-operation') this.fogOperation(data.operation);
      if (data.type === 'move-pin') this.movePin(data);
    },
    toggleCanvasUI(group) {
      this.canvasUI = {...this.canvasUI, [group]: !this.canvasUI[group]};
      writeCanvasUI('kw-map-ui', this.canvasUI); this.sync();
    },
    // Full screen (#476): the map alone, filling the screen; Esc returns.
    // Full screen takes the map and its toolbar (Discord feedback), fog tools included; again to leave.
    fullscreen() {
      if (document.fullscreenElement) {document.exitFullscreen?.().catch(() => {}); return;}
      (this.$refs.frame || this.$refs.canvas).requestFullscreen?.().catch(() => {});
    },
    get selectedNode() {return this.graph.nodes.find(node => String(node.id) === this.selected);},
    get selectedPath() {return this.graph.edges.find(edge => String(edge.id) === this.selectedEdge);},
    get pin() {return this.pins.find(pin => String(pin.id) === this.selectedPin);},
    startPin() {this.picking = !this.picking; this.send('pick-point', {value: this.picking}); this.status = this.picking ? this.labels.pick : '';},
    form(fields) {
      const body = new FormData();
      body.set('csrf_token', this.csrf);
      for (const [key, value] of Object.entries(fields)) body.set(key, value);
      return body;
    },
    async post(url, fields) {
      const response = await fetch(url, {method: 'POST', body: this.form(fields), headers: {'Accept': 'application/json'}});
      const data = await response.json().catch(() => ({}));
      return {ok: response.ok, status: response.status, data};
    },
    apply(state) {
      this.pins = state.pins;
      if ('fog' in state) {this.fog = state.fog; this.fogVersion = state.fog_version;}
      if (this.selectedPin && !this.pin) this.selectedPin = '';
      this.sync();
    },
    async savePin() {
      if (!this.draft?.title.trim() || this.saving) return;
      this.saving = true;
      try {
        const result = await this.post(this.urls.pins, {x: this.draft.x, y: this.draft.y, title: this.draft.title, body: this.draft.body});
        if (!result.ok) throw new Error(result.status);
        this.$refs.pinDialog.close(); this.draft = null; this.status = this.labels.pinSaved;
        this.apply(result.data);
        this.selectedPin = String(this.pins.at(-1)?.id || ''); this.sync();
      } catch {this.status = this.labels.error;} finally {this.saving = false;}
    },
    // A pin dragged to a new place (#482): its maker or the Warden.
    async movePin({id, x, y}) {
      const result = await this.post(`${this.urls.pins}/${id}/move`, {x, y});
      if (result.ok) {this.status = this.labels.pinMoved || ''; this.apply(result.data);}
      else {this.status = this.labels.error; this.sync();}
    },
    // "1 pin", "3 pins" (#482).
    get pinCount() {return `${this.pins.length} ${this.pins.length === 1 ? this.labels.pinOne : this.labels.pinMany}`;},
    async deletePin(pin) {
      if (!confirm(this.labels.deletePin)) return;
      const result = await this.post(`${this.urls.pins}/${pin.id}/delete`, {});
      if (result.ok) {this.selectedPin = ''; this.apply(result.data);} else this.status = this.labels.error;
    },
    // Warden: fog tools and operations (the whiteboard's format, stored per party).
    setFogTool(tool) {this.fogTool = this.fogTool === tool ? '' : tool; this.send('fog-tool', {tool: this.fogTool, radius: Number(this.fogRadius)});},
    setRadius() {this.send('fog-tool', {tool: this.fogTool, radius: Number(this.fogRadius)});},
    togglePreview() {this.preview = !this.preview; this.send('fog-preview', {value: this.preview});},
    fogAction(type) {this.fogOperation({id: crypto.randomUUID(), type});},
    async fogOperation(operation) {
      const result = await this.post(this.urls.fog, {payload: JSON.stringify({operation, fog_version: this.fogVersion})});
      if (result.ok || result.status === 409) {
        this.fog = result.data.fog; this.fogVersion = result.data.fog_version; this.sync();
        if (result.status === 409) this.status = this.labels.fogChanged;
      } else this.status = this.labels.error;
    },
    async refresh() {
      if (this.saving || this.picking || document.hidden) return;
      try {
        const response = await fetch(this.urls.state, {headers: {'Accept': 'application/json'}});
        if (!response.ok) return;
        const state = await response.json();
        const changed = JSON.stringify(state) !== JSON.stringify({fog: this.fog, fog_version: this.fogVersion, pins: this.pins});
        if (changed) this.apply(state);
      } catch {/* Offline for a moment: try again on the next tick. */}
    },
  };
}
