// Grid dungeons for the whiteboard (#439): paint floor squares, and walls follow
// the edge of the floor, as with a wet-erase marker on a battle mat.
//
// A dungeon is a set of floor squares plus edge overrides (doors, openings and
// inner walls). It is saved as ordinary Excalidraw shapes; their IDs encode the
// geometry, so the dungeon is read back from the board and needs no extra data.
// This module has no imports so it can be tested directly.

export const DEFAULT_SIZE = 80; // one token
export const STYLE = {floor: '#e6e6e6', wall: '#1e1e1e', door: '#9a9a9a', floorOpacity: 85};
const TENTHS = 10;
const DOOR_GAP = [3, 7]; // the door takes the middle of its edge, in tenths

const cellKey = (c, r) => `${c},${r}`;
const parseCell = key => key.split(',').map(Number);
export const emptyDungeon = (size = DEFAULT_SIZE) => ({size, cells: new Set(), edges: new Map()});

// Squares and edges --------------------------------------------------------
// h:c:r is the top edge of square (c, r); v:c:r is its left edge.

export const cellAt = (x, y, size) => [Math.floor(x / size), Math.floor(y / size)];

export function edgeSides(edge) {
  const [kind, c, r] = parseEdge(edge);
  return kind === 'h' ? [[c, r - 1], [c, r]] : [[c - 1, r], [c, r]];
}
function parseEdge(edge) {
  const [kind, c, r] = edge.split(':');
  return [kind, Number(c), Number(r)];
}
const cellEdges = (c, r) => [`h:${c}:${r}`, `h:${c}:${r + 1}`, `v:${c}:${r}`, `v:${c + 1}:${r}`];

// The edge nearest to a point, as the Doors tool picks it.
export function edgeAt(x, y, size) {
  const c = Math.floor(x / size), r = Math.floor(y / size);
  const fx = x / size - c, fy = y / size - r;
  const nearest = Math.min(fx, 1 - fx, fy, 1 - fy);
  if (nearest === fx) return `v:${c}:${r}`;
  if (nearest === 1 - fx) return `v:${c + 1}:${r}`;
  if (nearest === fy) return `h:${c}:${r}`;
  return `h:${c}:${r + 1}`;
}

// Every square a drag passes over, so a fast stroke leaves no gaps.
export function cellsAlong(from, to, size) {
  const cells = new Set();
  const steps = Math.max(1, Math.ceil(Math.hypot(to[0] - from[0], to[1] - from[1]) / (size / 4)));
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    cells.add(cellKey(...cellAt(from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t, size)));
  }
  return cells;
}

// Squares inside a box; used by tests to build rooms.
export function cellsInBox(from, to, size) {
  const [c1, r1] = cellAt(...from, size), [c2, r2] = cellAt(...to, size);
  const cells = new Set();
  for (let c = Math.min(c1, c2); c <= Math.max(c1, c2); c++)
    for (let r = Math.min(r1, r2); r <= Math.max(r1, r2); r++) cells.add(cellKey(c, r));
  return cells;
}

// Edge kinds ---------------------------------------------------------------
// Between floor and empty space an edge is a wall unless it is a door or an
// opening. Between two floor squares it is open unless it is a wall or a door.

function floorSides(dungeon, edge) {
  return edgeSides(edge).filter(([c, r]) => dungeon.cells.has(cellKey(c, r))).length;
}

export function edgeKind(dungeon, edge) {
  const sides = floorSides(dungeon, edge);
  if (!sides) return null;
  const override = dungeon.edges.get(edge);
  if (sides === 1) return override === 'door' || override === 'open' ? override : 'wall';
  return override === 'wall' || override === 'door' ? override : 'open';
}

// Drop overrides that no longer mean anything, e.g. after erasing.
function tidy(dungeon) {
  for (const [edge, kind] of dungeon.edges) {
    const sides = floorSides(dungeon, edge);
    if (!sides || (sides === 1 && kind === 'wall') || (sides === 2 && kind === 'open')) dungeon.edges.delete(edge);
  }
  return dungeon;
}

const copy = dungeon => ({size: dungeon.size, cells: new Set(dungeon.cells), edges: new Map(dungeon.edges)});

export function paint(dungeon, cells, erase = false) {
  const next = copy(dungeon);
  for (const cell of cells) erase ? next.cells.delete(cell) : next.cells.add(cell);
  return tidy(next);
}

// Doors tool: outer walls go wall → door → opening; inner edges go open → wall → door.
export function cycleEdge(dungeon, edge) {
  const kind = edgeKind(dungeon, edge);
  if (!kind) return dungeon;
  const outer = floorSides(dungeon, edge) === 1;
  const order = outer ? ['wall', 'door', 'open'] : ['open', 'wall', 'door'];
  const next = copy(dungeon);
  next.edges.set(edge, order[(order.indexOf(kind) + 1) % order.length]);
  return tidy(next);
}

// Shapes -------------------------------------------------------------------

const prefix = size => `dungeon-${size}-`;
const base = {roughness: 0, locked: true, angle: 0, strokeStyle: 'solid', roundness: null};

// Floor squares merged into rectangles: runs along each row, then equal runs
// on consecutive rows. Keeps a large dungeon well under the board's 2000 shapes.
export function floorRectangles(cells) {
  const rows = new Map();
  for (const key of cells) {
    const [c, r] = parseCell(key);
    if (!rows.has(r)) rows.set(r, []);
    rows.get(r).push(c);
  }
  const open = new Map(), rects = [];
  for (const r of [...rows.keys()].sort((a, b) => a - b)) {
    const columns = rows.get(r).sort((a, b) => a - b), runs = [];
    for (const c of columns) {
      const last = runs.at(-1);
      if (last && last[1] === c - 1) last[1] = c; else runs.push([c, c]);
    }
    const next = new Map();
    for (const [c1, c2] of runs) {
      const key = `${c1}:${c2}`, rect = open.get(key);
      if (rect && rect.r + rect.h === r) {rect.h += 1; next.set(key, rect);}
      else {const fresh = {c: c1, r, w: c2 - c1 + 1, h: 1}; rects.push(fresh); next.set(key, fresh);}
    }
    open.clear();
    for (const [key, rect] of next) open.set(key, rect);
  }
  return rects;
}

// Wall pieces along each grid line, in tenths of a square, merged where they touch.
function wallRuns(dungeon) {
  const lines = new Map();
  const add = (kind, line, from, to) => {
    const key = `${kind}:${line}`;
    if (!lines.has(key)) lines.set(key, []);
    lines.get(key).push([from, to]);
  };
  const doors = [];
  const edges = new Set();
  for (const key of dungeon.cells) for (const edge of cellEdges(...parseCell(key))) edges.add(edge);
  for (const edge of [...dungeon.edges.keys()]) edges.add(edge);
  for (const edge of edges) {
    const kind = edgeKind(dungeon, edge);
    if (kind !== 'wall' && kind !== 'door') continue;
    const [orientation, c, r] = parseEdge(edge);
    const [line, start] = orientation === 'h' ? [r, c] : [c, r];
    if (kind === 'wall') add(orientation, line, start * TENTHS, (start + 1) * TENTHS);
    else {
      add(orientation, line, start * TENTHS, start * TENTHS + DOOR_GAP[0]);
      add(orientation, line, start * TENTHS + DOOR_GAP[1], (start + 1) * TENTHS);
      doors.push(edge);
    }
  }
  const runs = [];
  for (const [key, pieces] of lines) {
    const [orientation, line] = key.split(':');
    pieces.sort((a, b) => a[0] - b[0]);
    const merged = [];
    for (const piece of pieces) {
      const last = merged.at(-1);
      if (last && piece[0] <= last[1]) last[1] = Math.max(last[1], piece[1]); else merged.push([...piece]);
    }
    for (const [from, to] of merged) runs.push({orientation, line: Number(line), from, to});
  }
  return {runs, doors};
}

// Excalidraw element skeletons for the whole dungeon, floor first.
export function dungeonShapes(dungeon, style = STYLE) {
  const s = dungeon.size, id = prefix(s), wallWidth = Math.max(3, Math.round(s / 10));
  const floors = floorRectangles(dungeon.cells).map(({c, r, w, h}) => ({...base, type: 'rectangle',
    id: `${id}floor-${c}_${r}_${w}_${h}`, x: c * s, y: r * s, width: w * s, height: h * s,
    backgroundColor: style.floor, strokeColor: style.floor, fillStyle: 'solid', strokeWidth: 1,
    opacity: style.floorOpacity}));
  const {runs, doors} = wallRuns(dungeon);
  const walls = runs.map(({orientation, line, from, to}) => {
    const length = (to - from) / TENTHS * s;
    const [x, y] = orientation === 'h' ? [from / TENTHS * s, line * s] : [line * s, from / TENTHS * s];
    return {...base, type: 'line', id: `${id}wall-${orientation}-${line}_${from}_${to}`, x, y,
      width: orientation === 'h' ? length : 0, height: orientation === 'h' ? 0 : length,
      points: orientation === 'h' ? [[0, 0], [length, 0]] : [[0, 0], [0, length]],
      strokeColor: style.wall, backgroundColor: 'transparent', strokeWidth: wallWidth, opacity: 100};
  });
  const doorShapes = doors.map(edge => {
    const [orientation, c, r] = parseEdge(edge);
    const along = (DOOR_GAP[1] - DOOR_GAP[0]) / TENTHS * s, across = Math.max(6, Math.round(s * .16));
    const start = (orientation === 'h' ? c : r) * s + DOOR_GAP[0] / TENTHS * s;
    const line = (orientation === 'h' ? r : c) * s - across / 2;
    return {...base, type: 'rectangle', id: `${id}door-${orientation}-${c}_${r}`,
      x: orientation === 'h' ? start : line, y: orientation === 'h' ? line : start,
      width: orientation === 'h' ? along : across, height: orientation === 'h' ? across : along,
      backgroundColor: style.door, strokeColor: style.wall, fillStyle: 'solid', strokeWidth: 2, opacity: 100};
  });
  return [...floors, ...walls, ...doorShapes];
}

// Reading a dungeon back from the board ------------------------------------

// IDs look like dungeon-80-floor-3_-2_4_1 or dungeon-80-wall-h-5_30_70.
const PATTERN = /^dungeon-(\d+)-(floor|wall-h|wall-v|door-h|door-v)-(-?\d+(?:_-?\d+)*)$/;
export function dungeonPart(id) {
  const match = PATTERN.exec(id || '');
  return match ? {size: Number(match[1]), part: match[2], rest: match[3].split('_').map(Number)} : null;
}
export const isDungeonShape = element => Boolean(dungeonPart(element.id));

// The board's dungeon size, or null when it has none.
export function boardSize(elements) {
  const part = elements.map(element => !element.isDeleted && dungeonPart(element.id)).find(Boolean);
  return part ? part.size : null;
}

export function dungeonFromShapes(elements, size) {
  const dungeon = emptyDungeon(size);
  const walls = new Set(), doors = new Set();
  for (const element of elements) {
    const part = !element.isDeleted && dungeonPart(element.id);
    if (!part || part.size !== size || part.rest.some(Number.isNaN)) continue;
    const [kind, orientation] = part.part.split('-');
    if (kind === 'floor' && part.rest.length === 4) {
      const [c, r, w, h] = part.rest;
      if (w > 0 && h > 0 && w * h <= 100000)
        for (let i = 0; i < w; i++) for (let j = 0; j < h; j++) dungeon.cells.add(cellKey(c + i, r + j));
    } else if (kind === 'door' && part.rest.length === 2) {
      doors.add(`${orientation}:${part.rest[0]}:${part.rest[1]}`);
    } else if (kind === 'wall' && part.rest.length === 3) {
      const [line, from, to] = part.rest;
      for (let start = Math.ceil(from / TENTHS); (start + 1) * TENTHS <= to; start++)
        walls.add(orientation === 'h' ? `h:${start}:${line}` : `v:${line}:${start}`);
    }
  }
  const edges = new Set();
  for (const key of dungeon.cells) for (const edge of cellEdges(...parseCell(key))) edges.add(edge);
  for (const edge of edges) {
    const sides = floorSides(dungeon, edge);
    const kind = doors.has(edge) ? 'door' : walls.has(edge) ? 'wall' : sides === 1 ? 'open' : null;
    if (kind && kind !== (sides === 1 ? 'wall' : 'open')) dungeon.edges.set(edge, kind);
  }
  return tidy(dungeon);
}
