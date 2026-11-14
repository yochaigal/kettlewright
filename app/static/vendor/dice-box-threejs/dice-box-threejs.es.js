var zo = Object.defineProperty;
var Bo = (h, e, t) => e in h ? zo(h, e, { enumerable: !0, configurable: !0, writable: !0, value: t }) : h[e] = t;
var Ys = (h, e, t) => (Bo(h, typeof e != "symbol" ? e + "" : e, t), t);
/**
 * @license
 * Copyright 2010-2022 Three.js Authors
 * SPDX-License-Identifier: MIT
 */
const Os = "143";
const Jt = "srgb", yn = "srgb-linear";
const Zs = "300 es";
class $n {
  addEventListener(e, t) {
    this._listeners === void 0 && (this._listeners = {});
    const n = this._listeners;
    n[e] === void 0 && (n[e] = []), n[e].indexOf(t) === -1 && n[e].push(t);
  }
  hasEventListener(e, t) {
    if (this._listeners === void 0)
      return !1;
    const n = this._listeners;
    return n[e] !== void 0 && n[e].indexOf(t) !== -1;
  }
  removeEventListener(e, t) {
    if (this._listeners === void 0)
      return;
    const i = this._listeners[e];
    if (i !== void 0) {
      const s = i.indexOf(t);
      s !== -1 && i.splice(s, 1);
    }
  }
  dispatchEvent(e) {
    if (this._listeners === void 0)
      return;
    const n = this._listeners[e.type];
    if (n !== void 0) {
      e.target = this;
      const i = n.slice(0);
      for (let s = 0, o = i.length; s < o; s++)
        i[s].call(this, e);
      e.target = null;
    }
  }
}
const nt = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "0a", "0b", "0c", "0d", "0e", "0f", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "1a", "1b", "1c", "1d", "1e", "1f", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "2a", "2b", "2c", "2d", "2e", "2f", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "3a", "3b", "3c", "3d", "3e", "3f", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "4a", "4b", "4c", "4d", "4e", "4f", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "5a", "5b", "5c", "5d", "5e", "5f", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "6a", "6b", "6c", "6d", "6e", "6f", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "7a", "7b", "7c", "7d", "7e", "7f", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "8a", "8b", "8c", "8d", "8e", "8f", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "9a", "9b", "9c", "9d", "9e", "9f", "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "aa", "ab", "ac", "ad", "ae", "af", "b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9", "ba", "bb", "bc", "bd", "be", "bf", "c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "ca", "cb", "cc", "cd", "ce", "cf", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "da", "db", "dc", "dd", "de", "df", "e0", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "e9", "ea", "eb", "ec", "ed", "ee", "ef", "f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "fa", "fb", "fc", "fd", "fe", "ff"], Qi = Math.PI / 180, zs = 180 / Math.PI;
function hi() {
  const h = Math.random() * 4294967295 | 0, e = Math.random() * 4294967295 | 0, t = Math.random() * 4294967295 | 0, n = Math.random() * 4294967295 | 0;
  return (nt[h & 255] + nt[h >> 8 & 255] + nt[h >> 16 & 255] + nt[h >> 24 & 255] + "-" + nt[e & 255] + nt[e >> 8 & 255] + "-" + nt[e >> 16 & 15 | 64] + nt[e >> 24 & 255] + "-" + nt[t & 63 | 128] + nt[t >> 8 & 255] + "-" + nt[t >> 16 & 255] + nt[t >> 24 & 255] + nt[n & 255] + nt[n >> 8 & 255] + nt[n >> 16 & 255] + nt[n >> 24 & 255]).toLowerCase();
}
function mt(h, e, t) {
  return Math.max(e, Math.min(t, h));
}
function No(h, e) {
  return (h % e + e) % e;
}
function es(h, e, t) {
  return (1 - t) * h + t * e;
}
function $s(h) {
  return (h & h - 1) === 0 && h !== 0;
}
function Bs(h) {
  return Math.pow(2, Math.floor(Math.log(h) / Math.LN2));
}
class Ce {
  constructor(e = 0, t = 0) {
    Ce.prototype.isVector2 = !0, this.x = e, this.y = t;
  }
  get width() {
    return this.x;
  }
  set width(e) {
    this.x = e;
  }
  get height() {
    return this.y;
  }
  set height(e) {
    this.y = e;
  }
  set(e, t) {
    return this.x = e, this.y = t, this;
  }
  setScalar(e) {
    return this.x = e, this.y = e, this;
  }
  setX(e) {
    return this.x = e, this;
  }
  setY(e) {
    return this.y = e, this;
  }
  setComponent(e, t) {
    switch (e) {
      case 0:
        this.x = t;
        break;
      case 1:
        this.y = t;
        break;
      default:
        throw new Error("index is out of range: " + e);
    }
    return this;
  }
  getComponent(e) {
    switch (e) {
      case 0:
        return this.x;
      case 1:
        return this.y;
      default:
        throw new Error("index is out of range: " + e);
    }
  }
  clone() {
    return new this.constructor(this.x, this.y);
  }
  copy(e) {
    return this.x = e.x, this.y = e.y, this;
  }
  add(e) {
    return this.x += e.x, this.y += e.y, this;
  }
  addScalar(e) {
    return this.x += e, this.y += e, this;
  }
  addVectors(e, t) {
    return this.x = e.x + t.x, this.y = e.y + t.y, this;
  }
  addScaledVector(e, t) {
    return this.x += e.x * t, this.y += e.y * t, this;
  }
  sub(e) {
    return this.x -= e.x, this.y -= e.y, this;
  }
  subScalar(e) {
    return this.x -= e, this.y -= e, this;
  }
  subVectors(e, t) {
    return this.x = e.x - t.x, this.y = e.y - t.y, this;
  }
  multiply(e) {
    return this.x *= e.x, this.y *= e.y, this;
  }
  multiplyScalar(e) {
    return this.x *= e, this.y *= e, this;
  }
  divide(e) {
    return this.x /= e.x, this.y /= e.y, this;
  }
  divideScalar(e) {
    return this.multiplyScalar(1 / e);
  }
  applyMatrix3(e) {
    const t = this.x, n = this.y, i = e.elements;
    return this.x = i[0] * t + i[3] * n + i[6], this.y = i[1] * t + i[4] * n + i[7], this;
  }
  min(e) {
    return this.x = Math.min(this.x, e.x), this.y = Math.min(this.y, e.y), this;
  }
  max(e) {
    return this.x = Math.max(this.x, e.x), this.y = Math.max(this.y, e.y), this;
  }
  clamp(e, t) {
    return this.x = Math.max(e.x, Math.min(t.x, this.x)), this.y = Math.max(e.y, Math.min(t.y, this.y)), this;
  }
  clampScalar(e, t) {
    return this.x = Math.max(e, Math.min(t, this.x)), this.y = Math.max(e, Math.min(t, this.y)), this;
  }
  clampLength(e, t) {
    const n = this.length();
    return this.divideScalar(n || 1).multiplyScalar(Math.max(e, Math.min(t, n)));
  }
  floor() {
    return this.x = Math.floor(this.x), this.y = Math.floor(this.y), this;
  }
  ceil() {
    return this.x = Math.ceil(this.x), this.y = Math.ceil(this.y), this;
  }
  round() {
    return this.x = Math.round(this.x), this.y = Math.round(this.y), this;
  }
  roundToZero() {
    return this.x = this.x < 0 ? Math.ceil(this.x) : Math.floor(this.x), this.y = this.y < 0 ? Math.ceil(this.y) : Math.floor(this.y), this;
  }
  negate() {
    return this.x = -this.x, this.y = -this.y, this;
  }
  dot(e) {
    return this.x * e.x + this.y * e.y;
  }
  cross(e) {
    return this.x * e.y - this.y * e.x;
  }
  lengthSq() {
    return this.x * this.x + this.y * this.y;
  }
  length() {
    return Math.sqrt(this.x * this.x + this.y * this.y);
  }
  manhattanLength() {
    return Math.abs(this.x) + Math.abs(this.y);
  }
  normalize() {
    return this.divideScalar(this.length() || 1);
  }
  angle() {
    return Math.atan2(-this.y, -this.x) + Math.PI;
  }
  distanceTo(e) {
    return Math.sqrt(this.distanceToSquared(e));
  }
  distanceToSquared(e) {
    const t = this.x - e.x, n = this.y - e.y;
    return t * t + n * n;
  }
  manhattanDistanceTo(e) {
    return Math.abs(this.x - e.x) + Math.abs(this.y - e.y);
  }
  setLength(e) {
    return this.normalize().multiplyScalar(e);
  }
  lerp(e, t) {
    return this.x += (e.x - this.x) * t, this.y += (e.y - this.y) * t, this;
  }
  lerpVectors(e, t, n) {
    return this.x = e.x + (t.x - e.x) * n, this.y = e.y + (t.y - e.y) * n, this;
  }
  equals(e) {
    return e.x === this.x && e.y === this.y;
  }
  fromArray(e, t = 0) {
    return this.x = e[t], this.y = e[t + 1], this;
  }
  toArray(e = [], t = 0) {
    return e[t] = this.x, e[t + 1] = this.y, e;
  }
  fromBufferAttribute(e, t) {
    return this.x = e.getX(t), this.y = e.getY(t), this;
  }
  rotateAround(e, t) {
    const n = Math.cos(t), i = Math.sin(t), s = this.x - e.x, o = this.y - e.y;
    return this.x = s * n - o * i + e.x, this.y = s * i + o * n + e.y, this;
  }
  random() {
    return this.x = Math.random(), this.y = Math.random(), this;
  }
  *[Symbol.iterator]() {
    yield this.x, yield this.y;
  }
}
class Mt {
  constructor() {
    Mt.prototype.isMatrix3 = !0, this.elements = [
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1
    ];
  }
  set(e, t, n, i, s, o, r, l, a) {
    const c = this.elements;
    return c[0] = e, c[1] = i, c[2] = r, c[3] = t, c[4] = s, c[5] = l, c[6] = n, c[7] = o, c[8] = a, this;
  }
  identity() {
    return this.set(
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1
    ), this;
  }
  copy(e) {
    const t = this.elements, n = e.elements;
    return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[4] = n[4], t[5] = n[5], t[6] = n[6], t[7] = n[7], t[8] = n[8], this;
  }
  extractBasis(e, t, n) {
    return e.setFromMatrix3Column(this, 0), t.setFromMatrix3Column(this, 1), n.setFromMatrix3Column(this, 2), this;
  }
  setFromMatrix4(e) {
    const t = e.elements;
    return this.set(
      t[0],
      t[4],
      t[8],
      t[1],
      t[5],
      t[9],
      t[2],
      t[6],
      t[10]
    ), this;
  }
  multiply(e) {
    return this.multiplyMatrices(this, e);
  }
  premultiply(e) {
    return this.multiplyMatrices(e, this);
  }
  multiplyMatrices(e, t) {
    const n = e.elements, i = t.elements, s = this.elements, o = n[0], r = n[3], l = n[6], a = n[1], c = n[4], d = n[7], u = n[2], m = n[5], g = n[8], p = i[0], f = i[3], v = i[6], _ = i[1], w = i[4], x = i[7], M = i[2], E = i[5], R = i[8];
    return s[0] = o * p + r * _ + l * M, s[3] = o * f + r * w + l * E, s[6] = o * v + r * x + l * R, s[1] = a * p + c * _ + d * M, s[4] = a * f + c * w + d * E, s[7] = a * v + c * x + d * R, s[2] = u * p + m * _ + g * M, s[5] = u * f + m * w + g * E, s[8] = u * v + m * x + g * R, this;
  }
  multiplyScalar(e) {
    const t = this.elements;
    return t[0] *= e, t[3] *= e, t[6] *= e, t[1] *= e, t[4] *= e, t[7] *= e, t[2] *= e, t[5] *= e, t[8] *= e, this;
  }
  determinant() {
    const e = this.elements, t = e[0], n = e[1], i = e[2], s = e[3], o = e[4], r = e[5], l = e[6], a = e[7], c = e[8];
    return t * o * c - t * r * a - n * s * c + n * r * l + i * s * a - i * o * l;
  }
  invert() {
    const e = this.elements, t = e[0], n = e[1], i = e[2], s = e[3], o = e[4], r = e[5], l = e[6], a = e[7], c = e[8], d = c * o - r * a, u = r * l - c * s, m = a * s - o * l, g = t * d + n * u + i * m;
    if (g === 0)
      return this.set(0, 0, 0, 0, 0, 0, 0, 0, 0);
    const p = 1 / g;
    return e[0] = d * p, e[1] = (i * a - c * n) * p, e[2] = (r * n - i * o) * p, e[3] = u * p, e[4] = (c * t - i * l) * p, e[5] = (i * s - r * t) * p, e[6] = m * p, e[7] = (n * l - a * t) * p, e[8] = (o * t - n * s) * p, this;
  }
  transpose() {
    let e;
    const t = this.elements;
    return e = t[1], t[1] = t[3], t[3] = e, e = t[2], t[2] = t[6], t[6] = e, e = t[5], t[5] = t[7], t[7] = e, this;
  }
  getNormalMatrix(e) {
    return this.setFromMatrix4(e).invert().transpose();
  }
  transposeIntoArray(e) {
    const t = this.elements;
    return e[0] = t[0], e[1] = t[3], e[2] = t[6], e[3] = t[1], e[4] = t[4], e[5] = t[7], e[6] = t[2], e[7] = t[5], e[8] = t[8], this;
  }
  setUvTransform(e, t, n, i, s, o, r) {
    const l = Math.cos(s), a = Math.sin(s);
    return this.set(
      n * l,
      n * a,
      -n * (l * o + a * r) + o + e,
      -i * a,
      i * l,
      -i * (-a * o + l * r) + r + t,
      0,
      0,
      1
    ), this;
  }
  scale(e, t) {
    const n = this.elements;
    return n[0] *= e, n[3] *= e, n[6] *= e, n[1] *= t, n[4] *= t, n[7] *= t, this;
  }
  rotate(e) {
    const t = Math.cos(e), n = Math.sin(e), i = this.elements, s = i[0], o = i[3], r = i[6], l = i[1], a = i[4], c = i[7];
    return i[0] = t * s + n * l, i[3] = t * o + n * a, i[6] = t * r + n * c, i[1] = -n * s + t * l, i[4] = -n * o + t * a, i[7] = -n * r + t * c, this;
  }
  translate(e, t) {
    const n = this.elements;
    return n[0] += e * n[2], n[3] += e * n[5], n[6] += e * n[8], n[1] += t * n[2], n[4] += t * n[5], n[7] += t * n[8], this;
  }
  equals(e) {
    const t = this.elements, n = e.elements;
    for (let i = 0; i < 9; i++)
      if (t[i] !== n[i])
        return !1;
    return !0;
  }
  fromArray(e, t = 0) {
    for (let n = 0; n < 9; n++)
      this.elements[n] = e[n + t];
    return this;
  }
  toArray(e = [], t = 0) {
    const n = this.elements;
    return e[t] = n[0], e[t + 1] = n[1], e[t + 2] = n[2], e[t + 3] = n[3], e[t + 4] = n[4], e[t + 5] = n[5], e[t + 6] = n[6], e[t + 7] = n[7], e[t + 8] = n[8], e;
  }
  clone() {
    return new this.constructor().fromArray(this.elements);
  }
}
function to(h) {
  for (let e = h.length - 1; e >= 0; --e)
    if (h[e] > 65535)
      return !0;
  return !1;
}
function qi(h) {
  return document.createElementNS("http://www.w3.org/1999/xhtml", h);
}
function bn(h) {
  return h < 0.04045 ? h * 0.0773993808 : Math.pow(h * 0.9478672986 + 0.0521327014, 2.4);
}
function Wi(h) {
  return h < 31308e-7 ? h * 12.92 : 1.055 * Math.pow(h, 0.41666) - 0.055;
}
const ts = {
  [Jt]: { [yn]: bn },
  [yn]: { [Jt]: Wi }
}, St = {
  legacyMode: !0,
  get workingColorSpace() {
    return yn;
  },
  set workingColorSpace(h) {
    console.warn("THREE.ColorManagement: .workingColorSpace is readonly.");
  },
  convert: function(h, e, t) {
    if (this.legacyMode || e === t || !e || !t)
      return h;
    if (ts[e] && ts[e][t] !== void 0) {
      const n = ts[e][t];
      return h.r = n(h.r), h.g = n(h.g), h.b = n(h.b), h;
    }
    throw new Error("Unsupported color space conversion.");
  },
  fromWorkingColorSpace: function(h, e) {
    return this.convert(h, this.workingColorSpace, e);
  },
  toWorkingColorSpace: function(h, e) {
    return this.convert(h, e, this.workingColorSpace);
  }
}, no = {
  aliceblue: 15792383,
  antiquewhite: 16444375,
  aqua: 65535,
  aquamarine: 8388564,
  azure: 15794175,
  beige: 16119260,
  bisque: 16770244,
  black: 0,
  blanchedalmond: 16772045,
  blue: 255,
  blueviolet: 9055202,
  brown: 10824234,
  burlywood: 14596231,
  cadetblue: 6266528,
  chartreuse: 8388352,
  chocolate: 13789470,
  coral: 16744272,
  cornflowerblue: 6591981,
  cornsilk: 16775388,
  crimson: 14423100,
  cyan: 65535,
  darkblue: 139,
  darkcyan: 35723,
  darkgoldenrod: 12092939,
  darkgray: 11119017,
  darkgreen: 25600,
  darkgrey: 11119017,
  darkkhaki: 12433259,
  darkmagenta: 9109643,
  darkolivegreen: 5597999,
  darkorange: 16747520,
  darkorchid: 10040012,
  darkred: 9109504,
  darksalmon: 15308410,
  darkseagreen: 9419919,
  darkslateblue: 4734347,
  darkslategray: 3100495,
  darkslategrey: 3100495,
  darkturquoise: 52945,
  darkviolet: 9699539,
  deeppink: 16716947,
  deepskyblue: 49151,
  dimgray: 6908265,
  dimgrey: 6908265,
  dodgerblue: 2003199,
  firebrick: 11674146,
  floralwhite: 16775920,
  forestgreen: 2263842,
  fuchsia: 16711935,
  gainsboro: 14474460,
  ghostwhite: 16316671,
  gold: 16766720,
  goldenrod: 14329120,
  gray: 8421504,
  green: 32768,
  greenyellow: 11403055,
  grey: 8421504,
  honeydew: 15794160,
  hotpink: 16738740,
  indianred: 13458524,
  indigo: 4915330,
  ivory: 16777200,
  khaki: 15787660,
  lavender: 15132410,
  lavenderblush: 16773365,
  lawngreen: 8190976,
  lemonchiffon: 16775885,
  lightblue: 11393254,
  lightcoral: 15761536,
  lightcyan: 14745599,
  lightgoldenrodyellow: 16448210,
  lightgray: 13882323,
  lightgreen: 9498256,
  lightgrey: 13882323,
  lightpink: 16758465,
  lightsalmon: 16752762,
  lightseagreen: 2142890,
  lightskyblue: 8900346,
  lightslategray: 7833753,
  lightslategrey: 7833753,
  lightsteelblue: 11584734,
  lightyellow: 16777184,
  lime: 65280,
  limegreen: 3329330,
  linen: 16445670,
  magenta: 16711935,
  maroon: 8388608,
  mediumaquamarine: 6737322,
  mediumblue: 205,
  mediumorchid: 12211667,
  mediumpurple: 9662683,
  mediumseagreen: 3978097,
  mediumslateblue: 8087790,
  mediumspringgreen: 64154,
  mediumturquoise: 4772300,
  mediumvioletred: 13047173,
  midnightblue: 1644912,
  mintcream: 16121850,
  mistyrose: 16770273,
  moccasin: 16770229,
  navajowhite: 16768685,
  navy: 128,
  oldlace: 16643558,
  olive: 8421376,
  olivedrab: 7048739,
  orange: 16753920,
  orangered: 16729344,
  orchid: 14315734,
  palegoldenrod: 15657130,
  palegreen: 10025880,
  paleturquoise: 11529966,
  palevioletred: 14381203,
  papayawhip: 16773077,
  peachpuff: 16767673,
  peru: 13468991,
  pink: 16761035,
  plum: 14524637,
  powderblue: 11591910,
  purple: 8388736,
  rebeccapurple: 6697881,
  red: 16711680,
  rosybrown: 12357519,
  royalblue: 4286945,
  saddlebrown: 9127187,
  salmon: 16416882,
  sandybrown: 16032864,
  seagreen: 3050327,
  seashell: 16774638,
  sienna: 10506797,
  silver: 12632256,
  skyblue: 8900331,
  slateblue: 6970061,
  slategray: 7372944,
  slategrey: 7372944,
  snow: 16775930,
  springgreen: 65407,
  steelblue: 4620980,
  tan: 13808780,
  teal: 32896,
  thistle: 14204888,
  tomato: 16737095,
  turquoise: 4251856,
  violet: 15631086,
  wheat: 16113331,
  white: 16777215,
  whitesmoke: 16119285,
  yellow: 16776960,
  yellowgreen: 10145074
}, Ye = { r: 0, g: 0, b: 0 }, Et = { h: 0, s: 0, l: 0 }, gi = { h: 0, s: 0, l: 0 };
function ns(h, e, t) {
  return t < 0 && (t += 1), t > 1 && (t -= 1), t < 1 / 6 ? h + (e - h) * 6 * t : t < 1 / 2 ? e : t < 2 / 3 ? h + (e - h) * 6 * (2 / 3 - t) : h;
}
function _i(h, e) {
  return e.r = h.r, e.g = h.g, e.b = h.b, e;
}
class Ae {
  constructor(e, t, n) {
    return this.isColor = !0, this.r = 1, this.g = 1, this.b = 1, t === void 0 && n === void 0 ? this.set(e) : this.setRGB(e, t, n);
  }
  set(e) {
    return e && e.isColor ? this.copy(e) : typeof e == "number" ? this.setHex(e) : typeof e == "string" && this.setStyle(e), this;
  }
  setScalar(e) {
    return this.r = e, this.g = e, this.b = e, this;
  }
  setHex(e, t = Jt) {
    return e = Math.floor(e), this.r = (e >> 16 & 255) / 255, this.g = (e >> 8 & 255) / 255, this.b = (e & 255) / 255, St.toWorkingColorSpace(this, t), this;
  }
  setRGB(e, t, n, i = yn) {
    return this.r = e, this.g = t, this.b = n, St.toWorkingColorSpace(this, i), this;
  }
  setHSL(e, t, n, i = yn) {
    if (e = No(e, 1), t = mt(t, 0, 1), n = mt(n, 0, 1), t === 0)
      this.r = this.g = this.b = n;
    else {
      const s = n <= 0.5 ? n * (1 + t) : n + t - n * t, o = 2 * n - s;
      this.r = ns(o, s, e + 1 / 3), this.g = ns(o, s, e), this.b = ns(o, s, e - 1 / 3);
    }
    return St.toWorkingColorSpace(this, i), this;
  }
  setStyle(e, t = Jt) {
    function n(s) {
      s !== void 0 && parseFloat(s) < 1 && console.warn("THREE.Color: Alpha component of " + e + " will be ignored.");
    }
    let i;
    if (i = /^((?:rgb|hsl)a?)\(([^\)]*)\)/.exec(e)) {
      let s;
      const o = i[1], r = i[2];
      switch (o) {
        case "rgb":
        case "rgba":
          if (s = /^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(r))
            return this.r = Math.min(255, parseInt(s[1], 10)) / 255, this.g = Math.min(255, parseInt(s[2], 10)) / 255, this.b = Math.min(255, parseInt(s[3], 10)) / 255, St.toWorkingColorSpace(this, t), n(s[4]), this;
          if (s = /^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(r))
            return this.r = Math.min(100, parseInt(s[1], 10)) / 100, this.g = Math.min(100, parseInt(s[2], 10)) / 100, this.b = Math.min(100, parseInt(s[3], 10)) / 100, St.toWorkingColorSpace(this, t), n(s[4]), this;
          break;
        case "hsl":
        case "hsla":
          if (s = /^\s*(\d*\.?\d+)\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(r)) {
            const l = parseFloat(s[1]) / 360, a = parseInt(s[2], 10) / 100, c = parseInt(s[3], 10) / 100;
            return n(s[4]), this.setHSL(l, a, c, t);
          }
          break;
      }
    } else if (i = /^\#([A-Fa-f\d]+)$/.exec(e)) {
      const s = i[1], o = s.length;
      if (o === 3)
        return this.r = parseInt(s.charAt(0) + s.charAt(0), 16) / 255, this.g = parseInt(s.charAt(1) + s.charAt(1), 16) / 255, this.b = parseInt(s.charAt(2) + s.charAt(2), 16) / 255, St.toWorkingColorSpace(this, t), this;
      if (o === 6)
        return this.r = parseInt(s.charAt(0) + s.charAt(1), 16) / 255, this.g = parseInt(s.charAt(2) + s.charAt(3), 16) / 255, this.b = parseInt(s.charAt(4) + s.charAt(5), 16) / 255, St.toWorkingColorSpace(this, t), this;
    }
    return e && e.length > 0 ? this.setColorName(e, t) : this;
  }
  setColorName(e, t = Jt) {
    const n = no[e.toLowerCase()];
    return n !== void 0 ? this.setHex(n, t) : console.warn("THREE.Color: Unknown color " + e), this;
  }
  clone() {
    return new this.constructor(this.r, this.g, this.b);
  }
  copy(e) {
    return this.r = e.r, this.g = e.g, this.b = e.b, this;
  }
  copySRGBToLinear(e) {
    return this.r = bn(e.r), this.g = bn(e.g), this.b = bn(e.b), this;
  }
  copyLinearToSRGB(e) {
    return this.r = Wi(e.r), this.g = Wi(e.g), this.b = Wi(e.b), this;
  }
  convertSRGBToLinear() {
    return this.copySRGBToLinear(this), this;
  }
  convertLinearToSRGB() {
    return this.copyLinearToSRGB(this), this;
  }
  getHex(e = Jt) {
    return St.fromWorkingColorSpace(_i(this, Ye), e), mt(Ye.r * 255, 0, 255) << 16 ^ mt(Ye.g * 255, 0, 255) << 8 ^ mt(Ye.b * 255, 0, 255) << 0;
  }
  getHexString(e = Jt) {
    return ("000000" + this.getHex(e).toString(16)).slice(-6);
  }
  getHSL(e, t = yn) {
    St.fromWorkingColorSpace(_i(this, Ye), t);
    const n = Ye.r, i = Ye.g, s = Ye.b, o = Math.max(n, i, s), r = Math.min(n, i, s);
    let l, a;
    const c = (r + o) / 2;
    if (r === o)
      l = 0, a = 0;
    else {
      const d = o - r;
      switch (a = c <= 0.5 ? d / (o + r) : d / (2 - o - r), o) {
        case n:
          l = (i - s) / d + (i < s ? 6 : 0);
          break;
        case i:
          l = (s - n) / d + 2;
          break;
        case s:
          l = (n - i) / d + 4;
          break;
      }
      l /= 6;
    }
    return e.h = l, e.s = a, e.l = c, e;
  }
  getRGB(e, t = yn) {
    return St.fromWorkingColorSpace(_i(this, Ye), t), e.r = Ye.r, e.g = Ye.g, e.b = Ye.b, e;
  }
  getStyle(e = Jt) {
    return St.fromWorkingColorSpace(_i(this, Ye), e), e !== Jt ? `color(${e} ${Ye.r} ${Ye.g} ${Ye.b})` : `rgb(${Ye.r * 255 | 0},${Ye.g * 255 | 0},${Ye.b * 255 | 0})`;
  }
  offsetHSL(e, t, n) {
    return this.getHSL(Et), Et.h += e, Et.s += t, Et.l += n, this.setHSL(Et.h, Et.s, Et.l), this;
  }
  add(e) {
    return this.r += e.r, this.g += e.g, this.b += e.b, this;
  }
  addColors(e, t) {
    return this.r = e.r + t.r, this.g = e.g + t.g, this.b = e.b + t.b, this;
  }
  addScalar(e) {
    return this.r += e, this.g += e, this.b += e, this;
  }
  sub(e) {
    return this.r = Math.max(0, this.r - e.r), this.g = Math.max(0, this.g - e.g), this.b = Math.max(0, this.b - e.b), this;
  }
  multiply(e) {
    return this.r *= e.r, this.g *= e.g, this.b *= e.b, this;
  }
  multiplyScalar(e) {
    return this.r *= e, this.g *= e, this.b *= e, this;
  }
  lerp(e, t) {
    return this.r += (e.r - this.r) * t, this.g += (e.g - this.g) * t, this.b += (e.b - this.b) * t, this;
  }
  lerpColors(e, t, n) {
    return this.r = e.r + (t.r - e.r) * n, this.g = e.g + (t.g - e.g) * n, this.b = e.b + (t.b - e.b) * n, this;
  }
  lerpHSL(e, t) {
    this.getHSL(Et), e.getHSL(gi);
    const n = es(Et.h, gi.h, t), i = es(Et.s, gi.s, t), s = es(Et.l, gi.l, t);
    return this.setHSL(n, i, s), this;
  }
  equals(e) {
    return e.r === this.r && e.g === this.g && e.b === this.b;
  }
  fromArray(e, t = 0) {
    return this.r = e[t], this.g = e[t + 1], this.b = e[t + 2], this;
  }
  toArray(e = [], t = 0) {
    return e[t] = this.r, e[t + 1] = this.g, e[t + 2] = this.b, e;
  }
  fromBufferAttribute(e, t) {
    return this.r = e.getX(t), this.g = e.getY(t), this.b = e.getZ(t), e.normalized === !0 && (this.r /= 255, this.g /= 255, this.b /= 255), this;
  }
  toJSON() {
    return this.getHex();
  }
  *[Symbol.iterator]() {
    yield this.r, yield this.g, yield this.b;
  }
}
Ae.NAMES = no;
let Fn;
class io {
  static getDataURL(e) {
    if (/^data:/i.test(e.src) || typeof HTMLCanvasElement > "u")
      return e.src;
    let t;
    if (e instanceof HTMLCanvasElement)
      t = e;
    else {
      Fn === void 0 && (Fn = qi("canvas")), Fn.width = e.width, Fn.height = e.height;
      const n = Fn.getContext("2d");
      e instanceof ImageData ? n.putImageData(e, 0, 0) : n.drawImage(e, 0, 0, e.width, e.height), t = Fn;
    }
    return t.width > 2048 || t.height > 2048 ? (console.warn("THREE.ImageUtils.getDataURL: Image converted to jpg for performance reasons", e), t.toDataURL("image/jpeg", 0.6)) : t.toDataURL("image/png");
  }
  static sRGBToLinear(e) {
    if (typeof HTMLImageElement < "u" && e instanceof HTMLImageElement || typeof HTMLCanvasElement < "u" && e instanceof HTMLCanvasElement || typeof ImageBitmap < "u" && e instanceof ImageBitmap) {
      const t = qi("canvas");
      t.width = e.width, t.height = e.height;
      const n = t.getContext("2d");
      n.drawImage(e, 0, 0, e.width, e.height);
      const i = n.getImageData(0, 0, e.width, e.height), s = i.data;
      for (let o = 0; o < s.length; o++)
        s[o] = bn(s[o] / 255) * 255;
      return n.putImageData(i, 0, 0), t;
    } else if (e.data) {
      const t = e.data.slice(0);
      for (let n = 0; n < t.length; n++)
        t instanceof Uint8Array || t instanceof Uint8ClampedArray ? t[n] = Math.floor(bn(t[n] / 255) * 255) : t[n] = bn(t[n]);
      return {
        data: t,
        width: e.width,
        height: e.height
      };
    } else
      return console.warn("THREE.ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."), e;
  }
}
class so {
  constructor(e = null) {
    this.isSource = !0, this.uuid = hi(), this.data = e, this.version = 0;
  }
  set needsUpdate(e) {
    e === !0 && this.version++;
  }
  toJSON(e) {
    const t = e === void 0 || typeof e == "string";
    if (!t && e.images[this.uuid] !== void 0)
      return e.images[this.uuid];
    const n = {
      uuid: this.uuid,
      url: ""
    }, i = this.data;
    if (i !== null) {
      let s;
      if (Array.isArray(i)) {
        s = [];
        for (let o = 0, r = i.length; o < r; o++)
          i[o].isDataTexture ? s.push(is(i[o].image)) : s.push(is(i[o]));
      } else
        s = is(i);
      n.url = s;
    }
    return t || (e.images[this.uuid] = n), n;
  }
}
function is(h) {
  return typeof HTMLImageElement < "u" && h instanceof HTMLImageElement || typeof HTMLCanvasElement < "u" && h instanceof HTMLCanvasElement || typeof ImageBitmap < "u" && h instanceof ImageBitmap ? io.getDataURL(h) : h.data ? {
    data: Array.from(h.data),
    width: h.width,
    height: h.height,
    type: h.data.constructor.name
  } : (console.warn("THREE.Texture: Unable to serialize Texture."), {});
}
let Oo = 0;
class _t extends $n {
  constructor(e = _t.DEFAULT_IMAGE, t = _t.DEFAULT_MAPPING, n = 1001, i = 1001, s = 1006, o = 1008, r = 1023, l = 1009, a = 1, c = 3e3) {
    super(), this.isTexture = !0, Object.defineProperty(this, "id", { value: Oo++ }), this.uuid = hi(), this.name = "", this.source = new so(e), this.mipmaps = [], this.mapping = t, this.wrapS = n, this.wrapT = i, this.magFilter = s, this.minFilter = o, this.anisotropy = a, this.format = r, this.internalFormat = null, this.type = l, this.offset = new Ce(0, 0), this.repeat = new Ce(1, 1), this.center = new Ce(0, 0), this.rotation = 0, this.matrixAutoUpdate = !0, this.matrix = new Mt(), this.generateMipmaps = !0, this.premultiplyAlpha = !1, this.flipY = !0, this.unpackAlignment = 4, this.encoding = c, this.userData = {}, this.version = 0, this.onUpdate = null, this.isRenderTargetTexture = !1, this.needsPMREMUpdate = !1;
  }
  get image() {
    return this.source.data;
  }
  set image(e) {
    this.source.data = e;
  }
  updateMatrix() {
    this.matrix.setUvTransform(this.offset.x, this.offset.y, this.repeat.x, this.repeat.y, this.rotation, this.center.x, this.center.y);
  }
  clone() {
    return new this.constructor().copy(this);
  }
  copy(e) {
    return this.name = e.name, this.source = e.source, this.mipmaps = e.mipmaps.slice(0), this.mapping = e.mapping, this.wrapS = e.wrapS, this.wrapT = e.wrapT, this.magFilter = e.magFilter, this.minFilter = e.minFilter, this.anisotropy = e.anisotropy, this.format = e.format, this.internalFormat = e.internalFormat, this.type = e.type, this.offset.copy(e.offset), this.repeat.copy(e.repeat), this.center.copy(e.center), this.rotation = e.rotation, this.matrixAutoUpdate = e.matrixAutoUpdate, this.matrix.copy(e.matrix), this.generateMipmaps = e.generateMipmaps, this.premultiplyAlpha = e.premultiplyAlpha, this.flipY = e.flipY, this.unpackAlignment = e.unpackAlignment, this.encoding = e.encoding, this.userData = JSON.parse(JSON.stringify(e.userData)), this.needsUpdate = !0, this;
  }
  toJSON(e) {
    const t = e === void 0 || typeof e == "string";
    if (!t && e.textures[this.uuid] !== void 0)
      return e.textures[this.uuid];
    const n = {
      metadata: {
        version: 4.5,
        type: "Texture",
        generator: "Texture.toJSON"
      },
      uuid: this.uuid,
      name: this.name,
      image: this.source.toJSON(e).uuid,
      mapping: this.mapping,
      repeat: [this.repeat.x, this.repeat.y],
      offset: [this.offset.x, this.offset.y],
      center: [this.center.x, this.center.y],
      rotation: this.rotation,
      wrap: [this.wrapS, this.wrapT],
      format: this.format,
      type: this.type,
      encoding: this.encoding,
      minFilter: this.minFilter,
      magFilter: this.magFilter,
      anisotropy: this.anisotropy,
      flipY: this.flipY,
      premultiplyAlpha: this.premultiplyAlpha,
      unpackAlignment: this.unpackAlignment
    };
    return JSON.stringify(this.userData) !== "{}" && (n.userData = this.userData), t || (e.textures[this.uuid] = n), n;
  }
  dispose() {
    this.dispatchEvent({ type: "dispose" });
  }
  transformUv(e) {
    if (this.mapping !== 300)
      return e;
    if (e.applyMatrix3(this.matrix), e.x < 0 || e.x > 1)
      switch (this.wrapS) {
        case 1e3:
          e.x = e.x - Math.floor(e.x);
          break;
        case 1001:
          e.x = e.x < 0 ? 0 : 1;
          break;
        case 1002:
          Math.abs(Math.floor(e.x) % 2) === 1 ? e.x = Math.ceil(e.x) - e.x : e.x = e.x - Math.floor(e.x);
          break;
      }
    if (e.y < 0 || e.y > 1)
      switch (this.wrapT) {
        case 1e3:
          e.y = e.y - Math.floor(e.y);
          break;
        case 1001:
          e.y = e.y < 0 ? 0 : 1;
          break;
        case 1002:
          Math.abs(Math.floor(e.y) % 2) === 1 ? e.y = Math.ceil(e.y) - e.y : e.y = e.y - Math.floor(e.y);
          break;
      }
    return this.flipY && (e.y = 1 - e.y), e;
  }
  set needsUpdate(e) {
    e === !0 && (this.version++, this.source.needsUpdate = !0);
  }
}
_t.DEFAULT_IMAGE = null;
_t.DEFAULT_MAPPING = 300;
class $e {
  constructor(e = 0, t = 0, n = 0, i = 1) {
    $e.prototype.isVector4 = !0, this.x = e, this.y = t, this.z = n, this.w = i;
  }
  get width() {
    return this.z;
  }
  set width(e) {
    this.z = e;
  }
  get height() {
    return this.w;
  }
  set height(e) {
    this.w = e;
  }
  set(e, t, n, i) {
    return this.x = e, this.y = t, this.z = n, this.w = i, this;
  }
  setScalar(e) {
    return this.x = e, this.y = e, this.z = e, this.w = e, this;
  }
  setX(e) {
    return this.x = e, this;
  }
  setY(e) {
    return this.y = e, this;
  }
  setZ(e) {
    return this.z = e, this;
  }
  setW(e) {
    return this.w = e, this;
  }
  setComponent(e, t) {
    switch (e) {
      case 0:
        this.x = t;
        break;
      case 1:
        this.y = t;
        break;
      case 2:
        this.z = t;
        break;
      case 3:
        this.w = t;
        break;
      default:
        throw new Error("index is out of range: " + e);
    }
    return this;
  }
  getComponent(e) {
    switch (e) {
      case 0:
        return this.x;
      case 1:
        return this.y;
      case 2:
        return this.z;
      case 3:
        return this.w;
      default:
        throw new Error("index is out of range: " + e);
    }
  }
  clone() {
    return new this.constructor(this.x, this.y, this.z, this.w);
  }
  copy(e) {
    return this.x = e.x, this.y = e.y, this.z = e.z, this.w = e.w !== void 0 ? e.w : 1, this;
  }
  add(e) {
    return this.x += e.x, this.y += e.y, this.z += e.z, this.w += e.w, this;
  }
  addScalar(e) {
    return this.x += e, this.y += e, this.z += e, this.w += e, this;
  }
  addVectors(e, t) {
    return this.x = e.x + t.x, this.y = e.y + t.y, this.z = e.z + t.z, this.w = e.w + t.w, this;
  }
  addScaledVector(e, t) {
    return this.x += e.x * t, this.y += e.y * t, this.z += e.z * t, this.w += e.w * t, this;
  }
  sub(e) {
    return this.x -= e.x, this.y -= e.y, this.z -= e.z, this.w -= e.w, this;
  }
  subScalar(e) {
    return this.x -= e, this.y -= e, this.z -= e, this.w -= e, this;
  }
  subVectors(e, t) {
    return this.x = e.x - t.x, this.y = e.y - t.y, this.z = e.z - t.z, this.w = e.w - t.w, this;
  }
  multiply(e) {
    return this.x *= e.x, this.y *= e.y, this.z *= e.z, this.w *= e.w, this;
  }
  multiplyScalar(e) {
    return this.x *= e, this.y *= e, this.z *= e, this.w *= e, this;
  }
  applyMatrix4(e) {
    const t = this.x, n = this.y, i = this.z, s = this.w, o = e.elements;
    return this.x = o[0] * t + o[4] * n + o[8] * i + o[12] * s, this.y = o[1] * t + o[5] * n + o[9] * i + o[13] * s, this.z = o[2] * t + o[6] * n + o[10] * i + o[14] * s, this.w = o[3] * t + o[7] * n + o[11] * i + o[15] * s, this;
  }
  divideScalar(e) {
    return this.multiplyScalar(1 / e);
  }
  setAxisAngleFromQuaternion(e) {
    this.w = 2 * Math.acos(e.w);
    const t = Math.sqrt(1 - e.w * e.w);
    return t < 1e-4 ? (this.x = 1, this.y = 0, this.z = 0) : (this.x = e.x / t, this.y = e.y / t, this.z = e.z / t), this;
  }
  setAxisAngleFromRotationMatrix(e) {
    let t, n, i, s;
    const l = e.elements, a = l[0], c = l[4], d = l[8], u = l[1], m = l[5], g = l[9], p = l[2], f = l[6], v = l[10];
    if (Math.abs(c - u) < 0.01 && Math.abs(d - p) < 0.01 && Math.abs(g - f) < 0.01) {
      if (Math.abs(c + u) < 0.1 && Math.abs(d + p) < 0.1 && Math.abs(g + f) < 0.1 && Math.abs(a + m + v - 3) < 0.1)
        return this.set(1, 0, 0, 0), this;
      t = Math.PI;
      const w = (a + 1) / 2, x = (m + 1) / 2, M = (v + 1) / 2, E = (c + u) / 4, R = (d + p) / 4, y = (g + f) / 4;
      return w > x && w > M ? w < 0.01 ? (n = 0, i = 0.707106781, s = 0.707106781) : (n = Math.sqrt(w), i = E / n, s = R / n) : x > M ? x < 0.01 ? (n = 0.707106781, i = 0, s = 0.707106781) : (i = Math.sqrt(x), n = E / i, s = y / i) : M < 0.01 ? (n = 0.707106781, i = 0.707106781, s = 0) : (s = Math.sqrt(M), n = R / s, i = y / s), this.set(n, i, s, t), this;
    }
    let _ = Math.sqrt((f - g) * (f - g) + (d - p) * (d - p) + (u - c) * (u - c));
    return Math.abs(_) < 1e-3 && (_ = 1), this.x = (f - g) / _, this.y = (d - p) / _, this.z = (u - c) / _, this.w = Math.acos((a + m + v - 1) / 2), this;
  }
  min(e) {
    return this.x = Math.min(this.x, e.x), this.y = Math.min(this.y, e.y), this.z = Math.min(this.z, e.z), this.w = Math.min(this.w, e.w), this;
  }
  max(e) {
    return this.x = Math.max(this.x, e.x), this.y = Math.max(this.y, e.y), this.z = Math.max(this.z, e.z), this.w = Math.max(this.w, e.w), this;
  }
  clamp(e, t) {
    return this.x = Math.max(e.x, Math.min(t.x, this.x)), this.y = Math.max(e.y, Math.min(t.y, this.y)), this.z = Math.max(e.z, Math.min(t.z, this.z)), this.w = Math.max(e.w, Math.min(t.w, this.w)), this;
  }
  clampScalar(e, t) {
    return this.x = Math.max(e, Math.min(t, this.x)), this.y = Math.max(e, Math.min(t, this.y)), this.z = Math.max(e, Math.min(t, this.z)), this.w = Math.max(e, Math.min(t, this.w)), this;
  }
  clampLength(e, t) {
    const n = this.length();
    return this.divideScalar(n || 1).multiplyScalar(Math.max(e, Math.min(t, n)));
  }
  floor() {
    return this.x = Math.floor(this.x), this.y = Math.floor(this.y), this.z = Math.floor(this.z), this.w = Math.floor(this.w), this;
  }
  ceil() {
    return this.x = Math.ceil(this.x), this.y = Math.ceil(this.y), this.z = Math.ceil(this.z), this.w = Math.ceil(this.w), this;
  }
  round() {
    return this.x = Math.round(this.x), this.y = Math.round(this.y), this.z = Math.round(this.z), this.w = Math.round(this.w), this;
  }
  roundToZero() {
    return this.x = this.x < 0 ? Math.ceil(this.x) : Math.floor(this.x), this.y = this.y < 0 ? Math.ceil(this.y) : Math.floor(this.y), this.z = this.z < 0 ? Math.ceil(this.z) : Math.floor(this.z), this.w = this.w < 0 ? Math.ceil(this.w) : Math.floor(this.w), this;
  }
  negate() {
    return this.x = -this.x, this.y = -this.y, this.z = -this.z, this.w = -this.w, this;
  }
  dot(e) {
    return this.x * e.x + this.y * e.y + this.z * e.z + this.w * e.w;
  }
  lengthSq() {
    return this.x * this.x + this.y * this.y + this.z * this.z + this.w * this.w;
  }
  length() {
    return Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z + this.w * this.w);
  }
  manhattanLength() {
    return Math.abs(this.x) + Math.abs(this.y) + Math.abs(this.z) + Math.abs(this.w);
  }
  normalize() {
    return this.divideScalar(this.length() || 1);
  }
  setLength(e) {
    return this.normalize().multiplyScalar(e);
  }
  lerp(e, t) {
    return this.x += (e.x - this.x) * t, this.y += (e.y - this.y) * t, this.z += (e.z - this.z) * t, this.w += (e.w - this.w) * t, this;
  }
  lerpVectors(e, t, n) {
    return this.x = e.x + (t.x - e.x) * n, this.y = e.y + (t.y - e.y) * n, this.z = e.z + (t.z - e.z) * n, this.w = e.w + (t.w - e.w) * n, this;
  }
  equals(e) {
    return e.x === this.x && e.y === this.y && e.z === this.z && e.w === this.w;
  }
  fromArray(e, t = 0) {
    return this.x = e[t], this.y = e[t + 1], this.z = e[t + 2], this.w = e[t + 3], this;
  }
  toArray(e = [], t = 0) {
    return e[t] = this.x, e[t + 1] = this.y, e[t + 2] = this.z, e[t + 3] = this.w, e;
  }
  fromBufferAttribute(e, t) {
    return this.x = e.getX(t), this.y = e.getY(t), this.z = e.getZ(t), this.w = e.getW(t), this;
  }
  random() {
    return this.x = Math.random(), this.y = Math.random(), this.z = Math.random(), this.w = Math.random(), this;
  }
  *[Symbol.iterator]() {
    yield this.x, yield this.y, yield this.z, yield this.w;
  }
}
class En extends $n {
  constructor(e, t, n = {}) {
    super(), this.isWebGLRenderTarget = !0, this.width = e, this.height = t, this.depth = 1, this.scissor = new $e(0, 0, e, t), this.scissorTest = !1, this.viewport = new $e(0, 0, e, t);
    const i = { width: e, height: t, depth: 1 };
    this.texture = new _t(i, n.mapping, n.wrapS, n.wrapT, n.magFilter, n.minFilter, n.format, n.type, n.anisotropy, n.encoding), this.texture.isRenderTargetTexture = !0, this.texture.flipY = !1, this.texture.generateMipmaps = n.generateMipmaps !== void 0 ? n.generateMipmaps : !1, this.texture.internalFormat = n.internalFormat !== void 0 ? n.internalFormat : null, this.texture.minFilter = n.minFilter !== void 0 ? n.minFilter : 1006, this.depthBuffer = n.depthBuffer !== void 0 ? n.depthBuffer : !0, this.stencilBuffer = n.stencilBuffer !== void 0 ? n.stencilBuffer : !1, this.depthTexture = n.depthTexture !== void 0 ? n.depthTexture : null, this.samples = n.samples !== void 0 ? n.samples : 0;
  }
  setSize(e, t, n = 1) {
    (this.width !== e || this.height !== t || this.depth !== n) && (this.width = e, this.height = t, this.depth = n, this.texture.image.width = e, this.texture.image.height = t, this.texture.image.depth = n, this.dispose()), this.viewport.set(0, 0, e, t), this.scissor.set(0, 0, e, t);
  }
  clone() {
    return new this.constructor().copy(this);
  }
  copy(e) {
    this.width = e.width, this.height = e.height, this.depth = e.depth, this.viewport.copy(e.viewport), this.texture = e.texture.clone(), this.texture.isRenderTargetTexture = !0;
    const t = Object.assign({}, e.texture.image);
    return this.texture.source = new so(t), this.depthBuffer = e.depthBuffer, this.stencilBuffer = e.stencilBuffer, e.depthTexture !== null && (this.depthTexture = e.depthTexture.clone()), this.samples = e.samples, this;
  }
  dispose() {
    this.dispatchEvent({ type: "dispose" });
  }
}
class ro extends _t {
  constructor(e = null, t = 1, n = 1, i = 1) {
    super(null), this.isDataArrayTexture = !0, this.image = { data: e, width: t, height: n, depth: i }, this.magFilter = 1003, this.minFilter = 1003, this.wrapR = 1001, this.generateMipmaps = !1, this.flipY = !1, this.unpackAlignment = 1;
  }
}
class Uo extends _t {
  constructor(e = null, t = 1, n = 1, i = 1) {
    super(null), this.isData3DTexture = !0, this.image = { data: e, width: t, height: n, depth: i }, this.magFilter = 1003, this.minFilter = 1003, this.wrapR = 1001, this.generateMipmaps = !1, this.flipY = !1, this.unpackAlignment = 1;
  }
}
class ui {
  constructor(e = 0, t = 0, n = 0, i = 1) {
    this.isQuaternion = !0, this._x = e, this._y = t, this._z = n, this._w = i;
  }
  static slerpFlat(e, t, n, i, s, o, r) {
    let l = n[i + 0], a = n[i + 1], c = n[i + 2], d = n[i + 3];
    const u = s[o + 0], m = s[o + 1], g = s[o + 2], p = s[o + 3];
    if (r === 0) {
      e[t + 0] = l, e[t + 1] = a, e[t + 2] = c, e[t + 3] = d;
      return;
    }
    if (r === 1) {
      e[t + 0] = u, e[t + 1] = m, e[t + 2] = g, e[t + 3] = p;
      return;
    }
    if (d !== p || l !== u || a !== m || c !== g) {
      let f = 1 - r;
      const v = l * u + a * m + c * g + d * p, _ = v >= 0 ? 1 : -1, w = 1 - v * v;
      if (w > Number.EPSILON) {
        const M = Math.sqrt(w), E = Math.atan2(M, v * _);
        f = Math.sin(f * E) / M, r = Math.sin(r * E) / M;
      }
      const x = r * _;
      if (l = l * f + u * x, a = a * f + m * x, c = c * f + g * x, d = d * f + p * x, f === 1 - r) {
        const M = 1 / Math.sqrt(l * l + a * a + c * c + d * d);
        l *= M, a *= M, c *= M, d *= M;
      }
    }
    e[t] = l, e[t + 1] = a, e[t + 2] = c, e[t + 3] = d;
  }
  static multiplyQuaternionsFlat(e, t, n, i, s, o) {
    const r = n[i], l = n[i + 1], a = n[i + 2], c = n[i + 3], d = s[o], u = s[o + 1], m = s[o + 2], g = s[o + 3];
    return e[t] = r * g + c * d + l * m - a * u, e[t + 1] = l * g + c * u + a * d - r * m, e[t + 2] = a * g + c * m + r * u - l * d, e[t + 3] = c * g - r * d - l * u - a * m, e;
  }
  get x() {
    return this._x;
  }
  set x(e) {
    this._x = e, this._onChangeCallback();
  }
  get y() {
    return this._y;
  }
  set y(e) {
    this._y = e, this._onChangeCallback();
  }
  get z() {
    return this._z;
  }
  set z(e) {
    this._z = e, this._onChangeCallback();
  }
  get w() {
    return this._w;
  }
  set w(e) {
    this._w = e, this._onChangeCallback();
  }
  set(e, t, n, i) {
    return this._x = e, this._y = t, this._z = n, this._w = i, this._onChangeCallback(), this;
  }
  clone() {
    return new this.constructor(this._x, this._y, this._z, this._w);
  }
  copy(e) {
    return this._x = e.x, this._y = e.y, this._z = e.z, this._w = e.w, this._onChangeCallback(), this;
  }
  setFromEuler(e, t) {
    if (!(e && e.isEuler))
      throw new Error("THREE.Quaternion: .setFromEuler() now expects an Euler rotation rather than a Vector3 and order.");
    const n = e._x, i = e._y, s = e._z, o = e._order, r = Math.cos, l = Math.sin, a = r(n / 2), c = r(i / 2), d = r(s / 2), u = l(n / 2), m = l(i / 2), g = l(s / 2);
    switch (o) {
      case "XYZ":
        this._x = u * c * d + a * m * g, this._y = a * m * d - u * c * g, this._z = a * c * g + u * m * d, this._w = a * c * d - u * m * g;
        break;
      case "YXZ":
        this._x = u * c * d + a * m * g, this._y = a * m * d - u * c * g, this._z = a * c * g - u * m * d, this._w = a * c * d + u * m * g;
        break;
      case "ZXY":
        this._x = u * c * d - a * m * g, this._y = a * m * d + u * c * g, this._z = a * c * g + u * m * d, this._w = a * c * d - u * m * g;
        break;
      case "ZYX":
        this._x = u * c * d - a * m * g, this._y = a * m * d + u * c * g, this._z = a * c * g - u * m * d, this._w = a * c * d + u * m * g;
        break;
      case "YZX":
        this._x = u * c * d + a * m * g, this._y = a * m * d + u * c * g, this._z = a * c * g - u * m * d, this._w = a * c * d - u * m * g;
        break;
      case "XZY":
        this._x = u * c * d - a * m * g, this._y = a * m * d - u * c * g, this._z = a * c * g + u * m * d, this._w = a * c * d + u * m * g;
        break;
      default:
        console.warn("THREE.Quaternion: .setFromEuler() encountered an unknown order: " + o);
    }
    return t !== !1 && this._onChangeCallback(), this;
  }
  setFromAxisAngle(e, t) {
    const n = t / 2, i = Math.sin(n);
    return this._x = e.x * i, this._y = e.y * i, this._z = e.z * i, this._w = Math.cos(n), this._onChangeCallback(), this;
  }
  setFromRotationMatrix(e) {
    const t = e.elements, n = t[0], i = t[4], s = t[8], o = t[1], r = t[5], l = t[9], a = t[2], c = t[6], d = t[10], u = n + r + d;
    if (u > 0) {
      const m = 0.5 / Math.sqrt(u + 1);
      this._w = 0.25 / m, this._x = (c - l) * m, this._y = (s - a) * m, this._z = (o - i) * m;
    } else if (n > r && n > d) {
      const m = 2 * Math.sqrt(1 + n - r - d);
      this._w = (c - l) / m, this._x = 0.25 * m, this._y = (i + o) / m, this._z = (s + a) / m;
    } else if (r > d) {
      const m = 2 * Math.sqrt(1 + r - n - d);
      this._w = (s - a) / m, this._x = (i + o) / m, this._y = 0.25 * m, this._z = (l + c) / m;
    } else {
      const m = 2 * Math.sqrt(1 + d - n - r);
      this._w = (o - i) / m, this._x = (s + a) / m, this._y = (l + c) / m, this._z = 0.25 * m;
    }
    return this._onChangeCallback(), this;
  }
  setFromUnitVectors(e, t) {
    let n = e.dot(t) + 1;
    return n < Number.EPSILON ? (n = 0, Math.abs(e.x) > Math.abs(e.z) ? (this._x = -e.y, this._y = e.x, this._z = 0, this._w = n) : (this._x = 0, this._y = -e.z, this._z = e.y, this._w = n)) : (this._x = e.y * t.z - e.z * t.y, this._y = e.z * t.x - e.x * t.z, this._z = e.x * t.y - e.y * t.x, this._w = n), this.normalize();
  }
  angleTo(e) {
    return 2 * Math.acos(Math.abs(mt(this.dot(e), -1, 1)));
  }
  rotateTowards(e, t) {
    const n = this.angleTo(e);
    if (n === 0)
      return this;
    const i = Math.min(1, t / n);
    return this.slerp(e, i), this;
  }
  identity() {
    return this.set(0, 0, 0, 1);
  }
  invert() {
    return this.conjugate();
  }
  conjugate() {
    return this._x *= -1, this._y *= -1, this._z *= -1, this._onChangeCallback(), this;
  }
  dot(e) {
    return this._x * e._x + this._y * e._y + this._z * e._z + this._w * e._w;
  }
  lengthSq() {
    return this._x * this._x + this._y * this._y + this._z * this._z + this._w * this._w;
  }
  length() {
    return Math.sqrt(this._x * this._x + this._y * this._y + this._z * this._z + this._w * this._w);
  }
  normalize() {
    let e = this.length();
    return e === 0 ? (this._x = 0, this._y = 0, this._z = 0, this._w = 1) : (e = 1 / e, this._x = this._x * e, this._y = this._y * e, this._z = this._z * e, this._w = this._w * e), this._onChangeCallback(), this;
  }
  multiply(e) {
    return this.multiplyQuaternions(this, e);
  }
  premultiply(e) {
    return this.multiplyQuaternions(e, this);
  }
  multiplyQuaternions(e, t) {
    const n = e._x, i = e._y, s = e._z, o = e._w, r = t._x, l = t._y, a = t._z, c = t._w;
    return this._x = n * c + o * r + i * a - s * l, this._y = i * c + o * l + s * r - n * a, this._z = s * c + o * a + n * l - i * r, this._w = o * c - n * r - i * l - s * a, this._onChangeCallback(), this;
  }
  slerp(e, t) {
    if (t === 0)
      return this;
    if (t === 1)
      return this.copy(e);
    const n = this._x, i = this._y, s = this._z, o = this._w;
    let r = o * e._w + n * e._x + i * e._y + s * e._z;
    if (r < 0 ? (this._w = -e._w, this._x = -e._x, this._y = -e._y, this._z = -e._z, r = -r) : this.copy(e), r >= 1)
      return this._w = o, this._x = n, this._y = i, this._z = s, this;
    const l = 1 - r * r;
    if (l <= Number.EPSILON) {
      const m = 1 - t;
      return this._w = m * o + t * this._w, this._x = m * n + t * this._x, this._y = m * i + t * this._y, this._z = m * s + t * this._z, this.normalize(), this._onChangeCallback(), this;
    }
    const a = Math.sqrt(l), c = Math.atan2(a, r), d = Math.sin((1 - t) * c) / a, u = Math.sin(t * c) / a;
    return this._w = o * d + this._w * u, this._x = n * d + this._x * u, this._y = i * d + this._y * u, this._z = s * d + this._z * u, this._onChangeCallback(), this;
  }
  slerpQuaternions(e, t, n) {
    return this.copy(e).slerp(t, n);
  }
  random() {
    const e = Math.random(), t = Math.sqrt(1 - e), n = Math.sqrt(e), i = 2 * Math.PI * Math.random(), s = 2 * Math.PI * Math.random();
    return this.set(
      t * Math.cos(i),
      n * Math.sin(s),
      n * Math.cos(s),
      t * Math.sin(i)
    );
  }
  equals(e) {
    return e._x === this._x && e._y === this._y && e._z === this._z && e._w === this._w;
  }
  fromArray(e, t = 0) {
    return this._x = e[t], this._y = e[t + 1], this._z = e[t + 2], this._w = e[t + 3], this._onChangeCallback(), this;
  }
  toArray(e = [], t = 0) {
    return e[t] = this._x, e[t + 1] = this._y, e[t + 2] = this._z, e[t + 3] = this._w, e;
  }
  fromBufferAttribute(e, t) {
    return this._x = e.getX(t), this._y = e.getY(t), this._z = e.getZ(t), this._w = e.getW(t), this;
  }
  _onChange(e) {
    return this._onChangeCallback = e, this;
  }
  _onChangeCallback() {
  }
  *[Symbol.iterator]() {
    yield this._x, yield this._y, yield this._z, yield this._w;
  }
}
class O {
  constructor(e = 0, t = 0, n = 0) {
    O.prototype.isVector3 = !0, this.x = e, this.y = t, this.z = n;
  }
  set(e, t, n) {
    return n === void 0 && (n = this.z), this.x = e, this.y = t, this.z = n, this;
  }
  setScalar(e) {
    return this.x = e, this.y = e, this.z = e, this;
  }
  setX(e) {
    return this.x = e, this;
  }
  setY(e) {
    return this.y = e, this;
  }
  setZ(e) {
    return this.z = e, this;
  }
  setComponent(e, t) {
    switch (e) {
      case 0:
        this.x = t;
        break;
      case 1:
        this.y = t;
        break;
      case 2:
        this.z = t;
        break;
      default:
        throw new Error("index is out of range: " + e);
    }
    return this;
  }
  getComponent(e) {
    switch (e) {
      case 0:
        return this.x;
      case 1:
        return this.y;
      case 2:
        return this.z;
      default:
        throw new Error("index is out of range: " + e);
    }
  }
  clone() {
    return new this.constructor(this.x, this.y, this.z);
  }
  copy(e) {
    return this.x = e.x, this.y = e.y, this.z = e.z, this;
  }
  add(e) {
    return this.x += e.x, this.y += e.y, this.z += e.z, this;
  }
  addScalar(e) {
    return this.x += e, this.y += e, this.z += e, this;
  }
  addVectors(e, t) {
    return this.x = e.x + t.x, this.y = e.y + t.y, this.z = e.z + t.z, this;
  }
  addScaledVector(e, t) {
    return this.x += e.x * t, this.y += e.y * t, this.z += e.z * t, this;
  }
  sub(e) {
    return this.x -= e.x, this.y -= e.y, this.z -= e.z, this;
  }
  subScalar(e) {
    return this.x -= e, this.y -= e, this.z -= e, this;
  }
  subVectors(e, t) {
    return this.x = e.x - t.x, this.y = e.y - t.y, this.z = e.z - t.z, this;
  }
  multiply(e) {
    return this.x *= e.x, this.y *= e.y, this.z *= e.z, this;
  }
  multiplyScalar(e) {
    return this.x *= e, this.y *= e, this.z *= e, this;
  }
  multiplyVectors(e, t) {
    return this.x = e.x * t.x, this.y = e.y * t.y, this.z = e.z * t.z, this;
  }
  applyEuler(e) {
    return this.applyQuaternion(Ks.setFromEuler(e));
  }
  applyAxisAngle(e, t) {
    return this.applyQuaternion(Ks.setFromAxisAngle(e, t));
  }
  applyMatrix3(e) {
    const t = this.x, n = this.y, i = this.z, s = e.elements;
    return this.x = s[0] * t + s[3] * n + s[6] * i, this.y = s[1] * t + s[4] * n + s[7] * i, this.z = s[2] * t + s[5] * n + s[8] * i, this;
  }
  applyNormalMatrix(e) {
    return this.applyMatrix3(e).normalize();
  }
  applyMatrix4(e) {
    const t = this.x, n = this.y, i = this.z, s = e.elements, o = 1 / (s[3] * t + s[7] * n + s[11] * i + s[15]);
    return this.x = (s[0] * t + s[4] * n + s[8] * i + s[12]) * o, this.y = (s[1] * t + s[5] * n + s[9] * i + s[13]) * o, this.z = (s[2] * t + s[6] * n + s[10] * i + s[14]) * o, this;
  }
  applyQuaternion(e) {
    const t = this.x, n = this.y, i = this.z, s = e.x, o = e.y, r = e.z, l = e.w, a = l * t + o * i - r * n, c = l * n + r * t - s * i, d = l * i + s * n - o * t, u = -s * t - o * n - r * i;
    return this.x = a * l + u * -s + c * -r - d * -o, this.y = c * l + u * -o + d * -s - a * -r, this.z = d * l + u * -r + a * -o - c * -s, this;
  }
  project(e) {
    return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix);
  }
  unproject(e) {
    return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld);
  }
  transformDirection(e) {
    const t = this.x, n = this.y, i = this.z, s = e.elements;
    return this.x = s[0] * t + s[4] * n + s[8] * i, this.y = s[1] * t + s[5] * n + s[9] * i, this.z = s[2] * t + s[6] * n + s[10] * i, this.normalize();
  }
  divide(e) {
    return this.x /= e.x, this.y /= e.y, this.z /= e.z, this;
  }
  divideScalar(e) {
    return this.multiplyScalar(1 / e);
  }
  min(e) {
    return this.x = Math.min(this.x, e.x), this.y = Math.min(this.y, e.y), this.z = Math.min(this.z, e.z), this;
  }
  max(e) {
    return this.x = Math.max(this.x, e.x), this.y = Math.max(this.y, e.y), this.z = Math.max(this.z, e.z), this;
  }
  clamp(e, t) {
    return this.x = Math.max(e.x, Math.min(t.x, this.x)), this.y = Math.max(e.y, Math.min(t.y, this.y)), this.z = Math.max(e.z, Math.min(t.z, this.z)), this;
  }
  clampScalar(e, t) {
    return this.x = Math.max(e, Math.min(t, this.x)), this.y = Math.max(e, Math.min(t, this.y)), this.z = Math.max(e, Math.min(t, this.z)), this;
  }
  clampLength(e, t) {
    const n = this.length();
    return this.divideScalar(n || 1).multiplyScalar(Math.max(e, Math.min(t, n)));
  }
  floor() {
    return this.x = Math.floor(this.x), this.y = Math.floor(this.y), this.z = Math.floor(this.z), this;
  }
  ceil() {
    return this.x = Math.ceil(this.x), this.y = Math.ceil(this.y), this.z = Math.ceil(this.z), this;
  }
  round() {
    return this.x = Math.round(this.x), this.y = Math.round(this.y), this.z = Math.round(this.z), this;
  }
  roundToZero() {
    return this.x = this.x < 0 ? Math.ceil(this.x) : Math.floor(this.x), this.y = this.y < 0 ? Math.ceil(this.y) : Math.floor(this.y), this.z = this.z < 0 ? Math.ceil(this.z) : Math.floor(this.z), this;
  }
  negate() {
    return this.x = -this.x, this.y = -this.y, this.z = -this.z, this;
  }
  dot(e) {
    return this.x * e.x + this.y * e.y + this.z * e.z;
  }
  lengthSq() {
    return this.x * this.x + this.y * this.y + this.z * this.z;
  }
  length() {
    return Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z);
  }
  manhattanLength() {
    return Math.abs(this.x) + Math.abs(this.y) + Math.abs(this.z);
  }
  normalize() {
    return this.divideScalar(this.length() || 1);
  }
  setLength(e) {
    return this.normalize().multiplyScalar(e);
  }
  lerp(e, t) {
    return this.x += (e.x - this.x) * t, this.y += (e.y - this.y) * t, this.z += (e.z - this.z) * t, this;
  }
  lerpVectors(e, t, n) {
    return this.x = e.x + (t.x - e.x) * n, this.y = e.y + (t.y - e.y) * n, this.z = e.z + (t.z - e.z) * n, this;
  }
  cross(e) {
    return this.crossVectors(this, e);
  }
  crossVectors(e, t) {
    const n = e.x, i = e.y, s = e.z, o = t.x, r = t.y, l = t.z;
    return this.x = i * l - s * r, this.y = s * o - n * l, this.z = n * r - i * o, this;
  }
  projectOnVector(e) {
    const t = e.lengthSq();
    if (t === 0)
      return this.set(0, 0, 0);
    const n = e.dot(this) / t;
    return this.copy(e).multiplyScalar(n);
  }
  projectOnPlane(e) {
    return ss.copy(this).projectOnVector(e), this.sub(ss);
  }
  reflect(e) {
    return this.sub(ss.copy(e).multiplyScalar(2 * this.dot(e)));
  }
  angleTo(e) {
    const t = Math.sqrt(this.lengthSq() * e.lengthSq());
    if (t === 0)
      return Math.PI / 2;
    const n = this.dot(e) / t;
    return Math.acos(mt(n, -1, 1));
  }
  distanceTo(e) {
    return Math.sqrt(this.distanceToSquared(e));
  }
  distanceToSquared(e) {
    const t = this.x - e.x, n = this.y - e.y, i = this.z - e.z;
    return t * t + n * n + i * i;
  }
  manhattanDistanceTo(e) {
    return Math.abs(this.x - e.x) + Math.abs(this.y - e.y) + Math.abs(this.z - e.z);
  }
  setFromSpherical(e) {
    return this.setFromSphericalCoords(e.radius, e.phi, e.theta);
  }
  setFromSphericalCoords(e, t, n) {
    const i = Math.sin(t) * e;
    return this.x = i * Math.sin(n), this.y = Math.cos(t) * e, this.z = i * Math.cos(n), this;
  }
  setFromCylindrical(e) {
    return this.setFromCylindricalCoords(e.radius, e.theta, e.y);
  }
  setFromCylindricalCoords(e, t, n) {
    return this.x = e * Math.sin(t), this.y = n, this.z = e * Math.cos(t), this;
  }
  setFromMatrixPosition(e) {
    const t = e.elements;
    return this.x = t[12], this.y = t[13], this.z = t[14], this;
  }
  setFromMatrixScale(e) {
    const t = this.setFromMatrixColumn(e, 0).length(), n = this.setFromMatrixColumn(e, 1).length(), i = this.setFromMatrixColumn(e, 2).length();
    return this.x = t, this.y = n, this.z = i, this;
  }
  setFromMatrixColumn(e, t) {
    return this.fromArray(e.elements, t * 4);
  }
  setFromMatrix3Column(e, t) {
    return this.fromArray(e.elements, t * 3);
  }
  setFromEuler(e) {
    return this.x = e._x, this.y = e._y, this.z = e._z, this;
  }
  equals(e) {
    return e.x === this.x && e.y === this.y && e.z === this.z;
  }
  fromArray(e, t = 0) {
    return this.x = e[t], this.y = e[t + 1], this.z = e[t + 2], this;
  }
  toArray(e = [], t = 0) {
    return e[t] = this.x, e[t + 1] = this.y, e[t + 2] = this.z, e;
  }
  fromBufferAttribute(e, t) {
    return this.x = e.getX(t), this.y = e.getY(t), this.z = e.getZ(t), this;
  }
  random() {
    return this.x = Math.random(), this.y = Math.random(), this.z = Math.random(), this;
  }
  randomDirection() {
    const e = (Math.random() - 0.5) * 2, t = Math.random() * Math.PI * 2, n = Math.sqrt(1 - e ** 2);
    return this.x = n * Math.cos(t), this.y = n * Math.sin(t), this.z = e, this;
  }
  *[Symbol.iterator]() {
    yield this.x, yield this.y, yield this.z;
  }
}
const ss = /* @__PURE__ */ new O(), Ks = /* @__PURE__ */ new ui();
class di {
  constructor(e = new O(1 / 0, 1 / 0, 1 / 0), t = new O(-1 / 0, -1 / 0, -1 / 0)) {
    this.isBox3 = !0, this.min = e, this.max = t;
  }
  set(e, t) {
    return this.min.copy(e), this.max.copy(t), this;
  }
  setFromArray(e) {
    let t = 1 / 0, n = 1 / 0, i = 1 / 0, s = -1 / 0, o = -1 / 0, r = -1 / 0;
    for (let l = 0, a = e.length; l < a; l += 3) {
      const c = e[l], d = e[l + 1], u = e[l + 2];
      c < t && (t = c), d < n && (n = d), u < i && (i = u), c > s && (s = c), d > o && (o = d), u > r && (r = u);
    }
    return this.min.set(t, n, i), this.max.set(s, o, r), this;
  }
  setFromBufferAttribute(e) {
    let t = 1 / 0, n = 1 / 0, i = 1 / 0, s = -1 / 0, o = -1 / 0, r = -1 / 0;
    for (let l = 0, a = e.count; l < a; l++) {
      const c = e.getX(l), d = e.getY(l), u = e.getZ(l);
      c < t && (t = c), d < n && (n = d), u < i && (i = u), c > s && (s = c), d > o && (o = d), u > r && (r = u);
    }
    return this.min.set(t, n, i), this.max.set(s, o, r), this;
  }
  setFromPoints(e) {
    this.makeEmpty();
    for (let t = 0, n = e.length; t < n; t++)
      this.expandByPoint(e[t]);
    return this;
  }
  setFromCenterAndSize(e, t) {
    const n = dn.copy(t).multiplyScalar(0.5);
    return this.min.copy(e).sub(n), this.max.copy(e).add(n), this;
  }
  setFromObject(e, t = !1) {
    return this.makeEmpty(), this.expandByObject(e, t);
  }
  clone() {
    return new this.constructor().copy(this);
  }
  copy(e) {
    return this.min.copy(e.min), this.max.copy(e.max), this;
  }
  makeEmpty() {
    return this.min.x = this.min.y = this.min.z = 1 / 0, this.max.x = this.max.y = this.max.z = -1 / 0, this;
  }
  isEmpty() {
    return this.max.x < this.min.x || this.max.y < this.min.y || this.max.z < this.min.z;
  }
  getCenter(e) {
    return this.isEmpty() ? e.set(0, 0, 0) : e.addVectors(this.min, this.max).multiplyScalar(0.5);
  }
  getSize(e) {
    return this.isEmpty() ? e.set(0, 0, 0) : e.subVectors(this.max, this.min);
  }
  expandByPoint(e) {
    return this.min.min(e), this.max.max(e), this;
  }
  expandByVector(e) {
    return this.min.sub(e), this.max.add(e), this;
  }
  expandByScalar(e) {
    return this.min.addScalar(-e), this.max.addScalar(e), this;
  }
  expandByObject(e, t = !1) {
    e.updateWorldMatrix(!1, !1);
    const n = e.geometry;
    if (n !== void 0)
      if (t && n.attributes != null && n.attributes.position !== void 0) {
        const s = n.attributes.position;
        for (let o = 0, r = s.count; o < r; o++)
          dn.fromBufferAttribute(s, o).applyMatrix4(e.matrixWorld), this.expandByPoint(dn);
      } else
        n.boundingBox === null && n.computeBoundingBox(), rs.copy(n.boundingBox), rs.applyMatrix4(e.matrixWorld), this.union(rs);
    const i = e.children;
    for (let s = 0, o = i.length; s < o; s++)
      this.expandByObject(i[s], t);
    return this;
  }
  containsPoint(e) {
    return !(e.x < this.min.x || e.x > this.max.x || e.y < this.min.y || e.y > this.max.y || e.z < this.min.z || e.z > this.max.z);
  }
  containsBox(e) {
    return this.min.x <= e.min.x && e.max.x <= this.max.x && this.min.y <= e.min.y && e.max.y <= this.max.y && this.min.z <= e.min.z && e.max.z <= this.max.z;
  }
  getParameter(e, t) {
    return t.set(
      (e.x - this.min.x) / (this.max.x - this.min.x),
      (e.y - this.min.y) / (this.max.y - this.min.y),
      (e.z - this.min.z) / (this.max.z - this.min.z)
    );
  }
  intersectsBox(e) {
    return !(e.max.x < this.min.x || e.min.x > this.max.x || e.max.y < this.min.y || e.min.y > this.max.y || e.max.z < this.min.z || e.min.z > this.max.z);
  }
  intersectsSphere(e) {
    return this.clampPoint(e.center, dn), dn.distanceToSquared(e.center) <= e.radius * e.radius;
  }
  intersectsPlane(e) {
    let t, n;
    return e.normal.x > 0 ? (t = e.normal.x * this.min.x, n = e.normal.x * this.max.x) : (t = e.normal.x * this.max.x, n = e.normal.x * this.min.x), e.normal.y > 0 ? (t += e.normal.y * this.min.y, n += e.normal.y * this.max.y) : (t += e.normal.y * this.max.y, n += e.normal.y * this.min.y), e.normal.z > 0 ? (t += e.normal.z * this.min.z, n += e.normal.z * this.max.z) : (t += e.normal.z * this.max.z, n += e.normal.z * this.min.z), t <= -e.constant && n >= -e.constant;
  }
  intersectsTriangle(e) {
    if (this.isEmpty())
      return !1;
    this.getCenter(ei), vi.subVectors(this.max, ei), Dn.subVectors(e.a, ei), Pn.subVectors(e.b, ei), In.subVectors(e.c, ei), nn.subVectors(Pn, Dn), sn.subVectors(In, Pn), fn.subVectors(Dn, In);
    let t = [
      0,
      -nn.z,
      nn.y,
      0,
      -sn.z,
      sn.y,
      0,
      -fn.z,
      fn.y,
      nn.z,
      0,
      -nn.x,
      sn.z,
      0,
      -sn.x,
      fn.z,
      0,
      -fn.x,
      -nn.y,
      nn.x,
      0,
      -sn.y,
      sn.x,
      0,
      -fn.y,
      fn.x,
      0
    ];
    return !os(t, Dn, Pn, In, vi) || (t = [1, 0, 0, 0, 1, 0, 0, 0, 1], !os(t, Dn, Pn, In, vi)) ? !1 : (xi.crossVectors(nn, sn), t = [xi.x, xi.y, xi.z], os(t, Dn, Pn, In, vi));
  }
  clampPoint(e, t) {
    return t.copy(e).clamp(this.min, this.max);
  }
  distanceToPoint(e) {
    return dn.copy(e).clamp(this.min, this.max).sub(e).length();
  }
  getBoundingSphere(e) {
    return this.getCenter(e.center), e.radius = this.getSize(dn).length() * 0.5, e;
  }
  intersect(e) {
    return this.min.max(e.min), this.max.min(e.max), this.isEmpty() && this.makeEmpty(), this;
  }
  union(e) {
    return this.min.min(e.min), this.max.max(e.max), this;
  }
  applyMatrix4(e) {
    return this.isEmpty() ? this : (Wt[0].set(this.min.x, this.min.y, this.min.z).applyMatrix4(e), Wt[1].set(this.min.x, this.min.y, this.max.z).applyMatrix4(e), Wt[2].set(this.min.x, this.max.y, this.min.z).applyMatrix4(e), Wt[3].set(this.min.x, this.max.y, this.max.z).applyMatrix4(e), Wt[4].set(this.max.x, this.min.y, this.min.z).applyMatrix4(e), Wt[5].set(this.max.x, this.min.y, this.max.z).applyMatrix4(e), Wt[6].set(this.max.x, this.max.y, this.min.z).applyMatrix4(e), Wt[7].set(this.max.x, this.max.y, this.max.z).applyMatrix4(e), this.setFromPoints(Wt), this);
  }
  translate(e) {
    return this.min.add(e), this.max.add(e), this;
  }
  equals(e) {
    return e.min.equals(this.min) && e.max.equals(this.max);
  }
}
const Wt = [
  /* @__PURE__ */ new O(),
  /* @__PURE__ */ new O(),
  /* @__PURE__ */ new O(),
  /* @__PURE__ */ new O(),
  /* @__PURE__ */ new O(),
  /* @__PURE__ */ new O(),
  /* @__PURE__ */ new O(),
  /* @__PURE__ */ new O()
], dn = /* @__PURE__ */ new O(), rs = /* @__PURE__ */ new di(), Dn = /* @__PURE__ */ new O(), Pn = /* @__PURE__ */ new O(), In = /* @__PURE__ */ new O(), nn = /* @__PURE__ */ new O(), sn = /* @__PURE__ */ new O(), fn = /* @__PURE__ */ new O(), ei = /* @__PURE__ */ new O(), vi = /* @__PURE__ */ new O(), xi = /* @__PURE__ */ new O(), pn = /* @__PURE__ */ new O();
function os(h, e, t, n, i) {
  for (let s = 0, o = h.length - 3; s <= o; s += 3) {
    pn.fromArray(h, s);
    const r = i.x * Math.abs(pn.x) + i.y * Math.abs(pn.y) + i.z * Math.abs(pn.z), l = e.dot(pn), a = t.dot(pn), c = n.dot(pn);
    if (Math.max(-Math.max(l, a, c), Math.min(l, a, c)) > r)
      return !1;
  }
  return !0;
}
const Go = /* @__PURE__ */ new di(), Js = /* @__PURE__ */ new O(), yi = /* @__PURE__ */ new O(), as = /* @__PURE__ */ new O();
class ci {
  constructor(e = new O(), t = -1) {
    this.center = e, this.radius = t;
  }
  set(e, t) {
    return this.center.copy(e), this.radius = t, this;
  }
  setFromPoints(e, t) {
    const n = this.center;
    t !== void 0 ? n.copy(t) : Go.setFromPoints(e).getCenter(n);
    let i = 0;
    for (let s = 0, o = e.length; s < o; s++)
      i = Math.max(i, n.distanceToSquared(e[s]));
    return this.radius = Math.sqrt(i), this;
  }
  copy(e) {
    return this.center.copy(e.center), this.radius = e.radius, this;
  }
  isEmpty() {
    return this.radius < 0;
  }
  makeEmpty() {
    return this.center.set(0, 0, 0), this.radius = -1, this;
  }
  containsPoint(e) {
    return e.distanceToSquared(this.center) <= this.radius * this.radius;
  }
  distanceToPoint(e) {
    return e.distanceTo(this.center) - this.radius;
  }
  intersectsSphere(e) {
    const t = this.radius + e.radius;
    return e.center.distanceToSquared(this.center) <= t * t;
  }
  intersectsBox(e) {
    return e.intersectsSphere(this);
  }
  intersectsPlane(e) {
    return Math.abs(e.distanceToPoint(this.center)) <= this.radius;
  }
  clampPoint(e, t) {
    const n = this.center.distanceToSquared(e);
    return t.copy(e), n > this.radius * this.radius && (t.sub(this.center).normalize(), t.multiplyScalar(this.radius).add(this.center)), t;
  }
  getBoundingBox(e) {
    return this.isEmpty() ? (e.makeEmpty(), e) : (e.set(this.center, this.center), e.expandByScalar(this.radius), e);
  }
  applyMatrix4(e) {
    return this.center.applyMatrix4(e), this.radius = this.radius * e.getMaxScaleOnAxis(), this;
  }
  translate(e) {
    return this.center.add(e), this;
  }
  expandByPoint(e) {
    as.subVectors(e, this.center);
    const t = as.lengthSq();
    if (t > this.radius * this.radius) {
      const n = Math.sqrt(t), i = (n - this.radius) * 0.5;
      this.center.add(as.multiplyScalar(i / n)), this.radius += i;
    }
    return this;
  }
  union(e) {
    return this.center.equals(e.center) === !0 ? yi.set(0, 0, 1).multiplyScalar(e.radius) : yi.subVectors(e.center, this.center).normalize().multiplyScalar(e.radius), this.expandByPoint(Js.copy(e.center).add(yi)), this.expandByPoint(Js.copy(e.center).sub(yi)), this;
  }
  equals(e) {
    return e.center.equals(this.center) && e.radius === this.radius;
  }
  clone() {
    return new this.constructor().copy(this);
  }
}
const Vt = /* @__PURE__ */ new O(), ls = /* @__PURE__ */ new O(), bi = /* @__PURE__ */ new O(), rn = /* @__PURE__ */ new O(), cs = /* @__PURE__ */ new O(), wi = /* @__PURE__ */ new O(), hs = /* @__PURE__ */ new O();
class ko {
  constructor(e = new O(), t = new O(0, 0, -1)) {
    this.origin = e, this.direction = t;
  }
  set(e, t) {
    return this.origin.copy(e), this.direction.copy(t), this;
  }
  copy(e) {
    return this.origin.copy(e.origin), this.direction.copy(e.direction), this;
  }
  at(e, t) {
    return t.copy(this.direction).multiplyScalar(e).add(this.origin);
  }
  lookAt(e) {
    return this.direction.copy(e).sub(this.origin).normalize(), this;
  }
  recast(e) {
    return this.origin.copy(this.at(e, Vt)), this;
  }
  closestPointToPoint(e, t) {
    t.subVectors(e, this.origin);
    const n = t.dot(this.direction);
    return n < 0 ? t.copy(this.origin) : t.copy(this.direction).multiplyScalar(n).add(this.origin);
  }
  distanceToPoint(e) {
    return Math.sqrt(this.distanceSqToPoint(e));
  }
  distanceSqToPoint(e) {
    const t = Vt.subVectors(e, this.origin).dot(this.direction);
    return t < 0 ? this.origin.distanceToSquared(e) : (Vt.copy(this.direction).multiplyScalar(t).add(this.origin), Vt.distanceToSquared(e));
  }
  distanceSqToSegment(e, t, n, i) {
    ls.copy(e).add(t).multiplyScalar(0.5), bi.copy(t).sub(e).normalize(), rn.copy(this.origin).sub(ls);
    const s = e.distanceTo(t) * 0.5, o = -this.direction.dot(bi), r = rn.dot(this.direction), l = -rn.dot(bi), a = rn.lengthSq(), c = Math.abs(1 - o * o);
    let d, u, m, g;
    if (c > 0)
      if (d = o * l - r, u = o * r - l, g = s * c, d >= 0)
        if (u >= -g)
          if (u <= g) {
            const p = 1 / c;
            d *= p, u *= p, m = d * (d + o * u + 2 * r) + u * (o * d + u + 2 * l) + a;
          } else
            u = s, d = Math.max(0, -(o * u + r)), m = -d * d + u * (u + 2 * l) + a;
        else
          u = -s, d = Math.max(0, -(o * u + r)), m = -d * d + u * (u + 2 * l) + a;
      else
        u <= -g ? (d = Math.max(0, -(-o * s + r)), u = d > 0 ? -s : Math.min(Math.max(-s, -l), s), m = -d * d + u * (u + 2 * l) + a) : u <= g ? (d = 0, u = Math.min(Math.max(-s, -l), s), m = u * (u + 2 * l) + a) : (d = Math.max(0, -(o * s + r)), u = d > 0 ? s : Math.min(Math.max(-s, -l), s), m = -d * d + u * (u + 2 * l) + a);
    else
      u = o > 0 ? -s : s, d = Math.max(0, -(o * u + r)), m = -d * d + u * (u + 2 * l) + a;
    return n && n.copy(this.direction).multiplyScalar(d).add(this.origin), i && i.copy(bi).multiplyScalar(u).add(ls), m;
  }
  intersectSphere(e, t) {
    Vt.subVectors(e.center, this.origin);
    const n = Vt.dot(this.direction), i = Vt.dot(Vt) - n * n, s = e.radius * e.radius;
    if (i > s)
      return null;
    const o = Math.sqrt(s - i), r = n - o, l = n + o;
    return r < 0 && l < 0 ? null : r < 0 ? this.at(l, t) : this.at(r, t);
  }
  intersectsSphere(e) {
    return this.distanceSqToPoint(e.center) <= e.radius * e.radius;
  }
  distanceToPlane(e) {
    const t = e.normal.dot(this.direction);
    if (t === 0)
      return e.distanceToPoint(this.origin) === 0 ? 0 : null;
    const n = -(this.origin.dot(e.normal) + e.constant) / t;
    return n >= 0 ? n : null;
  }
  intersectPlane(e, t) {
    const n = this.distanceToPlane(e);
    return n === null ? null : this.at(n, t);
  }
  intersectsPlane(e) {
    const t = e.distanceToPoint(this.origin);
    return t === 0 || e.normal.dot(this.direction) * t < 0;
  }
  intersectBox(e, t) {
    let n, i, s, o, r, l;
    const a = 1 / this.direction.x, c = 1 / this.direction.y, d = 1 / this.direction.z, u = this.origin;
    return a >= 0 ? (n = (e.min.x - u.x) * a, i = (e.max.x - u.x) * a) : (n = (e.max.x - u.x) * a, i = (e.min.x - u.x) * a), c >= 0 ? (s = (e.min.y - u.y) * c, o = (e.max.y - u.y) * c) : (s = (e.max.y - u.y) * c, o = (e.min.y - u.y) * c), n > o || s > i || ((s > n || n !== n) && (n = s), (o < i || i !== i) && (i = o), d >= 0 ? (r = (e.min.z - u.z) * d, l = (e.max.z - u.z) * d) : (r = (e.max.z - u.z) * d, l = (e.min.z - u.z) * d), n > l || r > i) || ((r > n || n !== n) && (n = r), (l < i || i !== i) && (i = l), i < 0) ? null : this.at(n >= 0 ? n : i, t);
  }
  intersectsBox(e) {
    return this.intersectBox(e, Vt) !== null;
  }
  intersectTriangle(e, t, n, i, s) {
    cs.subVectors(t, e), wi.subVectors(n, e), hs.crossVectors(cs, wi);
    let o = this.direction.dot(hs), r;
    if (o > 0) {
      if (i)
        return null;
      r = 1;
    } else if (o < 0)
      r = -1, o = -o;
    else
      return null;
    rn.subVectors(this.origin, e);
    const l = r * this.direction.dot(wi.crossVectors(rn, wi));
    if (l < 0)
      return null;
    const a = r * this.direction.dot(cs.cross(rn));
    if (a < 0 || l + a > o)
      return null;
    const c = -r * rn.dot(hs);
    return c < 0 ? null : this.at(c / o, s);
  }
  applyMatrix4(e) {
    return this.origin.applyMatrix4(e), this.direction.transformDirection(e), this;
  }
  equals(e) {
    return e.origin.equals(this.origin) && e.direction.equals(this.direction);
  }
  clone() {
    return new this.constructor().copy(this);
  }
}
class Ke {
  constructor() {
    Ke.prototype.isMatrix4 = !0, this.elements = [
      1,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      1
    ];
  }
  set(e, t, n, i, s, o, r, l, a, c, d, u, m, g, p, f) {
    const v = this.elements;
    return v[0] = e, v[4] = t, v[8] = n, v[12] = i, v[1] = s, v[5] = o, v[9] = r, v[13] = l, v[2] = a, v[6] = c, v[10] = d, v[14] = u, v[3] = m, v[7] = g, v[11] = p, v[15] = f, this;
  }
  identity() {
    return this.set(
      1,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  clone() {
    return new Ke().fromArray(this.elements);
  }
  copy(e) {
    const t = this.elements, n = e.elements;
    return t[0] = n[0], t[1] = n[1], t[2] = n[2], t[3] = n[3], t[4] = n[4], t[5] = n[5], t[6] = n[6], t[7] = n[7], t[8] = n[8], t[9] = n[9], t[10] = n[10], t[11] = n[11], t[12] = n[12], t[13] = n[13], t[14] = n[14], t[15] = n[15], this;
  }
  copyPosition(e) {
    const t = this.elements, n = e.elements;
    return t[12] = n[12], t[13] = n[13], t[14] = n[14], this;
  }
  setFromMatrix3(e) {
    const t = e.elements;
    return this.set(
      t[0],
      t[3],
      t[6],
      0,
      t[1],
      t[4],
      t[7],
      0,
      t[2],
      t[5],
      t[8],
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  extractBasis(e, t, n) {
    return e.setFromMatrixColumn(this, 0), t.setFromMatrixColumn(this, 1), n.setFromMatrixColumn(this, 2), this;
  }
  makeBasis(e, t, n) {
    return this.set(
      e.x,
      t.x,
      n.x,
      0,
      e.y,
      t.y,
      n.y,
      0,
      e.z,
      t.z,
      n.z,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  extractRotation(e) {
    const t = this.elements, n = e.elements, i = 1 / zn.setFromMatrixColumn(e, 0).length(), s = 1 / zn.setFromMatrixColumn(e, 1).length(), o = 1 / zn.setFromMatrixColumn(e, 2).length();
    return t[0] = n[0] * i, t[1] = n[1] * i, t[2] = n[2] * i, t[3] = 0, t[4] = n[4] * s, t[5] = n[5] * s, t[6] = n[6] * s, t[7] = 0, t[8] = n[8] * o, t[9] = n[9] * o, t[10] = n[10] * o, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, this;
  }
  makeRotationFromEuler(e) {
    const t = this.elements, n = e.x, i = e.y, s = e.z, o = Math.cos(n), r = Math.sin(n), l = Math.cos(i), a = Math.sin(i), c = Math.cos(s), d = Math.sin(s);
    if (e.order === "XYZ") {
      const u = o * c, m = o * d, g = r * c, p = r * d;
      t[0] = l * c, t[4] = -l * d, t[8] = a, t[1] = m + g * a, t[5] = u - p * a, t[9] = -r * l, t[2] = p - u * a, t[6] = g + m * a, t[10] = o * l;
    } else if (e.order === "YXZ") {
      const u = l * c, m = l * d, g = a * c, p = a * d;
      t[0] = u + p * r, t[4] = g * r - m, t[8] = o * a, t[1] = o * d, t[5] = o * c, t[9] = -r, t[2] = m * r - g, t[6] = p + u * r, t[10] = o * l;
    } else if (e.order === "ZXY") {
      const u = l * c, m = l * d, g = a * c, p = a * d;
      t[0] = u - p * r, t[4] = -o * d, t[8] = g + m * r, t[1] = m + g * r, t[5] = o * c, t[9] = p - u * r, t[2] = -o * a, t[6] = r, t[10] = o * l;
    } else if (e.order === "ZYX") {
      const u = o * c, m = o * d, g = r * c, p = r * d;
      t[0] = l * c, t[4] = g * a - m, t[8] = u * a + p, t[1] = l * d, t[5] = p * a + u, t[9] = m * a - g, t[2] = -a, t[6] = r * l, t[10] = o * l;
    } else if (e.order === "YZX") {
      const u = o * l, m = o * a, g = r * l, p = r * a;
      t[0] = l * c, t[4] = p - u * d, t[8] = g * d + m, t[1] = d, t[5] = o * c, t[9] = -r * c, t[2] = -a * c, t[6] = m * d + g, t[10] = u - p * d;
    } else if (e.order === "XZY") {
      const u = o * l, m = o * a, g = r * l, p = r * a;
      t[0] = l * c, t[4] = -d, t[8] = a * c, t[1] = u * d + p, t[5] = o * c, t[9] = m * d - g, t[2] = g * d - m, t[6] = r * c, t[10] = p * d + u;
    }
    return t[3] = 0, t[7] = 0, t[11] = 0, t[12] = 0, t[13] = 0, t[14] = 0, t[15] = 1, this;
  }
  makeRotationFromQuaternion(e) {
    return this.compose(Wo, e, Vo);
  }
  lookAt(e, t, n) {
    const i = this.elements;
    return ft.subVectors(e, t), ft.lengthSq() === 0 && (ft.z = 1), ft.normalize(), on.crossVectors(n, ft), on.lengthSq() === 0 && (Math.abs(n.z) === 1 ? ft.x += 1e-4 : ft.z += 1e-4, ft.normalize(), on.crossVectors(n, ft)), on.normalize(), Mi.crossVectors(ft, on), i[0] = on.x, i[4] = Mi.x, i[8] = ft.x, i[1] = on.y, i[5] = Mi.y, i[9] = ft.y, i[2] = on.z, i[6] = Mi.z, i[10] = ft.z, this;
  }
  multiply(e) {
    return this.multiplyMatrices(this, e);
  }
  premultiply(e) {
    return this.multiplyMatrices(e, this);
  }
  multiplyMatrices(e, t) {
    const n = e.elements, i = t.elements, s = this.elements, o = n[0], r = n[4], l = n[8], a = n[12], c = n[1], d = n[5], u = n[9], m = n[13], g = n[2], p = n[6], f = n[10], v = n[14], _ = n[3], w = n[7], x = n[11], M = n[15], E = i[0], R = i[4], y = i[8], A = i[12], F = i[1], P = i[5], G = i[9], z = i[13], L = i[2], I = i[6], D = i[10], q = i[14], k = i[3], N = i[7], H = i[11], J = i[15];
    return s[0] = o * E + r * F + l * L + a * k, s[4] = o * R + r * P + l * I + a * N, s[8] = o * y + r * G + l * D + a * H, s[12] = o * A + r * z + l * q + a * J, s[1] = c * E + d * F + u * L + m * k, s[5] = c * R + d * P + u * I + m * N, s[9] = c * y + d * G + u * D + m * H, s[13] = c * A + d * z + u * q + m * J, s[2] = g * E + p * F + f * L + v * k, s[6] = g * R + p * P + f * I + v * N, s[10] = g * y + p * G + f * D + v * H, s[14] = g * A + p * z + f * q + v * J, s[3] = _ * E + w * F + x * L + M * k, s[7] = _ * R + w * P + x * I + M * N, s[11] = _ * y + w * G + x * D + M * H, s[15] = _ * A + w * z + x * q + M * J, this;
  }
  multiplyScalar(e) {
    const t = this.elements;
    return t[0] *= e, t[4] *= e, t[8] *= e, t[12] *= e, t[1] *= e, t[5] *= e, t[9] *= e, t[13] *= e, t[2] *= e, t[6] *= e, t[10] *= e, t[14] *= e, t[3] *= e, t[7] *= e, t[11] *= e, t[15] *= e, this;
  }
  determinant() {
    const e = this.elements, t = e[0], n = e[4], i = e[8], s = e[12], o = e[1], r = e[5], l = e[9], a = e[13], c = e[2], d = e[6], u = e[10], m = e[14], g = e[3], p = e[7], f = e[11], v = e[15];
    return g * (+s * l * d - i * a * d - s * r * u + n * a * u + i * r * m - n * l * m) + p * (+t * l * m - t * a * u + s * o * u - i * o * m + i * a * c - s * l * c) + f * (+t * a * d - t * r * m - s * o * d + n * o * m + s * r * c - n * a * c) + v * (-i * r * c - t * l * d + t * r * u + i * o * d - n * o * u + n * l * c);
  }
  transpose() {
    const e = this.elements;
    let t;
    return t = e[1], e[1] = e[4], e[4] = t, t = e[2], e[2] = e[8], e[8] = t, t = e[6], e[6] = e[9], e[9] = t, t = e[3], e[3] = e[12], e[12] = t, t = e[7], e[7] = e[13], e[13] = t, t = e[11], e[11] = e[14], e[14] = t, this;
  }
  setPosition(e, t, n) {
    const i = this.elements;
    return e.isVector3 ? (i[12] = e.x, i[13] = e.y, i[14] = e.z) : (i[12] = e, i[13] = t, i[14] = n), this;
  }
  invert() {
    const e = this.elements, t = e[0], n = e[1], i = e[2], s = e[3], o = e[4], r = e[5], l = e[6], a = e[7], c = e[8], d = e[9], u = e[10], m = e[11], g = e[12], p = e[13], f = e[14], v = e[15], _ = d * f * a - p * u * a + p * l * m - r * f * m - d * l * v + r * u * v, w = g * u * a - c * f * a - g * l * m + o * f * m + c * l * v - o * u * v, x = c * p * a - g * d * a + g * r * m - o * p * m - c * r * v + o * d * v, M = g * d * l - c * p * l - g * r * u + o * p * u + c * r * f - o * d * f, E = t * _ + n * w + i * x + s * M;
    if (E === 0)
      return this.set(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
    const R = 1 / E;
    return e[0] = _ * R, e[1] = (p * u * s - d * f * s - p * i * m + n * f * m + d * i * v - n * u * v) * R, e[2] = (r * f * s - p * l * s + p * i * a - n * f * a - r * i * v + n * l * v) * R, e[3] = (d * l * s - r * u * s - d * i * a + n * u * a + r * i * m - n * l * m) * R, e[4] = w * R, e[5] = (c * f * s - g * u * s + g * i * m - t * f * m - c * i * v + t * u * v) * R, e[6] = (g * l * s - o * f * s - g * i * a + t * f * a + o * i * v - t * l * v) * R, e[7] = (o * u * s - c * l * s + c * i * a - t * u * a - o * i * m + t * l * m) * R, e[8] = x * R, e[9] = (g * d * s - c * p * s - g * n * m + t * p * m + c * n * v - t * d * v) * R, e[10] = (o * p * s - g * r * s + g * n * a - t * p * a - o * n * v + t * r * v) * R, e[11] = (c * r * s - o * d * s - c * n * a + t * d * a + o * n * m - t * r * m) * R, e[12] = M * R, e[13] = (c * p * i - g * d * i + g * n * u - t * p * u - c * n * f + t * d * f) * R, e[14] = (g * r * i - o * p * i - g * n * l + t * p * l + o * n * f - t * r * f) * R, e[15] = (o * d * i - c * r * i + c * n * l - t * d * l - o * n * u + t * r * u) * R, this;
  }
  scale(e) {
    const t = this.elements, n = e.x, i = e.y, s = e.z;
    return t[0] *= n, t[4] *= i, t[8] *= s, t[1] *= n, t[5] *= i, t[9] *= s, t[2] *= n, t[6] *= i, t[10] *= s, t[3] *= n, t[7] *= i, t[11] *= s, this;
  }
  getMaxScaleOnAxis() {
    const e = this.elements, t = e[0] * e[0] + e[1] * e[1] + e[2] * e[2], n = e[4] * e[4] + e[5] * e[5] + e[6] * e[6], i = e[8] * e[8] + e[9] * e[9] + e[10] * e[10];
    return Math.sqrt(Math.max(t, n, i));
  }
  makeTranslation(e, t, n) {
    return this.set(
      1,
      0,
      0,
      e,
      0,
      1,
      0,
      t,
      0,
      0,
      1,
      n,
      0,
      0,
      0,
      1
    ), this;
  }
  makeRotationX(e) {
    const t = Math.cos(e), n = Math.sin(e);
    return this.set(
      1,
      0,
      0,
      0,
      0,
      t,
      -n,
      0,
      0,
      n,
      t,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  makeRotationY(e) {
    const t = Math.cos(e), n = Math.sin(e);
    return this.set(
      t,
      0,
      n,
      0,
      0,
      1,
      0,
      0,
      -n,
      0,
      t,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  makeRotationZ(e) {
    const t = Math.cos(e), n = Math.sin(e);
    return this.set(
      t,
      -n,
      0,
      0,
      n,
      t,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  makeRotationAxis(e, t) {
    const n = Math.cos(t), i = Math.sin(t), s = 1 - n, o = e.x, r = e.y, l = e.z, a = s * o, c = s * r;
    return this.set(
      a * o + n,
      a * r - i * l,
      a * l + i * r,
      0,
      a * r + i * l,
      c * r + n,
      c * l - i * o,
      0,
      a * l - i * r,
      c * l + i * o,
      s * l * l + n,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  makeScale(e, t, n) {
    return this.set(
      e,
      0,
      0,
      0,
      0,
      t,
      0,
      0,
      0,
      0,
      n,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  makeShear(e, t, n, i, s, o) {
    return this.set(
      1,
      n,
      s,
      0,
      e,
      1,
      o,
      0,
      t,
      i,
      1,
      0,
      0,
      0,
      0,
      1
    ), this;
  }
  compose(e, t, n) {
    const i = this.elements, s = t._x, o = t._y, r = t._z, l = t._w, a = s + s, c = o + o, d = r + r, u = s * a, m = s * c, g = s * d, p = o * c, f = o * d, v = r * d, _ = l * a, w = l * c, x = l * d, M = n.x, E = n.y, R = n.z;
    return i[0] = (1 - (p + v)) * M, i[1] = (m + x) * M, i[2] = (g - w) * M, i[3] = 0, i[4] = (m - x) * E, i[5] = (1 - (u + v)) * E, i[6] = (f + _) * E, i[7] = 0, i[8] = (g + w) * R, i[9] = (f - _) * R, i[10] = (1 - (u + p)) * R, i[11] = 0, i[12] = e.x, i[13] = e.y, i[14] = e.z, i[15] = 1, this;
  }
  decompose(e, t, n) {
    const i = this.elements;
    let s = zn.set(i[0], i[1], i[2]).length();
    const o = zn.set(i[4], i[5], i[6]).length(), r = zn.set(i[8], i[9], i[10]).length();
    this.determinant() < 0 && (s = -s), e.x = i[12], e.y = i[13], e.z = i[14], Tt.copy(this);
    const a = 1 / s, c = 1 / o, d = 1 / r;
    return Tt.elements[0] *= a, Tt.elements[1] *= a, Tt.elements[2] *= a, Tt.elements[4] *= c, Tt.elements[5] *= c, Tt.elements[6] *= c, Tt.elements[8] *= d, Tt.elements[9] *= d, Tt.elements[10] *= d, t.setFromRotationMatrix(Tt), n.x = s, n.y = o, n.z = r, this;
  }
  makePerspective(e, t, n, i, s, o) {
    const r = this.elements, l = 2 * s / (t - e), a = 2 * s / (n - i), c = (t + e) / (t - e), d = (n + i) / (n - i), u = -(o + s) / (o - s), m = -2 * o * s / (o - s);
    return r[0] = l, r[4] = 0, r[8] = c, r[12] = 0, r[1] = 0, r[5] = a, r[9] = d, r[13] = 0, r[2] = 0, r[6] = 0, r[10] = u, r[14] = m, r[3] = 0, r[7] = 0, r[11] = -1, r[15] = 0, this;
  }
  makeOrthographic(e, t, n, i, s, o) {
    const r = this.elements, l = 1 / (t - e), a = 1 / (n - i), c = 1 / (o - s), d = (t + e) * l, u = (n + i) * a, m = (o + s) * c;
    return r[0] = 2 * l, r[4] = 0, r[8] = 0, r[12] = -d, r[1] = 0, r[5] = 2 * a, r[9] = 0, r[13] = -u, r[2] = 0, r[6] = 0, r[10] = -2 * c, r[14] = -m, r[3] = 0, r[7] = 0, r[11] = 0, r[15] = 1, this;
  }
  equals(e) {
    const t = this.elements, n = e.elements;
    for (let i = 0; i < 16; i++)
      if (t[i] !== n[i])
        return !1;
    return !0;
  }
  fromArray(e, t = 0) {
    for (let n = 0; n < 16; n++)
      this.elements[n] = e[n + t];
    return this;
  }
  toArray(e = [], t = 0) {
    const n = this.elements;
    return e[t] = n[0], e[t + 1] = n[1], e[t + 2] = n[2], e[t + 3] = n[3], e[t + 4] = n[4], e[t + 5] = n[5], e[t + 6] = n[6], e[t + 7] = n[7], e[t + 8] = n[8], e[t + 9] = n[9], e[t + 10] = n[10], e[t + 11] = n[11], e[t + 12] = n[12], e[t + 13] = n[13], e[t + 14] = n[14], e[t + 15] = n[15], e;
  }
}
const zn = /* @__PURE__ */ new O(), Tt = /* @__PURE__ */ new Ke(), Wo = /* @__PURE__ */ new O(0, 0, 0), Vo = /* @__PURE__ */ new O(1, 1, 1), on = /* @__PURE__ */ new O(), Mi = /* @__PURE__ */ new O(), ft = /* @__PURE__ */ new O(), Qs = /* @__PURE__ */ new Ke(), er = /* @__PURE__ */ new ui();
class fi {
  constructor(e = 0, t = 0, n = 0, i = fi.DefaultOrder) {
    this.isEuler = !0, this._x = e, this._y = t, this._z = n, this._order = i;
  }
  get x() {
    return this._x;
  }
  set x(e) {
    this._x = e, this._onChangeCallback();
  }
  get y() {
    return this._y;
  }
  set y(e) {
    this._y = e, this._onChangeCallback();
  }
  get z() {
    return this._z;
  }
  set z(e) {
    this._z = e, this._onChangeCallback();
  }
  get order() {
    return this._order;
  }
  set order(e) {
    this._order = e, this._onChangeCallback();
  }
  set(e, t, n, i = this._order) {
    return this._x = e, this._y = t, this._z = n, this._order = i, this._onChangeCallback(), this;
  }
  clone() {
    return new this.constructor(this._x, this._y, this._z, this._order);
  }
  copy(e) {
    return this._x = e._x, this._y = e._y, this._z = e._z, this._order = e._order, this._onChangeCallback(), this;
  }
  setFromRotationMatrix(e, t = this._order, n = !0) {
    const i = e.elements, s = i[0], o = i[4], r = i[8], l = i[1], a = i[5], c = i[9], d = i[2], u = i[6], m = i[10];
    switch (t) {
      case "XYZ":
        this._y = Math.asin(mt(r, -1, 1)), Math.abs(r) < 0.9999999 ? (this._x = Math.atan2(-c, m), this._z = Math.atan2(-o, s)) : (this._x = Math.atan2(u, a), this._z = 0);
        break;
      case "YXZ":
        this._x = Math.asin(-mt(c, -1, 1)), Math.abs(c) < 0.9999999 ? (this._y = Math.atan2(r, m), this._z = Math.atan2(l, a)) : (this._y = Math.atan2(-d, s), this._z = 0);
        break;
      case "ZXY":
        this._x = Math.asin(mt(u, -1, 1)), Math.abs(u) < 0.9999999 ? (this._y = Math.atan2(-d, m), this._z = Math.atan2(-o, a)) : (this._y = 0, this._z = Math.atan2(l, s));
        break;
      case "ZYX":
        this._y = Math.asin(-mt(d, -1, 1)), Math.abs(d) < 0.9999999 ? (this._x = Math.atan2(u, m), this._z = Math.atan2(l, s)) : (this._x = 0, this._z = Math.atan2(-o, a));
        break;
      case "YZX":
        this._z = Math.asin(mt(l, -1, 1)), Math.abs(l) < 0.9999999 ? (this._x = Math.atan2(-c, a), this._y = Math.atan2(-d, s)) : (this._x = 0, this._y = Math.atan2(r, m));
        break;
      case "XZY":
        this._z = Math.asin(-mt(o, -1, 1)), Math.abs(o) < 0.9999999 ? (this._x = Math.atan2(u, a), this._y = Math.atan2(r, s)) : (this._x = Math.atan2(-c, m), this._y = 0);
        break;
      default:
        console.warn("THREE.Euler: .setFromRotationMatrix() encountered an unknown order: " + t);
    }
    return this._order = t, n === !0 && this._onChangeCallback(), this;
  }
  setFromQuaternion(e, t, n) {
    return Qs.makeRotationFromQuaternion(e), this.setFromRotationMatrix(Qs, t, n);
  }
  setFromVector3(e, t = this._order) {
    return this.set(e.x, e.y, e.z, t);
  }
  reorder(e) {
    return er.setFromEuler(this), this.setFromQuaternion(er, e);
  }
  equals(e) {
    return e._x === this._x && e._y === this._y && e._z === this._z && e._order === this._order;
  }
  fromArray(e) {
    return this._x = e[0], this._y = e[1], this._z = e[2], e[3] !== void 0 && (this._order = e[3]), this._onChangeCallback(), this;
  }
  toArray(e = [], t = 0) {
    return e[t] = this._x, e[t + 1] = this._y, e[t + 2] = this._z, e[t + 3] = this._order, e;
  }
  _onChange(e) {
    return this._onChangeCallback = e, this;
  }
  _onChangeCallback() {
  }
  *[Symbol.iterator]() {
    yield this._x, yield this._y, yield this._z, yield this._order;
  }
  toVector3() {
    console.error("THREE.Euler: .toVector3() has been removed. Use Vector3.setFromEuler() instead");
  }
}
fi.DefaultOrder = "XYZ";
fi.RotationOrders = ["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"];
class oo {
  constructor() {
    this.mask = 1;
  }
  set(e) {
    this.mask = (1 << e | 0) >>> 0;
  }
  enable(e) {
    this.mask |= 1 << e | 0;
  }
  enableAll() {
    this.mask = -1;
  }
  toggle(e) {
    this.mask ^= 1 << e | 0;
  }
  disable(e) {
    this.mask &= ~(1 << e | 0);
  }
  disableAll() {
    this.mask = 0;
  }
  test(e) {
    return (this.mask & e.mask) !== 0;
  }
  isEnabled(e) {
    return (this.mask & (1 << e | 0)) !== 0;
  }
}
let Ho = 0;
const tr = /* @__PURE__ */ new O(), Bn = /* @__PURE__ */ new ui(), Ht = /* @__PURE__ */ new Ke(), Si = /* @__PURE__ */ new O(), ti = /* @__PURE__ */ new O(), qo = /* @__PURE__ */ new O(), Xo = /* @__PURE__ */ new ui(), nr = /* @__PURE__ */ new O(1, 0, 0), ir = /* @__PURE__ */ new O(0, 1, 0), sr = /* @__PURE__ */ new O(0, 0, 1), jo = { type: "added" }, rr = { type: "removed" };
class at extends $n {
  constructor() {
    super(), this.isObject3D = !0, Object.defineProperty(this, "id", { value: Ho++ }), this.uuid = hi(), this.name = "", this.type = "Object3D", this.parent = null, this.children = [], this.up = at.DefaultUp.clone();
    const e = new O(), t = new fi(), n = new ui(), i = new O(1, 1, 1);
    function s() {
      n.setFromEuler(t, !1);
    }
    function o() {
      t.setFromQuaternion(n, void 0, !1);
    }
    t._onChange(s), n._onChange(o), Object.defineProperties(this, {
      position: {
        configurable: !0,
        enumerable: !0,
        value: e
      },
      rotation: {
        configurable: !0,
        enumerable: !0,
        value: t
      },
      quaternion: {
        configurable: !0,
        enumerable: !0,
        value: n
      },
      scale: {
        configurable: !0,
        enumerable: !0,
        value: i
      },
      modelViewMatrix: {
        value: new Ke()
      },
      normalMatrix: {
        value: new Mt()
      }
    }), this.matrix = new Ke(), this.matrixWorld = new Ke(), this.matrixAutoUpdate = at.DefaultMatrixAutoUpdate, this.matrixWorldNeedsUpdate = !1, this.layers = new oo(), this.visible = !0, this.castShadow = !1, this.receiveShadow = !1, this.frustumCulled = !0, this.renderOrder = 0, this.animations = [], this.userData = {};
  }
  onBeforeRender() {
  }
  onAfterRender() {
  }
  applyMatrix4(e) {
    this.matrixAutoUpdate && this.updateMatrix(), this.matrix.premultiply(e), this.matrix.decompose(this.position, this.quaternion, this.scale);
  }
  applyQuaternion(e) {
    return this.quaternion.premultiply(e), this;
  }
  setRotationFromAxisAngle(e, t) {
    this.quaternion.setFromAxisAngle(e, t);
  }
  setRotationFromEuler(e) {
    this.quaternion.setFromEuler(e, !0);
  }
  setRotationFromMatrix(e) {
    this.quaternion.setFromRotationMatrix(e);
  }
  setRotationFromQuaternion(e) {
    this.quaternion.copy(e);
  }
  rotateOnAxis(e, t) {
    return Bn.setFromAxisAngle(e, t), this.quaternion.multiply(Bn), this;
  }
  rotateOnWorldAxis(e, t) {
    return Bn.setFromAxisAngle(e, t), this.quaternion.premultiply(Bn), this;
  }
  rotateX(e) {
    return this.rotateOnAxis(nr, e);
  }
  rotateY(e) {
    return this.rotateOnAxis(ir, e);
  }
  rotateZ(e) {
    return this.rotateOnAxis(sr, e);
  }
  translateOnAxis(e, t) {
    return tr.copy(e).applyQuaternion(this.quaternion), this.position.add(tr.multiplyScalar(t)), this;
  }
  translateX(e) {
    return this.translateOnAxis(nr, e);
  }
  translateY(e) {
    return this.translateOnAxis(ir, e);
  }
  translateZ(e) {
    return this.translateOnAxis(sr, e);
  }
  localToWorld(e) {
    return e.applyMatrix4(this.matrixWorld);
  }
  worldToLocal(e) {
    return e.applyMatrix4(Ht.copy(this.matrixWorld).invert());
  }
  lookAt(e, t, n) {
    e.isVector3 ? Si.copy(e) : Si.set(e, t, n);
    const i = this.parent;
    this.updateWorldMatrix(!0, !1), ti.setFromMatrixPosition(this.matrixWorld), this.isCamera || this.isLight ? Ht.lookAt(ti, Si, this.up) : Ht.lookAt(Si, ti, this.up), this.quaternion.setFromRotationMatrix(Ht), i && (Ht.extractRotation(i.matrixWorld), Bn.setFromRotationMatrix(Ht), this.quaternion.premultiply(Bn.invert()));
  }
  add(e) {
    if (arguments.length > 1) {
      for (let t = 0; t < arguments.length; t++)
        this.add(arguments[t]);
      return this;
    }
    return e === this ? (console.error("THREE.Object3D.add: object can't be added as a child of itself.", e), this) : (e && e.isObject3D ? (e.parent !== null && e.parent.remove(e), e.parent = this, this.children.push(e), e.dispatchEvent(jo)) : console.error("THREE.Object3D.add: object not an instance of THREE.Object3D.", e), this);
  }
  remove(e) {
    if (arguments.length > 1) {
      for (let n = 0; n < arguments.length; n++)
        this.remove(arguments[n]);
      return this;
    }
    const t = this.children.indexOf(e);
    return t !== -1 && (e.parent = null, this.children.splice(t, 1), e.dispatchEvent(rr)), this;
  }
  removeFromParent() {
    const e = this.parent;
    return e !== null && e.remove(this), this;
  }
  clear() {
    for (let e = 0; e < this.children.length; e++) {
      const t = this.children[e];
      t.parent = null, t.dispatchEvent(rr);
    }
    return this.children.length = 0, this;
  }
  attach(e) {
    return this.updateWorldMatrix(!0, !1), Ht.copy(this.matrixWorld).invert(), e.parent !== null && (e.parent.updateWorldMatrix(!0, !1), Ht.multiply(e.parent.matrixWorld)), e.applyMatrix4(Ht), this.add(e), e.updateWorldMatrix(!1, !0), this;
  }
  getObjectById(e) {
    return this.getObjectByProperty("id", e);
  }
  getObjectByName(e) {
    return this.getObjectByProperty("name", e);
  }
  getObjectByProperty(e, t) {
    if (this[e] === t)
      return this;
    for (let n = 0, i = this.children.length; n < i; n++) {
      const o = this.children[n].getObjectByProperty(e, t);
      if (o !== void 0)
        return o;
    }
  }
  getWorldPosition(e) {
    return this.updateWorldMatrix(!0, !1), e.setFromMatrixPosition(this.matrixWorld);
  }
  getWorldQuaternion(e) {
    return this.updateWorldMatrix(!0, !1), this.matrixWorld.decompose(ti, e, qo), e;
  }
  getWorldScale(e) {
    return this.updateWorldMatrix(!0, !1), this.matrixWorld.decompose(ti, Xo, e), e;
  }
  getWorldDirection(e) {
    this.updateWorldMatrix(!0, !1);
    const t = this.matrixWorld.elements;
    return e.set(t[8], t[9], t[10]).normalize();
  }
  raycast() {
  }
  traverse(e) {
    e(this);
    const t = this.children;
    for (let n = 0, i = t.length; n < i; n++)
      t[n].traverse(e);
  }
  traverseVisible(e) {
    if (this.visible === !1)
      return;
    e(this);
    const t = this.children;
    for (let n = 0, i = t.length; n < i; n++)
      t[n].traverseVisible(e);
  }
  traverseAncestors(e) {
    const t = this.parent;
    t !== null && (e(t), t.traverseAncestors(e));
  }
  updateMatrix() {
    this.matrix.compose(this.position, this.quaternion, this.scale), this.matrixWorldNeedsUpdate = !0;
  }
  updateMatrixWorld(e) {
    this.matrixAutoUpdate && this.updateMatrix(), (this.matrixWorldNeedsUpdate || e) && (this.parent === null ? this.matrixWorld.copy(this.matrix) : this.matrixWorld.multiplyMatrices(this.parent.matrixWorld, this.matrix), this.matrixWorldNeedsUpdate = !1, e = !0);
    const t = this.children;
    for (let n = 0, i = t.length; n < i; n++)
      t[n].updateMatrixWorld(e);
  }
  updateWorldMatrix(e, t) {
    const n = this.parent;
    if (e === !0 && n !== null && n.updateWorldMatrix(!0, !1), this.matrixAutoUpdate && this.updateMatrix(), this.parent === null ? this.matrixWorld.copy(this.matrix) : this.matrixWorld.multiplyMatrices(this.parent.matrixWorld, this.matrix), t === !0) {
      const i = this.children;
      for (let s = 0, o = i.length; s < o; s++)
        i[s].updateWorldMatrix(!1, !0);
    }
  }
  toJSON(e) {
    const t = e === void 0 || typeof e == "string", n = {};
    t && (e = {
      geometries: {},
      materials: {},
      textures: {},
      images: {},
      shapes: {},
      skeletons: {},
      animations: {},
      nodes: {}
    }, n.metadata = {
      version: 4.5,
      type: "Object",
      generator: "Object3D.toJSON"
    });
    const i = {};
    i.uuid = this.uuid, i.type = this.type, this.name !== "" && (i.name = this.name), this.castShadow === !0 && (i.castShadow = !0), this.receiveShadow === !0 && (i.receiveShadow = !0), this.visible === !1 && (i.visible = !1), this.frustumCulled === !1 && (i.frustumCulled = !1), this.renderOrder !== 0 && (i.renderOrder = this.renderOrder), JSON.stringify(this.userData) !== "{}" && (i.userData = this.userData), i.layers = this.layers.mask, i.matrix = this.matrix.toArray(), this.matrixAutoUpdate === !1 && (i.matrixAutoUpdate = !1), this.isInstancedMesh && (i.type = "InstancedMesh", i.count = this.count, i.instanceMatrix = this.instanceMatrix.toJSON(), this.instanceColor !== null && (i.instanceColor = this.instanceColor.toJSON()));
    function s(r, l) {
      return r[l.uuid] === void 0 && (r[l.uuid] = l.toJSON(e)), l.uuid;
    }
    if (this.isScene)
      this.background && (this.background.isColor ? i.background = this.background.toJSON() : this.background.isTexture && (i.background = this.background.toJSON(e).uuid)), this.environment && this.environment.isTexture && this.environment.isRenderTargetTexture !== !0 && (i.environment = this.environment.toJSON(e).uuid);
    else if (this.isMesh || this.isLine || this.isPoints) {
      i.geometry = s(e.geometries, this.geometry);
      const r = this.geometry.parameters;
      if (r !== void 0 && r.shapes !== void 0) {
        const l = r.shapes;
        if (Array.isArray(l))
          for (let a = 0, c = l.length; a < c; a++) {
            const d = l[a];
            s(e.shapes, d);
          }
        else
          s(e.shapes, l);
      }
    }
    if (this.isSkinnedMesh && (i.bindMode = this.bindMode, i.bindMatrix = this.bindMatrix.toArray(), this.skeleton !== void 0 && (s(e.skeletons, this.skeleton), i.skeleton = this.skeleton.uuid)), this.material !== void 0)
      if (Array.isArray(this.material)) {
        const r = [];
        for (let l = 0, a = this.material.length; l < a; l++)
          r.push(s(e.materials, this.material[l]));
        i.material = r;
      } else
        i.material = s(e.materials, this.material);
    if (this.children.length > 0) {
      i.children = [];
      for (let r = 0; r < this.children.length; r++)
        i.children.push(this.children[r].toJSON(e).object);
    }
    if (this.animations.length > 0) {
      i.animations = [];
      for (let r = 0; r < this.animations.length; r++) {
        const l = this.animations[r];
        i.animations.push(s(e.animations, l));
      }
    }
    if (t) {
      const r = o(e.geometries), l = o(e.materials), a = o(e.textures), c = o(e.images), d = o(e.shapes), u = o(e.skeletons), m = o(e.animations), g = o(e.nodes);
      r.length > 0 && (n.geometries = r), l.length > 0 && (n.materials = l), a.length > 0 && (n.textures = a), c.length > 0 && (n.images = c), d.length > 0 && (n.shapes = d), u.length > 0 && (n.skeletons = u), m.length > 0 && (n.animations = m), g.length > 0 && (n.nodes = g);
    }
    return n.object = i, n;
    function o(r) {
      const l = [];
      for (const a in r) {
        const c = r[a];
        delete c.metadata, l.push(c);
      }
      return l;
    }
  }
  clone(e) {
    return new this.constructor().copy(this, e);
  }
  copy(e, t = !0) {
    if (this.name = e.name, this.up.copy(e.up), this.position.copy(e.position), this.rotation.order = e.rotation.order, this.quaternion.copy(e.quaternion), this.scale.copy(e.scale), this.matrix.copy(e.matrix), this.matrixWorld.copy(e.matrixWorld), this.matrixAutoUpdate = e.matrixAutoUpdate, this.matrixWorldNeedsUpdate = e.matrixWorldNeedsUpdate, this.layers.mask = e.layers.mask, this.visible = e.visible, this.castShadow = e.castShadow, this.receiveShadow = e.receiveShadow, this.frustumCulled = e.frustumCulled, this.renderOrder = e.renderOrder, this.userData = JSON.parse(JSON.stringify(e.userData)), t === !0)
      for (let n = 0; n < e.children.length; n++) {
        const i = e.children[n];
        this.add(i.clone());
      }
    return this;
  }
}
at.DefaultUp = /* @__PURE__ */ new O(0, 1, 0);
at.DefaultMatrixAutoUpdate = !0;
const At = /* @__PURE__ */ new O(), qt = /* @__PURE__ */ new O(), us = /* @__PURE__ */ new O(), Xt = /* @__PURE__ */ new O(), Nn = /* @__PURE__ */ new O(), On = /* @__PURE__ */ new O(), or = /* @__PURE__ */ new O(), ds = /* @__PURE__ */ new O(), fs = /* @__PURE__ */ new O(), ps = /* @__PURE__ */ new O();
class Qt {
  constructor(e = new O(), t = new O(), n = new O()) {
    this.a = e, this.b = t, this.c = n;
  }
  static getNormal(e, t, n, i) {
    i.subVectors(n, t), At.subVectors(e, t), i.cross(At);
    const s = i.lengthSq();
    return s > 0 ? i.multiplyScalar(1 / Math.sqrt(s)) : i.set(0, 0, 0);
  }
  static getBarycoord(e, t, n, i, s) {
    At.subVectors(i, t), qt.subVectors(n, t), us.subVectors(e, t);
    const o = At.dot(At), r = At.dot(qt), l = At.dot(us), a = qt.dot(qt), c = qt.dot(us), d = o * a - r * r;
    if (d === 0)
      return s.set(-2, -1, -1);
    const u = 1 / d, m = (a * l - r * c) * u, g = (o * c - r * l) * u;
    return s.set(1 - m - g, g, m);
  }
  static containsPoint(e, t, n, i) {
    return this.getBarycoord(e, t, n, i, Xt), Xt.x >= 0 && Xt.y >= 0 && Xt.x + Xt.y <= 1;
  }
  static getUV(e, t, n, i, s, o, r, l) {
    return this.getBarycoord(e, t, n, i, Xt), l.set(0, 0), l.addScaledVector(s, Xt.x), l.addScaledVector(o, Xt.y), l.addScaledVector(r, Xt.z), l;
  }
  static isFrontFacing(e, t, n, i) {
    return At.subVectors(n, t), qt.subVectors(e, t), At.cross(qt).dot(i) < 0;
  }
  set(e, t, n) {
    return this.a.copy(e), this.b.copy(t), this.c.copy(n), this;
  }
  setFromPointsAndIndices(e, t, n, i) {
    return this.a.copy(e[t]), this.b.copy(e[n]), this.c.copy(e[i]), this;
  }
  setFromAttributeAndIndices(e, t, n, i) {
    return this.a.fromBufferAttribute(e, t), this.b.fromBufferAttribute(e, n), this.c.fromBufferAttribute(e, i), this;
  }
  clone() {
    return new this.constructor().copy(this);
  }
  copy(e) {
    return this.a.copy(e.a), this.b.copy(e.b), this.c.copy(e.c), this;
  }
  getArea() {
    return At.subVectors(this.c, this.b), qt.subVectors(this.a, this.b), At.cross(qt).length() * 0.5;
  }
  getMidpoint(e) {
    return e.addVectors(this.a, this.b).add(this.c).multiplyScalar(1 / 3);
  }
  getNormal(e) {
    return Qt.getNormal(this.a, this.b, this.c, e);
  }
  getPlane(e) {
    return e.setFromCoplanarPoints(this.a, this.b, this.c);
  }
  getBarycoord(e, t) {
    return Qt.getBarycoord(e, this.a, this.b, this.c, t);
  }
  getUV(e, t, n, i, s) {
    return Qt.getUV(e, this.a, this.b, this.c, t, n, i, s);
  }
  containsPoint(e) {
    return Qt.containsPoint(e, this.a, this.b, this.c);
  }
  isFrontFacing(e) {
    return Qt.isFrontFacing(this.a, this.b, this.c, e);
  }
  intersectsBox(e) {
    return e.intersectsTriangle(this);
  }
  closestPointToPoint(e, t) {
    const n = this.a, i = this.b, s = this.c;
    let o, r;
    Nn.subVectors(i, n), On.subVectors(s, n), ds.subVectors(e, n);
    const l = Nn.dot(ds), a = On.dot(ds);
    if (l <= 0 && a <= 0)
      return t.copy(n);
    fs.subVectors(e, i);
    const c = Nn.dot(fs), d = On.dot(fs);
    if (c >= 0 && d <= c)
      return t.copy(i);
    const u = l * d - c * a;
    if (u <= 0 && l >= 0 && c <= 0)
      return o = l / (l - c), t.copy(n).addScaledVector(Nn, o);
    ps.subVectors(e, s);
    const m = Nn.dot(ps), g = On.dot(ps);
    if (g >= 0 && m <= g)
      return t.copy(s);
    const p = m * a - l * g;
    if (p <= 0 && a >= 0 && g <= 0)
      return r = a / (a - g), t.copy(n).addScaledVector(On, r);
    const f = c * g - m * d;
    if (f <= 0 && d - c >= 0 && m - g >= 0)
      return or.subVectors(s, i), r = (d - c) / (d - c + (m - g)), t.copy(i).addScaledVector(or, r);
    const v = 1 / (f + p + u);
    return o = p * v, r = u * v, t.copy(n).addScaledVector(Nn, o).addScaledVector(On, r);
  }
  equals(e) {
    return e.a.equals(this.a) && e.b.equals(this.b) && e.c.equals(this.c);
  }
}
let Yo = 0;
class An extends $n {
  constructor() {
    super(), this.isMaterial = !0, Object.defineProperty(this, "id", { value: Yo++ }), this.uuid = hi(), this.name = "", this.type = "Material", this.blending = 1, this.side = 0, this.vertexColors = !1, this.opacity = 1, this.transparent = !1, this.blendSrc = 204, this.blendDst = 205, this.blendEquation = 100, this.blendSrcAlpha = null, this.blendDstAlpha = null, this.blendEquationAlpha = null, this.depthFunc = 3, this.depthTest = !0, this.depthWrite = !0, this.stencilWriteMask = 255, this.stencilFunc = 519, this.stencilRef = 0, this.stencilFuncMask = 255, this.stencilFail = 7680, this.stencilZFail = 7680, this.stencilZPass = 7680, this.stencilWrite = !1, this.clippingPlanes = null, this.clipIntersection = !1, this.clipShadows = !1, this.shadowSide = null, this.colorWrite = !0, this.precision = null, this.polygonOffset = !1, this.polygonOffsetFactor = 0, this.polygonOffsetUnits = 0, this.dithering = !1, this.alphaToCoverage = !1, this.premultipliedAlpha = !1, this.visible = !0, this.toneMapped = !0, this.userData = {}, this.version = 0, this._alphaTest = 0;
  }
  get alphaTest() {
    return this._alphaTest;
  }
  set alphaTest(e) {
    this._alphaTest > 0 != e > 0 && this.version++, this._alphaTest = e;
  }
  onBuild() {
  }
  onBeforeRender() {
  }
  onBeforeCompile() {
  }
  customProgramCacheKey() {
    return this.onBeforeCompile.toString();
  }
  setValues(e) {
    if (e !== void 0)
      for (const t in e) {
        const n = e[t];
        if (n === void 0) {
          console.warn("THREE.Material: '" + t + "' parameter is undefined.");
          continue;
        }
        if (t === "shading") {
          console.warn("THREE." + this.type + ": .shading has been removed. Use the boolean .flatShading instead."), this.flatShading = n === 1;
          continue;
        }
        const i = this[t];
        if (i === void 0) {
          console.warn("THREE." + this.type + ": '" + t + "' is not a property of this material.");
          continue;
        }
        i && i.isColor ? i.set(n) : i && i.isVector3 && n && n.isVector3 ? i.copy(n) : this[t] = n;
      }
  }
  toJSON(e) {
    const t = e === void 0 || typeof e == "string";
    t && (e = {
      textures: {},
      images: {}
    });
    const n = {
      metadata: {
        version: 4.5,
        type: "Material",
        generator: "Material.toJSON"
      }
    };
    n.uuid = this.uuid, n.type = this.type, this.name !== "" && (n.name = this.name), this.color && this.color.isColor && (n.color = this.color.getHex()), this.roughness !== void 0 && (n.roughness = this.roughness), this.metalness !== void 0 && (n.metalness = this.metalness), this.sheen !== void 0 && (n.sheen = this.sheen), this.sheenColor && this.sheenColor.isColor && (n.sheenColor = this.sheenColor.getHex()), this.sheenRoughness !== void 0 && (n.sheenRoughness = this.sheenRoughness), this.emissive && this.emissive.isColor && (n.emissive = this.emissive.getHex()), this.emissiveIntensity && this.emissiveIntensity !== 1 && (n.emissiveIntensity = this.emissiveIntensity), this.specular && this.specular.isColor && (n.specular = this.specular.getHex()), this.specularIntensity !== void 0 && (n.specularIntensity = this.specularIntensity), this.specularColor && this.specularColor.isColor && (n.specularColor = this.specularColor.getHex()), this.shininess !== void 0 && (n.shininess = this.shininess), this.clearcoat !== void 0 && (n.clearcoat = this.clearcoat), this.clearcoatRoughness !== void 0 && (n.clearcoatRoughness = this.clearcoatRoughness), this.clearcoatMap && this.clearcoatMap.isTexture && (n.clearcoatMap = this.clearcoatMap.toJSON(e).uuid), this.clearcoatRoughnessMap && this.clearcoatRoughnessMap.isTexture && (n.clearcoatRoughnessMap = this.clearcoatRoughnessMap.toJSON(e).uuid), this.clearcoatNormalMap && this.clearcoatNormalMap.isTexture && (n.clearcoatNormalMap = this.clearcoatNormalMap.toJSON(e).uuid, n.clearcoatNormalScale = this.clearcoatNormalScale.toArray()), this.iridescence !== void 0 && (n.iridescence = this.iridescence), this.iridescenceIOR !== void 0 && (n.iridescenceIOR = this.iridescenceIOR), this.iridescenceThicknessRange !== void 0 && (n.iridescenceThicknessRange = this.iridescenceThicknessRange), this.iridescenceMap && this.iridescenceMap.isTexture && (n.iridescenceMap = this.iridescenceMap.toJSON(e).uuid), this.iridescenceThicknessMap && this.iridescenceThicknessMap.isTexture && (n.iridescenceThicknessMap = this.iridescenceThicknessMap.toJSON(e).uuid), this.map && this.map.isTexture && (n.map = this.map.toJSON(e).uuid), this.matcap && this.matcap.isTexture && (n.matcap = this.matcap.toJSON(e).uuid), this.alphaMap && this.alphaMap.isTexture && (n.alphaMap = this.alphaMap.toJSON(e).uuid), this.lightMap && this.lightMap.isTexture && (n.lightMap = this.lightMap.toJSON(e).uuid, n.lightMapIntensity = this.lightMapIntensity), this.aoMap && this.aoMap.isTexture && (n.aoMap = this.aoMap.toJSON(e).uuid, n.aoMapIntensity = this.aoMapIntensity), this.bumpMap && this.bumpMap.isTexture && (n.bumpMap = this.bumpMap.toJSON(e).uuid, n.bumpScale = this.bumpScale), this.normalMap && this.normalMap.isTexture && (n.normalMap = this.normalMap.toJSON(e).uuid, n.normalMapType = this.normalMapType, n.normalScale = this.normalScale.toArray()), this.displacementMap && this.displacementMap.isTexture && (n.displacementMap = this.displacementMap.toJSON(e).uuid, n.displacementScale = this.displacementScale, n.displacementBias = this.displacementBias), this.roughnessMap && this.roughnessMap.isTexture && (n.roughnessMap = this.roughnessMap.toJSON(e).uuid), this.metalnessMap && this.metalnessMap.isTexture && (n.metalnessMap = this.metalnessMap.toJSON(e).uuid), this.emissiveMap && this.emissiveMap.isTexture && (n.emissiveMap = this.emissiveMap.toJSON(e).uuid), this.specularMap && this.specularMap.isTexture && (n.specularMap = this.specularMap.toJSON(e).uuid), this.specularIntensityMap && this.specularIntensityMap.isTexture && (n.specularIntensityMap = this.specularIntensityMap.toJSON(e).uuid), this.specularColorMap && this.specularColorMap.isTexture && (n.specularColorMap = this.specularColorMap.toJSON(e).uuid), this.envMap && this.envMap.isTexture && (n.envMap = this.envMap.toJSON(e).uuid, this.combine !== void 0 && (n.combine = this.combine)), this.envMapIntensity !== void 0 && (n.envMapIntensity = this.envMapIntensity), this.reflectivity !== void 0 && (n.reflectivity = this.reflectivity), this.refractionRatio !== void 0 && (n.refractionRatio = this.refractionRatio), this.gradientMap && this.gradientMap.isTexture && (n.gradientMap = this.gradientMap.toJSON(e).uuid), this.transmission !== void 0 && (n.transmission = this.transmission), this.transmissionMap && this.transmissionMap.isTexture && (n.transmissionMap = this.transmissionMap.toJSON(e).uuid), this.thickness !== void 0 && (n.thickness = this.thickness), this.thicknessMap && this.thicknessMap.isTexture && (n.thicknessMap = this.thicknessMap.toJSON(e).uuid), this.attenuationDistance !== void 0 && (n.attenuationDistance = this.attenuationDistance), this.attenuationColor !== void 0 && (n.attenuationColor = this.attenuationColor.getHex()), this.size !== void 0 && (n.size = this.size), this.shadowSide !== null && (n.shadowSide = this.shadowSide), this.sizeAttenuation !== void 0 && (n.sizeAttenuation = this.sizeAttenuation), this.blending !== 1 && (n.blending = this.blending), this.side !== 0 && (n.side = this.side), this.vertexColors && (n.vertexColors = !0), this.opacity < 1 && (n.opacity = this.opacity), this.transparent === !0 && (n.transparent = this.transparent), n.depthFunc = this.depthFunc, n.depthTest = this.depthTest, n.depthWrite = this.depthWrite, n.colorWrite = this.colorWrite, n.stencilWrite = this.stencilWrite, n.stencilWriteMask = this.stencilWriteMask, n.stencilFunc = this.stencilFunc, n.stencilRef = this.stencilRef, n.stencilFuncMask = this.stencilFuncMask, n.stencilFail = this.stencilFail, n.stencilZFail = this.stencilZFail, n.stencilZPass = this.stencilZPass, this.rotation !== void 0 && this.rotation !== 0 && (n.rotation = this.rotation), this.polygonOffset === !0 && (n.polygonOffset = !0), this.polygonOffsetFactor !== 0 && (n.polygonOffsetFactor = this.polygonOffsetFactor), this.polygonOffsetUnits !== 0 && (n.polygonOffsetUnits = this.polygonOffsetUnits), this.linewidth !== void 0 && this.linewidth !== 1 && (n.linewidth = this.linewidth), this.dashSize !== void 0 && (n.dashSize = this.dashSize), this.gapSize !== void 0 && (n.gapSize = this.gapSize), this.scale !== void 0 && (n.scale = this.scale), this.dithering === !0 && (n.dithering = !0), this.alphaTest > 0 && (n.alphaTest = this.alphaTest), this.alphaToCoverage === !0 && (n.alphaToCoverage = this.alphaToCoverage), this.premultipliedAlpha === !0 && (n.premultipliedAlpha = this.premultipliedAlpha), this.wireframe === !0 && (n.wireframe = this.wireframe), this.wireframeLinewidth > 1 && (n.wireframeLinewidth = this.wireframeLinewidth), this.wireframeLinecap !== "round" && (n.wireframeLinecap = this.wireframeLinecap), this.wireframeLinejoin !== "round" && (n.wireframeLinejoin = this.wireframeLinejoin), this.flatShading === !0 && (n.flatShading = this.flatShading), this.visible === !1 && (n.visible = !1), this.toneMapped === !1 && (n.toneMapped = !1), this.fog === !1 && (n.fog = !1), JSON.stringify(this.userData) !== "{}" && (n.userData = this.userData);
    function i(s) {
      const o = [];
      for (const r in s) {
        const l = s[r];
        delete l.metadata, o.push(l);
      }
      return o;
    }
    if (t) {
      const s = i(e.textures), o = i(e.images);
      s.length > 0 && (n.textures = s), o.length > 0 && (n.images = o);
    }
    return n;
  }
  clone() {
    return new this.constructor().copy(this);
  }
  copy(e) {
    this.name = e.name, this.blending = e.blending, this.side = e.side, this.vertexColors = e.vertexColors, this.opacity = e.opacity, this.transparent = e.transparent, this.blendSrc = e.blendSrc, this.blendDst = e.blendDst, this.blendEquation = e.blendEquation, this.blendSrcAlpha = e.blendSrcAlpha, this.blendDstAlpha = e.blendDstAlpha, this.blendEquationAlpha = e.blendEquationAlpha, this.depthFunc = e.depthFunc, this.depthTest = e.depthTest, this.depthWrite = e.depthWrite, this.stencilWriteMask = e.stencilWriteMask, this.stencilFunc = e.stencilFunc, this.stencilRef = e.stencilRef, this.stencilFuncMask = e.stencilFuncMask, this.stencilFail = e.stencilFail, this.stencilZFail = e.stencilZFail, this.stencilZPass = e.stencilZPass, this.stencilWrite = e.stencilWrite;
    const t = e.clippingPlanes;
    let n = null;
    if (t !== null) {
      const i = t.length;
      n = new Array(i);
      for (let s = 0; s !== i; ++s)
        n[s] = t[s].clone();
    }
    return this.clippingPlanes = n, this.clipIntersection = e.clipIntersection, this.clipShadows = e.clipShadows, this.shadowSide = e.shadowSide, this.colorWrite = e.colorWrite, this.precision = e.precision, this.polygonOffset = e.polygonOffset, this.polygonOffsetFactor = e.polygonOffsetFactor, this.polygonOffsetUnits = e.polygonOffsetUnits, this.dithering = e.dithering, this.alphaTest = e.alphaTest, this.alphaToCoverage = e.alphaToCoverage, this.premultipliedAlpha = e.premultipliedAlpha, this.visible = e.visible, this.toneMapped = e.toneMapped, this.userData = JSON.parse(JSON.stringify(e.userData)), this;
  }
  dispose() {
    this.dispatchEvent({ type: "dispose" });
  }
  set needsUpdate(e) {
    e === !0 && this.version++;
  }
}
class ao extends An {
  constructor(e) {
    super(), this.isMeshBasicMaterial = !0, this.type = "MeshBasicMaterial", this.color = new Ae(16777215), this.map = null, this.lightMap = null, this.lightMapIntensity = 1, this.aoMap = null, this.aoMapIntensity = 1, this.specularMap = null, this.alphaMap = null, this.envMap = null, this.combine = 0, this.reflectivity = 1, this.refractionRatio = 0.98, this.wireframe = !1, this.wireframeLinewidth = 1, this.wireframeLinecap = "round", this.wireframeLinejoin = "round", this.fog = !0, this.setValues(e);
  }
  copy(e) {
    return super.copy(e), this.color.copy(e.color), this.map = e.map, this.lightMap = e.lightMap, this.lightMapIntensity = e.lightMapIntensity, this.aoMap = e.aoMap, this.aoMapIntensity = e.aoMapIntensity, this.specularMap = e.specularMap, this.alphaMap = e.alphaMap, this.envMap = e.envMap, this.combine = e.combine, this.reflectivity = e.reflectivity, this.refractionRatio = e.refractionRatio, this.wireframe = e.wireframe, this.wireframeLinewidth = e.wireframeLinewidth, this.wireframeLinecap = e.wireframeLinecap, this.wireframeLinejoin = e.wireframeLinejoin, this.fog = e.fog, this;
  }
}
const qe = /* @__PURE__ */ new O(), Ei = /* @__PURE__ */ new Ce();
class Ot {
  constructor(e, t, n) {
    if (Array.isArray(e))
      throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");
    this.isBufferAttribute = !0, this.name = "", this.array = e, this.itemSize = t, this.count = e !== void 0 ? e.length / t : 0, this.normalized = n === !0, this.usage = 35044, this.updateRange = { offset: 0, count: -1 }, this.version = 0;
  }
  onUploadCallback() {
  }
  set needsUpdate(e) {
    e === !0 && this.version++;
  }
  setUsage(e) {
    return this.usage = e, this;
  }
  copy(e) {
    return this.name = e.name, this.array = new e.array.constructor(e.array), this.itemSize = e.itemSize, this.count = e.count, this.normalized = e.normalized, this.usage = e.usage, this;
  }
  copyAt(e, t, n) {
    e *= this.itemSize, n *= t.itemSize;
    for (let i = 0, s = this.itemSize; i < s; i++)
      this.array[e + i] = t.array[n + i];
    return this;
  }
  copyArray(e) {
    return this.array.set(e), this;
  }
  copyColorsArray(e) {
    const t = this.array;
    let n = 0;
    for (let i = 0, s = e.length; i < s; i++) {
      let o = e[i];
      o === void 0 && (console.warn("THREE.BufferAttribute.copyColorsArray(): color is undefined", i), o = new Ae()), t[n++] = o.r, t[n++] = o.g, t[n++] = o.b;
    }
    return this;
  }
  copyVector2sArray(e) {
    const t = this.array;
    let n = 0;
    for (let i = 0, s = e.length; i < s; i++) {
      let o = e[i];
      o === void 0 && (console.warn("THREE.BufferAttribute.copyVector2sArray(): vector is undefined", i), o = new Ce()), t[n++] = o.x, t[n++] = o.y;
    }
    return this;
  }
  copyVector3sArray(e) {
    const t = this.array;
    let n = 0;
    for (let i = 0, s = e.length; i < s; i++) {
      let o = e[i];
      o === void 0 && (console.warn("THREE.BufferAttribute.copyVector3sArray(): vector is undefined", i), o = new O()), t[n++] = o.x, t[n++] = o.y, t[n++] = o.z;
    }
    return this;
  }
  copyVector4sArray(e) {
    const t = this.array;
    let n = 0;
    for (let i = 0, s = e.length; i < s; i++) {
      let o = e[i];
      o === void 0 && (console.warn("THREE.BufferAttribute.copyVector4sArray(): vector is undefined", i), o = new $e()), t[n++] = o.x, t[n++] = o.y, t[n++] = o.z, t[n++] = o.w;
    }
    return this;
  }
  applyMatrix3(e) {
    if (this.itemSize === 2)
      for (let t = 0, n = this.count; t < n; t++)
        Ei.fromBufferAttribute(this, t), Ei.applyMatrix3(e), this.setXY(t, Ei.x, Ei.y);
    else if (this.itemSize === 3)
      for (let t = 0, n = this.count; t < n; t++)
        qe.fromBufferAttribute(this, t), qe.applyMatrix3(e), this.setXYZ(t, qe.x, qe.y, qe.z);
    return this;
  }
  applyMatrix4(e) {
    for (let t = 0, n = this.count; t < n; t++)
      qe.fromBufferAttribute(this, t), qe.applyMatrix4(e), this.setXYZ(t, qe.x, qe.y, qe.z);
    return this;
  }
  applyNormalMatrix(e) {
    for (let t = 0, n = this.count; t < n; t++)
      qe.fromBufferAttribute(this, t), qe.applyNormalMatrix(e), this.setXYZ(t, qe.x, qe.y, qe.z);
    return this;
  }
  transformDirection(e) {
    for (let t = 0, n = this.count; t < n; t++)
      qe.fromBufferAttribute(this, t), qe.transformDirection(e), this.setXYZ(t, qe.x, qe.y, qe.z);
    return this;
  }
  set(e, t = 0) {
    return this.array.set(e, t), this;
  }
  getX(e) {
    return this.array[e * this.itemSize];
  }
  setX(e, t) {
    return this.array[e * this.itemSize] = t, this;
  }
  getY(e) {
    return this.array[e * this.itemSize + 1];
  }
  setY(e, t) {
    return this.array[e * this.itemSize + 1] = t, this;
  }
  getZ(e) {
    return this.array[e * this.itemSize + 2];
  }
  setZ(e, t) {
    return this.array[e * this.itemSize + 2] = t, this;
  }
  getW(e) {
    return this.array[e * this.itemSize + 3];
  }
  setW(e, t) {
    return this.array[e * this.itemSize + 3] = t, this;
  }
  setXY(e, t, n) {
    return e *= this.itemSize, this.array[e + 0] = t, this.array[e + 1] = n, this;
  }
  setXYZ(e, t, n, i) {
    return e *= this.itemSize, this.array[e + 0] = t, this.array[e + 1] = n, this.array[e + 2] = i, this;
  }
  setXYZW(e, t, n, i, s) {
    return e *= this.itemSize, this.array[e + 0] = t, this.array[e + 1] = n, this.array[e + 2] = i, this.array[e + 3] = s, this;
  }
  onUpload(e) {
    return this.onUploadCallback = e, this;
  }
  clone() {
    return new this.constructor(this.array, this.itemSize).copy(this);
  }
  toJSON() {
    const e = {
      itemSize: this.itemSize,
      type: this.array.constructor.name,
      array: Array.from(this.array),
      normalized: this.normalized
    };
    return this.name !== "" && (e.name = this.name), this.usage !== 35044 && (e.usage = this.usage), (this.updateRange.offset !== 0 || this.updateRange.count !== -1) && (e.updateRange = this.updateRange), e;
  }
}
class lo extends Ot {
  constructor(e, t, n) {
    super(new Uint16Array(e), t, n);
  }
}
class co extends Ot {
  constructor(e, t, n) {
    super(new Uint32Array(e), t, n);
  }
}
class st extends Ot {
  constructor(e, t, n) {
    super(new Float32Array(e), t, n);
  }
}
let Zo = 0;
const bt = /* @__PURE__ */ new Ke(), ms = /* @__PURE__ */ new at(), Un = /* @__PURE__ */ new O(), pt = /* @__PURE__ */ new di(), ni = /* @__PURE__ */ new di(), Qe = /* @__PURE__ */ new O();
class Ut extends $n {
  constructor() {
    super(), this.isBufferGeometry = !0, Object.defineProperty(this, "id", { value: Zo++ }), this.uuid = hi(), this.name = "", this.type = "BufferGeometry", this.index = null, this.attributes = {}, this.morphAttributes = {}, this.morphTargetsRelative = !1, this.groups = [], this.boundingBox = null, this.boundingSphere = null, this.drawRange = { start: 0, count: 1 / 0 }, this.userData = {};
  }
  getIndex() {
    return this.index;
  }
  setIndex(e) {
    return Array.isArray(e) ? this.index = new (to(e) ? co : lo)(e, 1) : this.index = e, this;
  }
  getAttribute(e) {
    return this.attributes[e];
  }
  setAttribute(e, t) {
    return this.attributes[e] = t, this;
  }
  deleteAttribute(e) {
    return delete this.attributes[e], this;
  }
  hasAttribute(e) {
    return this.attributes[e] !== void 0;
  }
  addGroup(e, t, n = 0) {
    this.groups.push({
      start: e,
      count: t,
      materialIndex: n
    });
  }
  clearGroups() {
    this.groups = [];
  }
  setDrawRange(e, t) {
    this.drawRange.start = e, this.drawRange.count = t;
  }
  applyMatrix4(e) {
    const t = this.attributes.position;
    t !== void 0 && (t.applyMatrix4(e), t.needsUpdate = !0);
    const n = this.attributes.normal;
    if (n !== void 0) {
      const s = new Mt().getNormalMatrix(e);
      n.applyNormalMatrix(s), n.needsUpdate = !0;
    }
    const i = this.attributes.tangent;
    return i !== void 0 && (i.transformDirection(e), i.needsUpdate = !0), this.boundingBox !== null && this.computeBoundingBox(), this.boundingSphere !== null && this.computeBoundingSphere(), this;
  }
  applyQuaternion(e) {
    return bt.makeRotationFromQuaternion(e), this.applyMatrix4(bt), this;
  }
  rotateX(e) {
    return bt.makeRotationX(e), this.applyMatrix4(bt), this;
  }
  rotateY(e) {
    return bt.makeRotationY(e), this.applyMatrix4(bt), this;
  }
  rotateZ(e) {
    return bt.makeRotationZ(e), this.applyMatrix4(bt), this;
  }
  translate(e, t, n) {
    return bt.makeTranslation(e, t, n), this.applyMatrix4(bt), this;
  }
  scale(e, t, n) {
    return bt.makeScale(e, t, n), this.applyMatrix4(bt), this;
  }
  lookAt(e) {
    return ms.lookAt(e), ms.updateMatrix(), this.applyMatrix4(ms.matrix), this;
  }
  center() {
    return this.computeBoundingBox(), this.boundingBox.getCenter(Un).negate(), this.translate(Un.x, Un.y, Un.z), this;
  }
  setFromPoints(e) {
    const t = [];
    for (let n = 0, i = e.length; n < i; n++) {
      const s = e[n];
      t.push(s.x, s.y, s.z || 0);
    }
    return this.setAttribute("position", new st(t, 3)), this;
  }
  computeBoundingBox() {
    this.boundingBox === null && (this.boundingBox = new di());
    const e = this.attributes.position, t = this.morphAttributes.position;
    if (e && e.isGLBufferAttribute) {
      console.error('THREE.BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box. Alternatively set "mesh.frustumCulled" to "false".', this), this.boundingBox.set(
        new O(-1 / 0, -1 / 0, -1 / 0),
        new O(1 / 0, 1 / 0, 1 / 0)
      );
      return;
    }
    if (e !== void 0) {
      if (this.boundingBox.setFromBufferAttribute(e), t)
        for (let n = 0, i = t.length; n < i; n++) {
          const s = t[n];
          pt.setFromBufferAttribute(s), this.morphTargetsRelative ? (Qe.addVectors(this.boundingBox.min, pt.min), this.boundingBox.expandByPoint(Qe), Qe.addVectors(this.boundingBox.max, pt.max), this.boundingBox.expandByPoint(Qe)) : (this.boundingBox.expandByPoint(pt.min), this.boundingBox.expandByPoint(pt.max));
        }
    } else
      this.boundingBox.makeEmpty();
    (isNaN(this.boundingBox.min.x) || isNaN(this.boundingBox.min.y) || isNaN(this.boundingBox.min.z)) && console.error('THREE.BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.', this);
  }
  computeBoundingSphere() {
    this.boundingSphere === null && (this.boundingSphere = new ci());
    const e = this.attributes.position, t = this.morphAttributes.position;
    if (e && e.isGLBufferAttribute) {
      console.error('THREE.BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere. Alternatively set "mesh.frustumCulled" to "false".', this), this.boundingSphere.set(new O(), 1 / 0);
      return;
    }
    if (e) {
      const n = this.boundingSphere.center;
      if (pt.setFromBufferAttribute(e), t)
        for (let s = 0, o = t.length; s < o; s++) {
          const r = t[s];
          ni.setFromBufferAttribute(r), this.morphTargetsRelative ? (Qe.addVectors(pt.min, ni.min), pt.expandByPoint(Qe), Qe.addVectors(pt.max, ni.max), pt.expandByPoint(Qe)) : (pt.expandByPoint(ni.min), pt.expandByPoint(ni.max));
        }
      pt.getCenter(n);
      let i = 0;
      for (let s = 0, o = e.count; s < o; s++)
        Qe.fromBufferAttribute(e, s), i = Math.max(i, n.distanceToSquared(Qe));
      if (t)
        for (let s = 0, o = t.length; s < o; s++) {
          const r = t[s], l = this.morphTargetsRelative;
          for (let a = 0, c = r.count; a < c; a++)
            Qe.fromBufferAttribute(r, a), l && (Un.fromBufferAttribute(e, a), Qe.add(Un)), i = Math.max(i, n.distanceToSquared(Qe));
        }
      this.boundingSphere.radius = Math.sqrt(i), isNaN(this.boundingSphere.radius) && console.error('THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.', this);
    }
  }
  computeTangents() {
    const e = this.index, t = this.attributes;
    if (e === null || t.position === void 0 || t.normal === void 0 || t.uv === void 0) {
      console.error("THREE.BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");
      return;
    }
    const n = e.array, i = t.position.array, s = t.normal.array, o = t.uv.array, r = i.length / 3;
    this.hasAttribute("tangent") === !1 && this.setAttribute("tangent", new Ot(new Float32Array(4 * r), 4));
    const l = this.getAttribute("tangent").array, a = [], c = [];
    for (let F = 0; F < r; F++)
      a[F] = new O(), c[F] = new O();
    const d = new O(), u = new O(), m = new O(), g = new Ce(), p = new Ce(), f = new Ce(), v = new O(), _ = new O();
    function w(F, P, G) {
      d.fromArray(i, F * 3), u.fromArray(i, P * 3), m.fromArray(i, G * 3), g.fromArray(o, F * 2), p.fromArray(o, P * 2), f.fromArray(o, G * 2), u.sub(d), m.sub(d), p.sub(g), f.sub(g);
      const z = 1 / (p.x * f.y - f.x * p.y);
      !isFinite(z) || (v.copy(u).multiplyScalar(f.y).addScaledVector(m, -p.y).multiplyScalar(z), _.copy(m).multiplyScalar(p.x).addScaledVector(u, -f.x).multiplyScalar(z), a[F].add(v), a[P].add(v), a[G].add(v), c[F].add(_), c[P].add(_), c[G].add(_));
    }
    let x = this.groups;
    x.length === 0 && (x = [{
      start: 0,
      count: n.length
    }]);
    for (let F = 0, P = x.length; F < P; ++F) {
      const G = x[F], z = G.start, L = G.count;
      for (let I = z, D = z + L; I < D; I += 3)
        w(
          n[I + 0],
          n[I + 1],
          n[I + 2]
        );
    }
    const M = new O(), E = new O(), R = new O(), y = new O();
    function A(F) {
      R.fromArray(s, F * 3), y.copy(R);
      const P = a[F];
      M.copy(P), M.sub(R.multiplyScalar(R.dot(P))).normalize(), E.crossVectors(y, P);
      const z = E.dot(c[F]) < 0 ? -1 : 1;
      l[F * 4] = M.x, l[F * 4 + 1] = M.y, l[F * 4 + 2] = M.z, l[F * 4 + 3] = z;
    }
    for (let F = 0, P = x.length; F < P; ++F) {
      const G = x[F], z = G.start, L = G.count;
      for (let I = z, D = z + L; I < D; I += 3)
        A(n[I + 0]), A(n[I + 1]), A(n[I + 2]);
    }
  }
  computeVertexNormals() {
    const e = this.index, t = this.getAttribute("position");
    if (t !== void 0) {
      let n = this.getAttribute("normal");
      if (n === void 0)
        n = new Ot(new Float32Array(t.count * 3), 3), this.setAttribute("normal", n);
      else
        for (let u = 0, m = n.count; u < m; u++)
          n.setXYZ(u, 0, 0, 0);
      const i = new O(), s = new O(), o = new O(), r = new O(), l = new O(), a = new O(), c = new O(), d = new O();
      if (e)
        for (let u = 0, m = e.count; u < m; u += 3) {
          const g = e.getX(u + 0), p = e.getX(u + 1), f = e.getX(u + 2);
          i.fromBufferAttribute(t, g), s.fromBufferAttribute(t, p), o.fromBufferAttribute(t, f), c.subVectors(o, s), d.subVectors(i, s), c.cross(d), r.fromBufferAttribute(n, g), l.fromBufferAttribute(n, p), a.fromBufferAttribute(n, f), r.add(c), l.add(c), a.add(c), n.setXYZ(g, r.x, r.y, r.z), n.setXYZ(p, l.x, l.y, l.z), n.setXYZ(f, a.x, a.y, a.z);
        }
      else
        for (let u = 0, m = t.count; u < m; u += 3)
          i.fromBufferAttribute(t, u + 0), s.fromBufferAttribute(t, u + 1), o.fromBufferAttribute(t, u + 2), c.subVectors(o, s), d.subVectors(i, s), c.cross(d), n.setXYZ(u + 0, c.x, c.y, c.z), n.setXYZ(u + 1, c.x, c.y, c.z), n.setXYZ(u + 2, c.x, c.y, c.z);
      this.normalizeNormals(), n.needsUpdate = !0;
    }
  }
  merge(e, t) {
    if (!(e && e.isBufferGeometry)) {
      console.error("THREE.BufferGeometry.merge(): geometry not an instance of THREE.BufferGeometry.", e);
      return;
    }
    t === void 0 && (t = 0, console.warn(
      "THREE.BufferGeometry.merge(): Overwriting original geometry, starting at offset=0. Use BufferGeometryUtils.mergeBufferGeometries() for lossless merge."
    ));
    const n = this.attributes;
    for (const i in n) {
      if (e.attributes[i] === void 0)
        continue;
      const o = n[i].array, r = e.attributes[i], l = r.array, a = r.itemSize * t, c = Math.min(l.length, o.length - a);
      for (let d = 0, u = a; d < c; d++, u++)
        o[u] = l[d];
    }
    return this;
  }
  normalizeNormals() {
    const e = this.attributes.normal;
    for (let t = 0, n = e.count; t < n; t++)
      Qe.fromBufferAttribute(e, t), Qe.normalize(), e.setXYZ(t, Qe.x, Qe.y, Qe.z);
  }
  toNonIndexed() {
    function e(r, l) {
      const a = r.array, c = r.itemSize, d = r.normalized, u = new a.constructor(l.length * c);
      let m = 0, g = 0;
      for (let p = 0, f = l.length; p < f; p++) {
        r.isInterleavedBufferAttribute ? m = l[p] * r.data.stride + r.offset : m = l[p] * c;
        for (let v = 0; v < c; v++)
          u[g++] = a[m++];
      }
      return new Ot(u, c, d);
    }
    if (this.index === null)
      return console.warn("THREE.BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."), this;
    const t = new Ut(), n = this.index.array, i = this.attributes;
    for (const r in i) {
      const l = i[r], a = e(l, n);
      t.setAttribute(r, a);
    }
    const s = this.morphAttributes;
    for (const r in s) {
      const l = [], a = s[r];
      for (let c = 0, d = a.length; c < d; c++) {
        const u = a[c], m = e(u, n);
        l.push(m);
      }
      t.morphAttributes[r] = l;
    }
    t.morphTargetsRelative = this.morphTargetsRelative;
    const o = this.groups;
    for (let r = 0, l = o.length; r < l; r++) {
      const a = o[r];
      t.addGroup(a.start, a.count, a.materialIndex);
    }
    return t;
  }
  toJSON() {
    const e = {
      metadata: {
        version: 4.5,
        type: "BufferGeometry",
        generator: "BufferGeometry.toJSON"
      }
    };
    if (e.uuid = this.uuid, e.type = this.type, this.name !== "" && (e.name = this.name), Object.keys(this.userData).length > 0 && (e.userData = this.userData), this.parameters !== void 0) {
      const l = this.parameters;
      for (const a in l)
        l[a] !== void 0 && (e[a] = l[a]);
      return e;
    }
    e.data = { attributes: {} };
    const t = this.index;
    t !== null && (e.data.index = {
      type: t.array.constructor.name,
      array: Array.prototype.slice.call(t.array)
    });
    const n = this.attributes;
    for (const l in n) {
      const a = n[l];
      e.data.attributes[l] = a.toJSON(e.data);
    }
    const i = {};
    let s = !1;
    for (const l in this.morphAttributes) {
      const a = this.morphAttributes[l], c = [];
      for (let d = 0, u = a.length; d < u; d++) {
        const m = a[d];
        c.push(m.toJSON(e.data));
      }
      c.length > 0 && (i[l] = c, s = !0);
    }
    s && (e.data.morphAttributes = i, e.data.morphTargetsRelative = this.morphTargetsRelative);
    const o = this.groups;
    o.length > 0 && (e.data.groups = JSON.parse(JSON.stringify(o)));
    const r = this.boundingSphere;
    return r !== null && (e.data.boundingSphere = {
      center: r.center.toArray(),
      radius: r.radius
    }), e;
  }
  clone() {
    return new this.constructor().copy(this);
  }
  copy(e) {
    this.index = null, this.attributes = {}, this.morphAttributes = {}, this.groups = [], this.boundingBox = null, this.boundingSphere = null;
    const t = {};
    this.name = e.name;
    const n = e.index;
    n !== null && this.setIndex(n.clone(t));
    const i = e.attributes;
    for (const a in i) {
      const c = i[a];
      this.setAttribute(a, c.clone(t));
    }
    const s = e.morphAttributes;
    for (const a in s) {
      const c = [], d = s[a];
      for (let u = 0, m = d.length; u < m; u++)
        c.push(d[u].clone(t));
      this.morphAttributes[a] = c;
    }
    this.morphTargetsRelative = e.morphTargetsRelative;
    const o = e.groups;
    for (let a = 0, c = o.length; a < c; a++) {
      const d = o[a];
      this.addGroup(d.start, d.count, d.materialIndex);
    }
    const r = e.boundingBox;
    r !== null && (this.boundingBox = r.clone());
    const l = e.boundingSphere;
    return l !== null && (this.boundingSphere = l.clone()), this.drawRange.start = e.drawRange.start, this.drawRange.count = e.drawRange.count, this.userData = e.userData, e.parameters !== void 0 && (this.parameters = Object.assign({}, e.parameters)), this;
  }
  dispose() {
    this.dispatchEvent({ type: "dispose" });
  }
}
const ar = /* @__PURE__ */ new Ke(), Gn = /* @__PURE__ */ new ko(), gs = /* @__PURE__ */ new ci(), an = /* @__PURE__ */ new O(), ln = /* @__PURE__ */ new O(), cn = /* @__PURE__ */ new O(), _s = /* @__PURE__ */ new O(), vs = /* @__PURE__ */ new O(), xs = /* @__PURE__ */ new O(), Ti = /* @__PURE__ */ new O(), Ai = /* @__PURE__ */ new O(), Ci = /* @__PURE__ */ new O(), Li = /* @__PURE__ */ new Ce(), Ri = /* @__PURE__ */ new Ce(), Fi = /* @__PURE__ */ new Ce(), ys = /* @__PURE__ */ new O(), Di = /* @__PURE__ */ new O();
class Nt extends at {
  constructor(e = new Ut(), t = new ao()) {
    super(), this.isMesh = !0, this.type = "Mesh", this.geometry = e, this.material = t, this.updateMorphTargets();
  }
  copy(e, t) {
    return super.copy(e, t), e.morphTargetInfluences !== void 0 && (this.morphTargetInfluences = e.morphTargetInfluences.slice()), e.morphTargetDictionary !== void 0 && (this.morphTargetDictionary = Object.assign({}, e.morphTargetDictionary)), this.material = e.material, this.geometry = e.geometry, this;
  }
  updateMorphTargets() {
    const t = this.geometry.morphAttributes, n = Object.keys(t);
    if (n.length > 0) {
      const i = t[n[0]];
      if (i !== void 0) {
        this.morphTargetInfluences = [], this.morphTargetDictionary = {};
        for (let s = 0, o = i.length; s < o; s++) {
          const r = i[s].name || String(s);
          this.morphTargetInfluences.push(0), this.morphTargetDictionary[r] = s;
        }
      }
    }
  }
  raycast(e, t) {
    const n = this.geometry, i = this.material, s = this.matrixWorld;
    if (i === void 0 || (n.boundingSphere === null && n.computeBoundingSphere(), gs.copy(n.boundingSphere), gs.applyMatrix4(s), e.ray.intersectsSphere(gs) === !1) || (ar.copy(s).invert(), Gn.copy(e.ray).applyMatrix4(ar), n.boundingBox !== null && Gn.intersectsBox(n.boundingBox) === !1))
      return;
    let o;
    const r = n.index, l = n.attributes.position, a = n.morphAttributes.position, c = n.morphTargetsRelative, d = n.attributes.uv, u = n.attributes.uv2, m = n.groups, g = n.drawRange;
    if (r !== null)
      if (Array.isArray(i))
        for (let p = 0, f = m.length; p < f; p++) {
          const v = m[p], _ = i[v.materialIndex], w = Math.max(v.start, g.start), x = Math.min(r.count, Math.min(v.start + v.count, g.start + g.count));
          for (let M = w, E = x; M < E; M += 3) {
            const R = r.getX(M), y = r.getX(M + 1), A = r.getX(M + 2);
            o = Pi(this, _, e, Gn, l, a, c, d, u, R, y, A), o && (o.faceIndex = Math.floor(M / 3), o.face.materialIndex = v.materialIndex, t.push(o));
          }
        }
      else {
        const p = Math.max(0, g.start), f = Math.min(r.count, g.start + g.count);
        for (let v = p, _ = f; v < _; v += 3) {
          const w = r.getX(v), x = r.getX(v + 1), M = r.getX(v + 2);
          o = Pi(this, i, e, Gn, l, a, c, d, u, w, x, M), o && (o.faceIndex = Math.floor(v / 3), t.push(o));
        }
      }
    else if (l !== void 0)
      if (Array.isArray(i))
        for (let p = 0, f = m.length; p < f; p++) {
          const v = m[p], _ = i[v.materialIndex], w = Math.max(v.start, g.start), x = Math.min(l.count, Math.min(v.start + v.count, g.start + g.count));
          for (let M = w, E = x; M < E; M += 3) {
            const R = M, y = M + 1, A = M + 2;
            o = Pi(this, _, e, Gn, l, a, c, d, u, R, y, A), o && (o.faceIndex = Math.floor(M / 3), o.face.materialIndex = v.materialIndex, t.push(o));
          }
        }
      else {
        const p = Math.max(0, g.start), f = Math.min(l.count, g.start + g.count);
        for (let v = p, _ = f; v < _; v += 3) {
          const w = v, x = v + 1, M = v + 2;
          o = Pi(this, i, e, Gn, l, a, c, d, u, w, x, M), o && (o.faceIndex = Math.floor(v / 3), t.push(o));
        }
      }
  }
}
function $o(h, e, t, n, i, s, o, r) {
  let l;
  if (e.side === 1 ? l = n.intersectTriangle(o, s, i, !0, r) : l = n.intersectTriangle(i, s, o, e.side !== 2, r), l === null)
    return null;
  Di.copy(r), Di.applyMatrix4(h.matrixWorld);
  const a = t.ray.origin.distanceTo(Di);
  return a < t.near || a > t.far ? null : {
    distance: a,
    point: Di.clone(),
    object: h
  };
}
function Pi(h, e, t, n, i, s, o, r, l, a, c, d) {
  an.fromBufferAttribute(i, a), ln.fromBufferAttribute(i, c), cn.fromBufferAttribute(i, d);
  const u = h.morphTargetInfluences;
  if (s && u) {
    Ti.set(0, 0, 0), Ai.set(0, 0, 0), Ci.set(0, 0, 0);
    for (let g = 0, p = s.length; g < p; g++) {
      const f = u[g], v = s[g];
      f !== 0 && (_s.fromBufferAttribute(v, a), vs.fromBufferAttribute(v, c), xs.fromBufferAttribute(v, d), o ? (Ti.addScaledVector(_s, f), Ai.addScaledVector(vs, f), Ci.addScaledVector(xs, f)) : (Ti.addScaledVector(_s.sub(an), f), Ai.addScaledVector(vs.sub(ln), f), Ci.addScaledVector(xs.sub(cn), f)));
    }
    an.add(Ti), ln.add(Ai), cn.add(Ci);
  }
  h.isSkinnedMesh && (h.boneTransform(a, an), h.boneTransform(c, ln), h.boneTransform(d, cn));
  const m = $o(h, e, t, n, an, ln, cn, ys);
  if (m) {
    r && (Li.fromBufferAttribute(r, a), Ri.fromBufferAttribute(r, c), Fi.fromBufferAttribute(r, d), m.uv = Qt.getUV(ys, an, ln, cn, Li, Ri, Fi, new Ce())), l && (Li.fromBufferAttribute(l, a), Ri.fromBufferAttribute(l, c), Fi.fromBufferAttribute(l, d), m.uv2 = Qt.getUV(ys, an, ln, cn, Li, Ri, Fi, new Ce()));
    const g = {
      a,
      b: c,
      c: d,
      normal: new O(),
      materialIndex: 0
    };
    Qt.getNormal(an, ln, cn, g.normal), m.face = g;
  }
  return m;
}
class pi extends Ut {
  constructor(e = 1, t = 1, n = 1, i = 1, s = 1, o = 1) {
    super(), this.type = "BoxGeometry", this.parameters = {
      width: e,
      height: t,
      depth: n,
      widthSegments: i,
      heightSegments: s,
      depthSegments: o
    };
    const r = this;
    i = Math.floor(i), s = Math.floor(s), o = Math.floor(o);
    const l = [], a = [], c = [], d = [];
    let u = 0, m = 0;
    g("z", "y", "x", -1, -1, n, t, e, o, s, 0), g("z", "y", "x", 1, -1, n, t, -e, o, s, 1), g("x", "z", "y", 1, 1, e, n, t, i, o, 2), g("x", "z", "y", 1, -1, e, n, -t, i, o, 3), g("x", "y", "z", 1, -1, e, t, n, i, s, 4), g("x", "y", "z", -1, -1, e, t, -n, i, s, 5), this.setIndex(l), this.setAttribute("position", new st(a, 3)), this.setAttribute("normal", new st(c, 3)), this.setAttribute("uv", new st(d, 2));
    function g(p, f, v, _, w, x, M, E, R, y, A) {
      const F = x / R, P = M / y, G = x / 2, z = M / 2, L = E / 2, I = R + 1, D = y + 1;
      let q = 0, k = 0;
      const N = new O();
      for (let H = 0; H < D; H++) {
        const J = H * P - z;
        for (let V = 0; V < I; V++) {
          const ee = V * F - G;
          N[p] = ee * _, N[f] = J * w, N[v] = L, a.push(N.x, N.y, N.z), N[p] = 0, N[f] = 0, N[v] = E > 0 ? 1 : -1, c.push(N.x, N.y, N.z), d.push(V / R), d.push(1 - H / y), q += 1;
        }
      }
      for (let H = 0; H < y; H++)
        for (let J = 0; J < R; J++) {
          const V = u + J + I * H, ee = u + J + I * (H + 1), ce = u + (J + 1) + I * (H + 1), ge = u + (J + 1) + I * H;
          l.push(V, ee, ge), l.push(ee, ce, ge), k += 6;
        }
      r.addGroup(m, k, A), m += k, u += q;
    }
  }
  static fromJSON(e) {
    return new pi(e.width, e.height, e.depth, e.widthSegments, e.heightSegments, e.depthSegments);
  }
}
function Zn(h) {
  const e = {};
  for (const t in h) {
    e[t] = {};
    for (const n in h[t]) {
      const i = h[t][n];
      i && (i.isColor || i.isMatrix3 || i.isMatrix4 || i.isVector2 || i.isVector3 || i.isVector4 || i.isTexture || i.isQuaternion) ? e[t][n] = i.clone() : Array.isArray(i) ? e[t][n] = i.slice() : e[t][n] = i;
    }
  }
  return e;
}
function it(h) {
  const e = {};
  for (let t = 0; t < h.length; t++) {
    const n = Zn(h[t]);
    for (const i in n)
      e[i] = n[i];
  }
  return e;
}
function Ko(h) {
  const e = [];
  for (let t = 0; t < h.length; t++)
    e.push(h[t].clone());
  return e;
}
const Jo = { clone: Zn, merge: it };
var Qo = `void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`, ea = `void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;
class Tn extends An {
  constructor(e) {
    super(), this.isShaderMaterial = !0, this.type = "ShaderMaterial", this.defines = {}, this.uniforms = {}, this.uniformsGroups = [], this.vertexShader = Qo, this.fragmentShader = ea, this.linewidth = 1, this.wireframe = !1, this.wireframeLinewidth = 1, this.fog = !1, this.lights = !1, this.clipping = !1, this.extensions = {
      derivatives: !1,
      fragDepth: !1,
      drawBuffers: !1,
      shaderTextureLOD: !1
    }, this.defaultAttributeValues = {
      color: [1, 1, 1],
      uv: [0, 0],
      uv2: [0, 0]
    }, this.index0AttributeName = void 0, this.uniformsNeedUpdate = !1, this.glslVersion = null, e !== void 0 && (e.attributes !== void 0 && console.error("THREE.ShaderMaterial: attributes should now be defined in THREE.BufferGeometry instead."), this.setValues(e));
  }
  copy(e) {
    return super.copy(e), this.fragmentShader = e.fragmentShader, this.vertexShader = e.vertexShader, this.uniforms = Zn(e.uniforms), this.uniformsGroups = Ko(e.uniformsGroups), this.defines = Object.assign({}, e.defines), this.wireframe = e.wireframe, this.wireframeLinewidth = e.wireframeLinewidth, this.fog = e.fog, this.lights = e.lights, this.clipping = e.clipping, this.extensions = Object.assign({}, e.extensions), this.glslVersion = e.glslVersion, this;
  }
  toJSON(e) {
    const t = super.toJSON(e);
    t.glslVersion = this.glslVersion, t.uniforms = {};
    for (const i in this.uniforms) {
      const o = this.uniforms[i].value;
      o && o.isTexture ? t.uniforms[i] = {
        type: "t",
        value: o.toJSON(e).uuid
      } : o && o.isColor ? t.uniforms[i] = {
        type: "c",
        value: o.getHex()
      } : o && o.isVector2 ? t.uniforms[i] = {
        type: "v2",
        value: o.toArray()
      } : o && o.isVector3 ? t.uniforms[i] = {
        type: "v3",
        value: o.toArray()
      } : o && o.isVector4 ? t.uniforms[i] = {
        type: "v4",
        value: o.toArray()
      } : o && o.isMatrix3 ? t.uniforms[i] = {
        type: "m3",
        value: o.toArray()
      } : o && o.isMatrix4 ? t.uniforms[i] = {
        type: "m4",
        value: o.toArray()
      } : t.uniforms[i] = {
        value: o
      };
    }
    Object.keys(this.defines).length > 0 && (t.defines = this.defines), t.vertexShader = this.vertexShader, t.fragmentShader = this.fragmentShader;
    const n = {};
    for (const i in this.extensions)
      this.extensions[i] === !0 && (n[i] = !0);
    return Object.keys(n).length > 0 && (t.extensions = n), t;
  }
}
class ho extends at {
  constructor() {
    super(), this.isCamera = !0, this.type = "Camera", this.matrixWorldInverse = new Ke(), this.projectionMatrix = new Ke(), this.projectionMatrixInverse = new Ke();
  }
  copy(e, t) {
    return super.copy(e, t), this.matrixWorldInverse.copy(e.matrixWorldInverse), this.projectionMatrix.copy(e.projectionMatrix), this.projectionMatrixInverse.copy(e.projectionMatrixInverse), this;
  }
  getWorldDirection(e) {
    this.updateWorldMatrix(!0, !1);
    const t = this.matrixWorld.elements;
    return e.set(-t[8], -t[9], -t[10]).normalize();
  }
  updateMatrixWorld(e) {
    super.updateMatrixWorld(e), this.matrixWorldInverse.copy(this.matrixWorld).invert();
  }
  updateWorldMatrix(e, t) {
    super.updateWorldMatrix(e, t), this.matrixWorldInverse.copy(this.matrixWorld).invert();
  }
  clone() {
    return new this.constructor().copy(this);
  }
}
class gt extends ho {
  constructor(e = 50, t = 1, n = 0.1, i = 2e3) {
    super(), this.isPerspectiveCamera = !0, this.type = "PerspectiveCamera", this.fov = e, this.zoom = 1, this.near = n, this.far = i, this.focus = 10, this.aspect = t, this.view = null, this.filmGauge = 35, this.filmOffset = 0, this.updateProjectionMatrix();
  }
  copy(e, t) {
    return super.copy(e, t), this.fov = e.fov, this.zoom = e.zoom, this.near = e.near, this.far = e.far, this.focus = e.focus, this.aspect = e.aspect, this.view = e.view === null ? null : Object.assign({}, e.view), this.filmGauge = e.filmGauge, this.filmOffset = e.filmOffset, this;
  }
  setFocalLength(e) {
    const t = 0.5 * this.getFilmHeight() / e;
    this.fov = zs * 2 * Math.atan(t), this.updateProjectionMatrix();
  }
  getFocalLength() {
    const e = Math.tan(Qi * 0.5 * this.fov);
    return 0.5 * this.getFilmHeight() / e;
  }
  getEffectiveFOV() {
    return zs * 2 * Math.atan(
      Math.tan(Qi * 0.5 * this.fov) / this.zoom
    );
  }
  getFilmWidth() {
    return this.filmGauge * Math.min(this.aspect, 1);
  }
  getFilmHeight() {
    return this.filmGauge / Math.max(this.aspect, 1);
  }
  setViewOffset(e, t, n, i, s, o) {
    this.aspect = e / t, this.view === null && (this.view = {
      enabled: !0,
      fullWidth: 1,
      fullHeight: 1,
      offsetX: 0,
      offsetY: 0,
      width: 1,
      height: 1
    }), this.view.enabled = !0, this.view.fullWidth = e, this.view.fullHeight = t, this.view.offsetX = n, this.view.offsetY = i, this.view.width = s, this.view.height = o, this.updateProjectionMatrix();
  }
  clearViewOffset() {
    this.view !== null && (this.view.enabled = !1), this.updateProjectionMatrix();
  }
  updateProjectionMatrix() {
    const e = this.near;
    let t = e * Math.tan(Qi * 0.5 * this.fov) / this.zoom, n = 2 * t, i = this.aspect * n, s = -0.5 * i;
    const o = this.view;
    if (this.view !== null && this.view.enabled) {
      const l = o.fullWidth, a = o.fullHeight;
      s += o.offsetX * i / l, t -= o.offsetY * n / a, i *= o.width / l, n *= o.height / a;
    }
    const r = this.filmOffset;
    r !== 0 && (s += e * r / this.getFilmWidth()), this.projectionMatrix.makePerspective(s, s + i, t, t - n, e, this.far), this.projectionMatrixInverse.copy(this.projectionMatrix).invert();
  }
  toJSON(e) {
    const t = super.toJSON(e);
    return t.object.fov = this.fov, t.object.zoom = this.zoom, t.object.near = this.near, t.object.far = this.far, t.object.focus = this.focus, t.object.aspect = this.aspect, this.view !== null && (t.object.view = Object.assign({}, this.view)), t.object.filmGauge = this.filmGauge, t.object.filmOffset = this.filmOffset, t;
  }
}
const kn = 90, Wn = 1;
class ta extends at {
  constructor(e, t, n) {
    if (super(), this.type = "CubeCamera", n.isWebGLCubeRenderTarget !== !0) {
      console.error("THREE.CubeCamera: The constructor now expects an instance of WebGLCubeRenderTarget as third parameter.");
      return;
    }
    this.renderTarget = n;
    const i = new gt(kn, Wn, e, t);
    i.layers = this.layers, i.up.set(0, -1, 0), i.lookAt(new O(1, 0, 0)), this.add(i);
    const s = new gt(kn, Wn, e, t);
    s.layers = this.layers, s.up.set(0, -1, 0), s.lookAt(new O(-1, 0, 0)), this.add(s);
    const o = new gt(kn, Wn, e, t);
    o.layers = this.layers, o.up.set(0, 0, 1), o.lookAt(new O(0, 1, 0)), this.add(o);
    const r = new gt(kn, Wn, e, t);
    r.layers = this.layers, r.up.set(0, 0, -1), r.lookAt(new O(0, -1, 0)), this.add(r);
    const l = new gt(kn, Wn, e, t);
    l.layers = this.layers, l.up.set(0, -1, 0), l.lookAt(new O(0, 0, 1)), this.add(l);
    const a = new gt(kn, Wn, e, t);
    a.layers = this.layers, a.up.set(0, -1, 0), a.lookAt(new O(0, 0, -1)), this.add(a);
  }
  update(e, t) {
    this.parent === null && this.updateMatrixWorld();
    const n = this.renderTarget, [i, s, o, r, l, a] = this.children, c = e.getRenderTarget(), d = e.toneMapping, u = e.xr.enabled;
    e.toneMapping = 0, e.xr.enabled = !1;
    const m = n.texture.generateMipmaps;
    n.texture.generateMipmaps = !1, e.setRenderTarget(n, 0), e.render(t, i), e.setRenderTarget(n, 1), e.render(t, s), e.setRenderTarget(n, 2), e.render(t, o), e.setRenderTarget(n, 3), e.render(t, r), e.setRenderTarget(n, 4), e.render(t, l), n.texture.generateMipmaps = m, e.setRenderTarget(n, 5), e.render(t, a), e.setRenderTarget(c), e.toneMapping = d, e.xr.enabled = u, n.texture.needsPMREMUpdate = !0;
  }
}
class uo extends _t {
  constructor(e, t, n, i, s, o, r, l, a, c) {
    e = e !== void 0 ? e : [], t = t !== void 0 ? t : 301, super(e, t, n, i, s, o, r, l, a, c), this.isCubeTexture = !0, this.flipY = !1;
  }
  get images() {
    return this.image;
  }
  set images(e) {
    this.image = e;
  }
}
class na extends En {
  constructor(e, t = {}) {
    super(e, e, t), this.isWebGLCubeRenderTarget = !0;
    const n = { width: e, height: e, depth: 1 }, i = [n, n, n, n, n, n];
    this.texture = new uo(i, t.mapping, t.wrapS, t.wrapT, t.magFilter, t.minFilter, t.format, t.type, t.anisotropy, t.encoding), this.texture.isRenderTargetTexture = !0, this.texture.generateMipmaps = t.generateMipmaps !== void 0 ? t.generateMipmaps : !1, this.texture.minFilter = t.minFilter !== void 0 ? t.minFilter : 1006;
  }
  fromEquirectangularTexture(e, t) {
    this.texture.type = t.type, this.texture.encoding = t.encoding, this.texture.generateMipmaps = t.generateMipmaps, this.texture.minFilter = t.minFilter, this.texture.magFilter = t.magFilter;
    const n = {
      uniforms: {
        tEquirect: { value: null }
      },
      vertexShader: `

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,
      fragmentShader: `

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`
    }, i = new pi(5, 5, 5), s = new Tn({
      name: "CubemapFromEquirect",
      uniforms: Zn(n.uniforms),
      vertexShader: n.vertexShader,
      fragmentShader: n.fragmentShader,
      side: 1,
      blending: 0
    });
    s.uniforms.tEquirect.value = t;
    const o = new Nt(i, s), r = t.minFilter;
    return t.minFilter === 1008 && (t.minFilter = 1006), new ta(1, 10, this).update(e, o), t.minFilter = r, o.geometry.dispose(), o.material.dispose(), this;
  }
  clear(e, t, n, i) {
    const s = e.getRenderTarget();
    for (let o = 0; o < 6; o++)
      e.setRenderTarget(this, o), e.clear(t, n, i);
    e.setRenderTarget(s);
  }
}
const bs = /* @__PURE__ */ new O(), ia = /* @__PURE__ */ new O(), sa = /* @__PURE__ */ new Mt();
class gn {
  constructor(e = new O(1, 0, 0), t = 0) {
    this.isPlane = !0, this.normal = e, this.constant = t;
  }
  set(e, t) {
    return this.normal.copy(e), this.constant = t, this;
  }
  setComponents(e, t, n, i) {
    return this.normal.set(e, t, n), this.constant = i, this;
  }
  setFromNormalAndCoplanarPoint(e, t) {
    return this.normal.copy(e), this.constant = -t.dot(this.normal), this;
  }
  setFromCoplanarPoints(e, t, n) {
    const i = bs.subVectors(n, t).cross(ia.subVectors(e, t)).normalize();
    return this.setFromNormalAndCoplanarPoint(i, e), this;
  }
  copy(e) {
    return this.normal.copy(e.normal), this.constant = e.constant, this;
  }
  normalize() {
    const e = 1 / this.normal.length();
    return this.normal.multiplyScalar(e), this.constant *= e, this;
  }
  negate() {
    return this.constant *= -1, this.normal.negate(), this;
  }
  distanceToPoint(e) {
    return this.normal.dot(e) + this.constant;
  }
  distanceToSphere(e) {
    return this.distanceToPoint(e.center) - e.radius;
  }
  projectPoint(e, t) {
    return t.copy(this.normal).multiplyScalar(-this.distanceToPoint(e)).add(e);
  }
  intersectLine(e, t) {
    const n = e.delta(bs), i = this.normal.dot(n);
    if (i === 0)
      return this.distanceToPoint(e.start) === 0 ? t.copy(e.start) : null;
    const s = -(e.start.dot(this.normal) + this.constant) / i;
    return s < 0 || s > 1 ? null : t.copy(n).multiplyScalar(s).add(e.start);
  }
  intersectsLine(e) {
    const t = this.distanceToPoint(e.start), n = this.distanceToPoint(e.end);
    return t < 0 && n > 0 || n < 0 && t > 0;
  }
  intersectsBox(e) {
    return e.intersectsPlane(this);
  }
  intersectsSphere(e) {
    return e.intersectsPlane(this);
  }
  coplanarPoint(e) {
    return e.copy(this.normal).multiplyScalar(-this.constant);
  }
  applyMatrix4(e, t) {
    const n = t || sa.getNormalMatrix(e), i = this.coplanarPoint(bs).applyMatrix4(e), s = this.normal.applyMatrix3(n).normalize();
    return this.constant = -i.dot(s), this;
  }
  translate(e) {
    return this.constant -= e.dot(this.normal), this;
  }
  equals(e) {
    return e.normal.equals(this.normal) && e.constant === this.constant;
  }
  clone() {
    return new this.constructor().copy(this);
  }
}
const Vn = /* @__PURE__ */ new ci(), Ii = /* @__PURE__ */ new O();
class Us {
  constructor(e = new gn(), t = new gn(), n = new gn(), i = new gn(), s = new gn(), o = new gn()) {
    this.planes = [e, t, n, i, s, o];
  }
  set(e, t, n, i, s, o) {
    const r = this.planes;
    return r[0].copy(e), r[1].copy(t), r[2].copy(n), r[3].copy(i), r[4].copy(s), r[5].copy(o), this;
  }
  copy(e) {
    const t = this.planes;
    for (let n = 0; n < 6; n++)
      t[n].copy(e.planes[n]);
    return this;
  }
  setFromProjectionMatrix(e) {
    const t = this.planes, n = e.elements, i = n[0], s = n[1], o = n[2], r = n[3], l = n[4], a = n[5], c = n[6], d = n[7], u = n[8], m = n[9], g = n[10], p = n[11], f = n[12], v = n[13], _ = n[14], w = n[15];
    return t[0].setComponents(r - i, d - l, p - u, w - f).normalize(), t[1].setComponents(r + i, d + l, p + u, w + f).normalize(), t[2].setComponents(r + s, d + a, p + m, w + v).normalize(), t[3].setComponents(r - s, d - a, p - m, w - v).normalize(), t[4].setComponents(r - o, d - c, p - g, w - _).normalize(), t[5].setComponents(r + o, d + c, p + g, w + _).normalize(), this;
  }
  intersectsObject(e) {
    const t = e.geometry;
    return t.boundingSphere === null && t.computeBoundingSphere(), Vn.copy(t.boundingSphere).applyMatrix4(e.matrixWorld), this.intersectsSphere(Vn);
  }
  intersectsSprite(e) {
    return Vn.center.set(0, 0, 0), Vn.radius = 0.7071067811865476, Vn.applyMatrix4(e.matrixWorld), this.intersectsSphere(Vn);
  }
  intersectsSphere(e) {
    const t = this.planes, n = e.center, i = -e.radius;
    for (let s = 0; s < 6; s++)
      if (t[s].distanceToPoint(n) < i)
        return !1;
    return !0;
  }
  intersectsBox(e) {
    const t = this.planes;
    for (let n = 0; n < 6; n++) {
      const i = t[n];
      if (Ii.x = i.normal.x > 0 ? e.max.x : e.min.x, Ii.y = i.normal.y > 0 ? e.max.y : e.min.y, Ii.z = i.normal.z > 0 ? e.max.z : e.min.z, i.distanceToPoint(Ii) < 0)
        return !1;
    }
    return !0;
  }
  containsPoint(e) {
    const t = this.planes;
    for (let n = 0; n < 6; n++)
      if (t[n].distanceToPoint(e) < 0)
        return !1;
    return !0;
  }
  clone() {
    return new this.constructor().copy(this);
  }
}
function fo() {
  let h = null, e = !1, t = null, n = null;
  function i(s, o) {
    t(s, o), n = h.requestAnimationFrame(i);
  }
  return {
    start: function() {
      e !== !0 && t !== null && (n = h.requestAnimationFrame(i), e = !0);
    },
    stop: function() {
      h.cancelAnimationFrame(n), e = !1;
    },
    setAnimationLoop: function(s) {
      t = s;
    },
    setContext: function(s) {
      h = s;
    }
  };
}
function ra(h, e) {
  const t = e.isWebGL2, n = /* @__PURE__ */ new WeakMap();
  function i(a, c) {
    const d = a.array, u = a.usage, m = h.createBuffer();
    h.bindBuffer(c, m), h.bufferData(c, d, u), a.onUploadCallback();
    let g;
    if (d instanceof Float32Array)
      g = 5126;
    else if (d instanceof Uint16Array)
      if (a.isFloat16BufferAttribute)
        if (t)
          g = 5131;
        else
          throw new Error("THREE.WebGLAttributes: Usage of Float16BufferAttribute requires WebGL2.");
      else
        g = 5123;
    else if (d instanceof Int16Array)
      g = 5122;
    else if (d instanceof Uint32Array)
      g = 5125;
    else if (d instanceof Int32Array)
      g = 5124;
    else if (d instanceof Int8Array)
      g = 5120;
    else if (d instanceof Uint8Array)
      g = 5121;
    else if (d instanceof Uint8ClampedArray)
      g = 5121;
    else
      throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: " + d);
    return {
      buffer: m,
      type: g,
      bytesPerElement: d.BYTES_PER_ELEMENT,
      version: a.version
    };
  }
  function s(a, c, d) {
    const u = c.array, m = c.updateRange;
    h.bindBuffer(d, a), m.count === -1 ? h.bufferSubData(d, 0, u) : (t ? h.bufferSubData(
      d,
      m.offset * u.BYTES_PER_ELEMENT,
      u,
      m.offset,
      m.count
    ) : h.bufferSubData(
      d,
      m.offset * u.BYTES_PER_ELEMENT,
      u.subarray(m.offset, m.offset + m.count)
    ), m.count = -1);
  }
  function o(a) {
    return a.isInterleavedBufferAttribute && (a = a.data), n.get(a);
  }
  function r(a) {
    a.isInterleavedBufferAttribute && (a = a.data);
    const c = n.get(a);
    c && (h.deleteBuffer(c.buffer), n.delete(a));
  }
  function l(a, c) {
    if (a.isGLBufferAttribute) {
      const u = n.get(a);
      (!u || u.version < a.version) && n.set(a, {
        buffer: a.buffer,
        type: a.type,
        bytesPerElement: a.elementSize,
        version: a.version
      });
      return;
    }
    a.isInterleavedBufferAttribute && (a = a.data);
    const d = n.get(a);
    d === void 0 ? n.set(a, i(a, c)) : d.version < a.version && (s(d.buffer, a, c), d.version = a.version);
  }
  return {
    get: o,
    remove: r,
    update: l
  };
}
class ji extends Ut {
  constructor(e = 1, t = 1, n = 1, i = 1) {
    super(), this.type = "PlaneGeometry", this.parameters = {
      width: e,
      height: t,
      widthSegments: n,
      heightSegments: i
    };
    const s = e / 2, o = t / 2, r = Math.floor(n), l = Math.floor(i), a = r + 1, c = l + 1, d = e / r, u = t / l, m = [], g = [], p = [], f = [];
    for (let v = 0; v < c; v++) {
      const _ = v * u - o;
      for (let w = 0; w < a; w++) {
        const x = w * d - s;
        g.push(x, -_, 0), p.push(0, 0, 1), f.push(w / r), f.push(1 - v / l);
      }
    }
    for (let v = 0; v < l; v++)
      for (let _ = 0; _ < r; _++) {
        const w = _ + a * v, x = _ + a * (v + 1), M = _ + 1 + a * (v + 1), E = _ + 1 + a * v;
        m.push(w, x, E), m.push(x, M, E);
      }
    this.setIndex(m), this.setAttribute("position", new st(g, 3)), this.setAttribute("normal", new st(p, 3)), this.setAttribute("uv", new st(f, 2));
  }
  static fromJSON(e) {
    return new ji(e.width, e.height, e.widthSegments, e.heightSegments);
  }
}
var oa = `#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vUv ).g;
#endif`, aa = `#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`, la = `#ifdef USE_ALPHATEST
	if ( diffuseColor.a < alphaTest ) discard;
#endif`, ca = `#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`, ha = `#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vUv2 ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometry.normal, geometry.viewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`, ua = `#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`, da = "vec3 transformed = vec3( position );", fa = `vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`, pa = `vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 f0, const in float f90, const in float roughness ) {
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
	float D = D_GGX( alpha, dotNH );
	return F * ( V * D );
}
#ifdef USE_IRIDESCENCE
	vec3 BRDF_GGX_Iridescence( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 f0, const in float f90, const in float iridescence, const in vec3 iridescenceFresnel, const in float roughness ) {
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = mix( F_Schlick( f0, f90, dotVH ), iridescenceFresnel, iridescence );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transposeMat3( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif`, ma = `#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			 return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float R21 = R12;
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`, ga = `#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vUv );
		vec2 dSTdy = dFdy( vUv );
		float Hll = bumpScale * texture2D( bumpMap, vUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = dFdx( surf_pos.xyz );
		vec3 vSigmaY = dFdy( surf_pos.xyz );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`, _a = `#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#pragma unroll_loop_start
	for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
		plane = clippingPlanes[ i ];
		if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
	}
	#pragma unroll_loop_end
	#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
		bool clipped = true;
		#pragma unroll_loop_start
		for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
		}
		#pragma unroll_loop_end
		if ( clipped ) discard;
	#endif
#endif`, va = `#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`, xa = `#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`, ya = `#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`, ba = `#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`, wa = `#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`, Ma = `#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR )
	varying vec3 vColor;
#endif`, Sa = `#if defined( USE_COLOR_ALPHA )
	vColor = vec4( 1.0 );
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR )
	vColor = vec3( 1.0 );
#endif
#ifdef USE_COLOR
	vColor *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.xyz *= instanceColor.xyz;
#endif`, Ea = `#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
struct GeometricContext {
	vec3 position;
	vec3 normal;
	vec3 viewDir;
#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal;
#endif
};
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
mat3 transposeMat3( const in mat3 m ) {
	mat3 tmp;
	tmp[ 0 ] = vec3( m[ 0 ].x, m[ 1 ].x, m[ 2 ].x );
	tmp[ 1 ] = vec3( m[ 0 ].y, m[ 1 ].y, m[ 2 ].y );
	tmp[ 2 ] = vec3( m[ 0 ].z, m[ 1 ].z, m[ 2 ].z );
	return tmp;
}
float luminance( const in vec3 rgb ) {
	const vec3 weights = vec3( 0.2126729, 0.7151522, 0.0721750 );
	return dot( weights, rgb );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}`, Ta = `#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define r0 1.0
	#define v0 0.339
	#define m0 - 2.0
	#define r1 0.8
	#define v1 0.276
	#define m1 - 1.0
	#define r4 0.4
	#define v4 0.046
	#define m4 2.0
	#define r5 0.305
	#define v5 0.016
	#define m5 3.0
	#define r6 0.21
	#define v6 0.0038
	#define m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= r1 ) {
			mip = ( r0 - roughness ) * ( m1 - m0 ) / ( r0 - r1 ) + m0;
		} else if ( roughness >= r4 ) {
			mip = ( r1 - roughness ) * ( m4 - m1 ) / ( r1 - r4 ) + m1;
		} else if ( roughness >= r5 ) {
			mip = ( r4 - roughness ) * ( m5 - m4 ) / ( r4 - r5 ) + m4;
		} else if ( roughness >= r6 ) {
			mip = ( r5 - roughness ) * ( m6 - m5 ) / ( r5 - r6 ) + m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`, Aa = `vec3 transformedNormal = objectNormal;
#ifdef USE_INSTANCING
	mat3 m = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( m[ 0 ], m[ 0 ] ), dot( m[ 1 ], m[ 1 ] ), dot( m[ 2 ], m[ 2 ] ) );
	transformedNormal = m * transformedNormal;
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	vec3 transformedTangent = ( modelViewMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`, Ca = `#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`, La = `#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vUv ).x * displacementScale + displacementBias );
#endif`, Ra = `#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vUv );
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`, Fa = `#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`, Da = "gl_FragColor = linearToOutputTexel( gl_FragColor );", Pa = `vec4 LinearToLinear( in vec4 value ) {
	return value;
}
vec4 LinearTosRGB( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`, Ia = `#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 envColor = textureCubeUV( envMap, reflectVec, 0.0 );
	#else
		vec4 envColor = vec4( 0.0 );
	#endif
	#ifdef ENVMAP_BLENDING_MULTIPLY
		outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_MIX )
		outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_ADD )
		outgoingLight += envColor.xyz * specularStrength * reflectivity;
	#endif
#endif`, za = `#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
	
#endif`, Ba = `#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`, Na = `#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) ||defined( PHONG )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`, Oa = `#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`, Ua = `#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`, Ga = `#ifdef USE_FOG
	varying float vFogDepth;
#endif`, ka = `#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`, Wa = `#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`, Va = `#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		return ( coord.x < 0.7 ) ? vec3( 0.7 ) : vec3( 1.0 );
	#endif
}`, Ha = `#ifdef USE_LIGHTMAP
	vec4 lightMapTexel = texture2D( lightMap, vUv2 );
	vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
	reflectedLight.indirectDiffuse += lightMapIrradiance;
#endif`, qa = `#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`, Xa = `vec3 diffuse = vec3( 1.0 );
GeometricContext geometry;
geometry.position = mvPosition.xyz;
geometry.normal = normalize( transformedNormal );
geometry.viewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( -mvPosition.xyz );
GeometricContext backGeometry;
backGeometry.position = geometry.position;
backGeometry.normal = -geometry.normal;
backGeometry.viewDir = geometry.viewDir;
vLightFront = vec3( 0.0 );
vIndirectFront = vec3( 0.0 );
#ifdef DOUBLE_SIDED
	vLightBack = vec3( 0.0 );
	vIndirectBack = vec3( 0.0 );
#endif
IncidentLight directLight;
float dotNL;
vec3 directLightColor_Diffuse;
vIndirectFront += getAmbientLightIrradiance( ambientLightColor );
vIndirectFront += getLightProbeIrradiance( lightProbe, geometry.normal );
#ifdef DOUBLE_SIDED
	vIndirectBack += getAmbientLightIrradiance( ambientLightColor );
	vIndirectBack += getLightProbeIrradiance( lightProbe, backGeometry.normal );
#endif
#if NUM_POINT_LIGHTS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		getPointLightInfo( pointLights[ i ], geometry, directLight );
		dotNL = dot( geometry.normal, directLight.direction );
		directLightColor_Diffuse = directLight.color;
		vLightFront += saturate( dotNL ) * directLightColor_Diffuse;
		#ifdef DOUBLE_SIDED
			vLightBack += saturate( - dotNL ) * directLightColor_Diffuse;
		#endif
	}
	#pragma unroll_loop_end
#endif
#if NUM_SPOT_LIGHTS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		getSpotLightInfo( spotLights[ i ], geometry, directLight );
		dotNL = dot( geometry.normal, directLight.direction );
		directLightColor_Diffuse = directLight.color;
		vLightFront += saturate( dotNL ) * directLightColor_Diffuse;
		#ifdef DOUBLE_SIDED
			vLightBack += saturate( - dotNL ) * directLightColor_Diffuse;
		#endif
	}
	#pragma unroll_loop_end
#endif
#if NUM_DIR_LIGHTS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		getDirectionalLightInfo( directionalLights[ i ], geometry, directLight );
		dotNL = dot( geometry.normal, directLight.direction );
		directLightColor_Diffuse = directLight.color;
		vLightFront += saturate( dotNL ) * directLightColor_Diffuse;
		#ifdef DOUBLE_SIDED
			vLightBack += saturate( - dotNL ) * directLightColor_Diffuse;
		#endif
	}
	#pragma unroll_loop_end
#endif
#if NUM_HEMI_LIGHTS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
		vIndirectFront += getHemisphereLightIrradiance( hemisphereLights[ i ], geometry.normal );
		#ifdef DOUBLE_SIDED
			vIndirectBack += getHemisphereLightIrradiance( hemisphereLights[ i ], backGeometry.normal );
		#endif
	}
	#pragma unroll_loop_end
#endif`, ja = `uniform bool receiveShadow;
uniform vec3 ambientLightColor;
uniform vec3 lightProbe[ 9 ];
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	#if defined ( PHYSICALLY_CORRECT_LIGHTS )
		float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
		if ( cutoffDistance > 0.0 ) {
			distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
		}
		return distanceFalloff;
	#else
		if ( cutoffDistance > 0.0 && decayExponent > 0.0 ) {
			return pow( saturate( - lightDistance / cutoffDistance + 1.0 ), decayExponent );
		}
		return 1.0;
	#endif
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, const in GeometricContext geometry, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in GeometricContext geometry, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometry.position;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in GeometricContext geometry, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometry.position;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`, Ya = `#if defined( USE_ENVMAP )
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#if defined( ENVMAP_TYPE_CUBE_UV )
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#if defined( ENVMAP_TYPE_CUBE_UV )
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, roughness * roughness) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
#endif`, Za = `ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`, $a = `varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in GeometricContext geometry, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometry.normal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in GeometricContext geometry, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon
#define Material_LightProbeLOD( material )	(0)`, Ka = `BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`, Ja = `varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in GeometricContext geometry, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometry.normal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometry.viewDir, geometry.normal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in GeometricContext geometry, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong
#define Material_LightProbeLOD( material )	(0)`, Qa = `PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb * ( 1.0 - metalnessFactor );
vec3 dxy = max( abs( dFdx( geometryNormal ) ), abs( dFdy( geometryNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	#ifdef SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULARINTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vUv ).a;
		#endif
		#ifdef USE_SPECULARCOLORMAP
			specularColorFactor *= texture2D( specularColorMap, vUv ).rgb;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = mix( min( pow2( ( ior - 1.0 ) / ( ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = mix( vec3( 0.04 ), diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEENCOLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.07, 1.0 );
	#ifdef USE_SHEENROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vUv ).a;
	#endif
#endif`, el = `struct PhysicalMaterial {
	vec3 diffuseColor;
	float roughness;
	vec3 specularColor;
	float specularF90;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
};
vec3 clearcoatSpecular = vec3( 0.0 );
vec3 sheenSpecular = vec3( 0.0 );
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float a = roughness < 0.25 ? -339.2 * r2 + 161.4 * roughness - 25.9 : -8.48 * r2 + 14.3 * roughness - 9.95;
	float b = roughness < 0.25 ? 44.0 * r2 - 23.7 * roughness + 3.26 : 1.97 * r2 - 3.27 * roughness + 0.72;
	float DG = exp( a * dotNV + b ) + ( roughness < 0.25 ? 0.0 : 0.1 * ( roughness - 0.25 ) );
	return saturate( DG * RECIPROCAL_PI );
}
vec2 DFGApprox( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	const vec4 c0 = vec4( - 1, - 0.0275, - 0.572, 0.022 );
	const vec4 c1 = vec4( 1, 0.0425, 1.04, - 0.04 );
	vec4 r = roughness * c0 + c1;
	float a004 = min( r.x * r.x, exp2( - 9.28 * dotNV ) ) * r.x + r.y;
	vec2 fab = vec2( - 1.04, 1.04 ) * a004 + r.zw;
	return fab;
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in GeometricContext geometry, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometry.normal;
		vec3 viewDir = geometry.viewDir;
		vec3 position = geometry.position;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColor * t2.x + ( vec3( 1.0 ) - material.specularColor ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseColor * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in GeometricContext geometry, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometry.normal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometry.clearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecular += ccIrradiance * BRDF_GGX( directLight.direction, geometry.viewDir, geometry.clearcoatNormal, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecular += irradiance * BRDF_Sheen( directLight.direction, geometry.viewDir, geometry.normal, material.sheenColor, material.sheenRoughness );
	#endif
	#ifdef USE_IRIDESCENCE
		reflectedLight.directSpecular += irradiance * BRDF_GGX_Iridescence( directLight.direction, geometry.viewDir, geometry.normal, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnel, material.roughness );
	#else
		reflectedLight.directSpecular += irradiance * BRDF_GGX( directLight.direction, geometry.viewDir, geometry.normal, material.specularColor, material.specularF90, material.roughness );
	#endif
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in GeometricContext geometry, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in GeometricContext geometry, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecular += clearcoatRadiance * EnvironmentBRDF( geometry.clearcoatNormal, geometry.viewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecular += irradiance * material.sheenColor * IBLSheenBRDF( geometry.normal, geometry.viewDir, material.sheenRoughness );
	#endif
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometry.normal, geometry.viewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnel, material.roughness, singleScattering, multiScattering );
	#else
		computeMultiscattering( geometry.normal, geometry.viewDir, material.specularColor, material.specularF90, material.roughness, singleScattering, multiScattering );
	#endif
	vec3 totalScattering = singleScattering + multiScattering;
	vec3 diffuse = material.diffuseColor * ( 1.0 - max( max( totalScattering.r, totalScattering.g ), totalScattering.b ) );
	reflectedLight.indirectSpecular += radiance * singleScattering;
	reflectedLight.indirectSpecular += multiScattering * cosineWeightedIrradiance;
	reflectedLight.indirectDiffuse += diffuse * cosineWeightedIrradiance;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`, tl = `
GeometricContext geometry;
geometry.position = - vViewPosition;
geometry.normal = normal;
geometry.viewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
#ifdef USE_CLEARCOAT
	geometry.clearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometry.viewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnel = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometry, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= all( bvec2( directLight.visible, receiveShadow ) ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometry, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometry, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= all( bvec2( directLight.visible, receiveShadow ) ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometry, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, geometry, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= all( bvec2( directLight.visible, receiveShadow ) ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometry, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometry, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	irradiance += getLightProbeIrradiance( lightProbe, geometry.normal );
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometry.normal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`, nl = `#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vUv2 );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD ) && defined( ENVMAP_TYPE_CUBE_UV )
		iblIrradiance += getIBLIrradiance( geometry.normal );
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	radiance += getIBLRadiance( geometry.viewDir, geometry.normal, material.roughness );
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometry.viewDir, geometry.clearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`, il = `#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometry, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometry, material, reflectedLight );
#endif`, sl = `#if defined( USE_LOGDEPTHBUF ) && defined( USE_LOGDEPTHBUF_EXT )
	gl_FragDepthEXT = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`, rl = `#if defined( USE_LOGDEPTHBUF ) && defined( USE_LOGDEPTHBUF_EXT )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`, ol = `#ifdef USE_LOGDEPTHBUF
	#ifdef USE_LOGDEPTHBUF_EXT
		varying float vFragDepth;
		varying float vIsPerspective;
	#else
		uniform float logDepthBufFC;
	#endif
#endif`, al = `#ifdef USE_LOGDEPTHBUF
	#ifdef USE_LOGDEPTHBUF_EXT
		vFragDepth = 1.0 + gl_Position.w;
		vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
	#else
		if ( isPerspectiveMatrix( projectionMatrix ) ) {
			gl_Position.z = log2( max( EPSILON, gl_Position.w + 1.0 ) ) * logDepthBufFC - 1.0;
			gl_Position.z *= gl_Position.w;
		}
	#endif
#endif`, ll = `#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = vec4( mix( pow( sampledDiffuseColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), sampledDiffuseColor.rgb * 0.0773993808, vec3( lessThanEqual( sampledDiffuseColor.rgb, vec3( 0.04045 ) ) ) ), sampledDiffuseColor.w );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`, cl = `#ifdef USE_MAP
	uniform sampler2D map;
#endif`, hl = `#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`, ul = `#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	uniform mat3 uvTransform;
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`, dl = `float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vUv );
	metalnessFactor *= texelMetalness.b;
#endif`, fl = `#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`, pl = `#if defined( USE_MORPHCOLORS ) && defined( MORPHTARGETS_TEXTURE )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`, ml = `#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	#ifdef MORPHTARGETS_TEXTURE
		for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
			if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
		}
	#else
		objectNormal += morphNormal0 * morphTargetInfluences[ 0 ];
		objectNormal += morphNormal1 * morphTargetInfluences[ 1 ];
		objectNormal += morphNormal2 * morphTargetInfluences[ 2 ];
		objectNormal += morphNormal3 * morphTargetInfluences[ 3 ];
	#endif
#endif`, gl = `#ifdef USE_MORPHTARGETS
	uniform float morphTargetBaseInfluence;
	#ifdef MORPHTARGETS_TEXTURE
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
		uniform sampler2DArray morphTargetsTexture;
		uniform ivec2 morphTargetsTextureSize;
		vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
			int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
			int y = texelIndex / morphTargetsTextureSize.x;
			int x = texelIndex - y * morphTargetsTextureSize.x;
			ivec3 morphUV = ivec3( x, y, morphTargetIndex );
			return texelFetch( morphTargetsTexture, morphUV, 0 );
		}
	#else
		#ifndef USE_MORPHNORMALS
			uniform float morphTargetInfluences[ 8 ];
		#else
			uniform float morphTargetInfluences[ 4 ];
		#endif
	#endif
#endif`, _l = `#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	#ifdef MORPHTARGETS_TEXTURE
		for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
			if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
		}
	#else
		transformed += morphTarget0 * morphTargetInfluences[ 0 ];
		transformed += morphTarget1 * morphTargetInfluences[ 1 ];
		transformed += morphTarget2 * morphTargetInfluences[ 2 ];
		transformed += morphTarget3 * morphTargetInfluences[ 3 ];
		#ifndef USE_MORPHNORMALS
			transformed += morphTarget4 * morphTargetInfluences[ 4 ];
			transformed += morphTarget5 * morphTargetInfluences[ 5 ];
			transformed += morphTarget6 * morphTargetInfluences[ 6 ];
			transformed += morphTarget7 * morphTargetInfluences[ 7 ];
		#endif
	#endif
#endif`, vl = `float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = vec3( dFdx( vViewPosition.x ), dFdx( vViewPosition.y ), dFdx( vViewPosition.z ) );
	vec3 fdy = vec3( dFdy( vViewPosition.x ), dFdy( vViewPosition.y ), dFdy( vViewPosition.z ) );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	#ifdef USE_TANGENT
		vec3 tangent = normalize( vTangent );
		vec3 bitangent = normalize( vBitangent );
		#ifdef DOUBLE_SIDED
			tangent = tangent * faceDirection;
			bitangent = bitangent * faceDirection;
		#endif
		#if defined( TANGENTSPACE_NORMALMAP ) || defined( USE_CLEARCOAT_NORMALMAP )
			mat3 vTBN = mat3( tangent, bitangent, normal );
		#endif
	#endif
#endif
vec3 geometryNormal = normal;`, xl = `#ifdef OBJECTSPACE_NORMALMAP
	normal = texture2D( normalMap, vUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( TANGENTSPACE_NORMALMAP )
	vec3 mapN = texture2D( normalMap, vUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	#ifdef USE_TANGENT
		normal = normalize( vTBN * mapN );
	#else
		normal = perturbNormal2Arb( - vViewPosition, normal, mapN, faceDirection );
	#endif
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`, yl = `#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`, bl = `#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`, wl = `#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`, Ml = `#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef OBJECTSPACE_NORMALMAP
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( TANGENTSPACE_NORMALMAP ) || defined ( USE_CLEARCOAT_NORMALMAP ) )
	vec3 perturbNormal2Arb( vec3 eye_pos, vec3 surf_norm, vec3 mapN, float faceDirection ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( vUv.st );
		vec2 st1 = dFdy( vUv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : faceDirection * inversesqrt( det );
		return normalize( T * ( mapN.x * scale ) + B * ( mapN.y * scale ) + N * mapN.z );
	}
#endif`, Sl = `#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = geometryNormal;
#endif`, El = `#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	#ifdef USE_TANGENT
		clearcoatNormal = normalize( vTBN * clearcoatMapN );
	#else
		clearcoatNormal = perturbNormal2Arb( - vViewPosition, clearcoatNormal, clearcoatMapN, faceDirection );
	#endif
#endif`, Tl = `#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif`, Al = `#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`, Cl = `#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= transmissionAlpha + 0.1;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`, Ll = `vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;
const vec3 PackFactors = vec3( 256. * 256. * 256., 256. * 256., 256. );
const vec4 UnpackFactors = UnpackDownscale / vec4( PackFactors, 1. );
const float ShiftRight8 = 1. / 256.;
vec4 packDepthToRGBA( const in float v ) {
	vec4 r = vec4( fract( v * PackFactors ), v );
	r.yzw -= r.xyz * ShiftRight8;	return r * PackUpscale;
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors );
}
vec4 pack2HalfToRGBA( vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float linearClipZ, const in float near, const in float far ) {
	return linearClipZ * ( near - far ) - near;
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float invClipZ, const in float near, const in float far ) {
	return ( near * far ) / ( ( far - near ) * invClipZ - far );
}`, Rl = `#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`, Fl = `vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`, Dl = `#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`, Pl = `#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`, Il = `float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vUv );
	roughnessFactor *= texelRoughness.g;
#endif`, zl = `#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`, Bl = `#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		varying vec4 vSpotShadowCoord[ NUM_SPOT_LIGHT_SHADOWS ];
		struct SpotLightShadow {
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform sampler2D pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	float texture2DCompare( sampler2D depths, vec2 uv, float compare ) {
		return step( compare, unpackRGBAToDepth( texture2D( depths, uv ) ) );
	}
	vec2 texture2DDistribution( sampler2D shadow, vec2 uv ) {
		return unpackRGBATo2Half( texture2D( shadow, uv ) );
	}
	float VSMShadow (sampler2D shadow, vec2 uv, float compare ){
		float occlusion = 1.0;
		vec2 distribution = texture2DDistribution( shadow, uv );
		float hard_shadow = step( compare , distribution.x );
		if (hard_shadow != 1.0 ) {
			float distance = compare - distribution.x ;
			float variance = max( 0.00000, distribution.y * distribution.y );
			float softness_probability = variance / (variance + distance * distance );			softness_probability = clamp( ( softness_probability - 0.3 ) / ( 0.95 - 0.3 ), 0.0, 1.0 );			occlusion = clamp( max( hard_shadow, softness_probability ), 0.0, 1.0 );
		}
		return occlusion;
	}
	float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
		float shadow = 1.0;
		shadowCoord.xyz /= shadowCoord.w;
		shadowCoord.z += shadowBias;
		bvec4 inFrustumVec = bvec4 ( shadowCoord.x >= 0.0, shadowCoord.x <= 1.0, shadowCoord.y >= 0.0, shadowCoord.y <= 1.0 );
		bool inFrustum = all( inFrustumVec );
		bvec2 frustumTestVec = bvec2( inFrustum, shadowCoord.z <= 1.0 );
		bool frustumTest = all( frustumTestVec );
		if ( frustumTest ) {
		#if defined( SHADOWMAP_TYPE_PCF )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx0 = - texelSize.x * shadowRadius;
			float dy0 = - texelSize.y * shadowRadius;
			float dx1 = + texelSize.x * shadowRadius;
			float dy1 = + texelSize.y * shadowRadius;
			float dx2 = dx0 / 2.0;
			float dy2 = dy0 / 2.0;
			float dx3 = dx1 / 2.0;
			float dy3 = dy1 / 2.0;
			shadow = (
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy1 ), shadowCoord.z )
			) * ( 1.0 / 17.0 );
		#elif defined( SHADOWMAP_TYPE_PCF_SOFT )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx = texelSize.x;
			float dy = texelSize.y;
			vec2 uv = shadowCoord.xy;
			vec2 f = fract( uv * shadowMapSize + 0.5 );
			uv -= f * texelSize;
			shadow = (
				texture2DCompare( shadowMap, uv, shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( dx, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( 0.0, dy ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + texelSize, shadowCoord.z ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, 0.0 ), shadowCoord.z ), 
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 0.0 ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, dy ), shadowCoord.z ), 
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, dy ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( 0.0, -dy ), shadowCoord.z ), 
					 texture2DCompare( shadowMap, uv + vec2( 0.0, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( texture2DCompare( shadowMap, uv + vec2( dx, -dy ), shadowCoord.z ), 
					 texture2DCompare( shadowMap, uv + vec2( dx, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( mix( texture2DCompare( shadowMap, uv + vec2( -dx, -dy ), shadowCoord.z ), 
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, -dy ), shadowCoord.z ),
						  f.x ),
					 mix( texture2DCompare( shadowMap, uv + vec2( -dx, 2.0 * dy ), shadowCoord.z ), 
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 2.0 * dy ), shadowCoord.z ),
						  f.x ),
					 f.y )
			) * ( 1.0 / 9.0 );
		#elif defined( SHADOWMAP_TYPE_VSM )
			shadow = VSMShadow( shadowMap, shadowCoord.xy, shadowCoord.z );
		#else
			shadow = texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z );
		#endif
		}
		return shadow;
	}
	vec2 cubeToUV( vec3 v, float texelSizeY ) {
		vec3 absV = abs( v );
		float scaleToCube = 1.0 / max( absV.x, max( absV.y, absV.z ) );
		absV *= scaleToCube;
		v *= scaleToCube * ( 1.0 - 2.0 * texelSizeY );
		vec2 planar = v.xy;
		float almostATexel = 1.5 * texelSizeY;
		float almostOne = 1.0 - almostATexel;
		if ( absV.z >= almostOne ) {
			if ( v.z > 0.0 )
				planar.x = 4.0 - v.x;
		} else if ( absV.x >= almostOne ) {
			float signX = sign( v.x );
			planar.x = v.z * signX + 2.0 * signX;
		} else if ( absV.y >= almostOne ) {
			float signY = sign( v.y );
			planar.x = v.x + 2.0 * signY + 2.0;
			planar.y = v.z * signY - 2.0;
		}
		return vec2( 0.125, 0.25 ) * planar + vec2( 0.375, 0.75 );
	}
	float getPointShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		vec2 texelSize = vec2( 1.0 ) / ( shadowMapSize * vec2( 4.0, 2.0 ) );
		vec3 lightToPosition = shadowCoord.xyz;
		float dp = ( length( lightToPosition ) - shadowCameraNear ) / ( shadowCameraFar - shadowCameraNear );		dp += shadowBias;
		vec3 bd3D = normalize( lightToPosition );
		#if defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_PCF_SOFT ) || defined( SHADOWMAP_TYPE_VSM )
			vec2 offset = vec2( - 1, 1 ) * shadowRadius * texelSize.y;
			return (
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyy, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyy, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyx, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyx, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxy, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxy, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxx, texelSize.y ), dp ) +
				texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxx, texelSize.y ), dp )
			) * ( 1.0 / 9.0 );
		#else
			return texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp );
		#endif
	}
#endif`, Nl = `#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		uniform mat4 spotShadowMatrix[ NUM_SPOT_LIGHT_SHADOWS ];
		varying vec4 vSpotShadowCoord[ NUM_SPOT_LIGHT_SHADOWS ];
		struct SpotLightShadow {
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`, Ol = `#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SPOT_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0
		vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		vec4 shadowWorldPosition;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
		vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias, 0 );
		vSpotShadowCoord[ i ] = spotShadowMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
		vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
	#endif
#endif`, Ul = `float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowBias, spotLight.shadowRadius, vSpotShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`, Gl = `#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`, kl = `#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	uniform int boneTextureSize;
	mat4 getBoneMatrix( const in float i ) {
		float j = i * 4.0;
		float x = mod( j, float( boneTextureSize ) );
		float y = floor( j / float( boneTextureSize ) );
		float dx = 1.0 / float( boneTextureSize );
		float dy = 1.0 / float( boneTextureSize );
		y = dy * ( y + 0.5 );
		vec4 v1 = texture2D( boneTexture, vec2( dx * ( x + 0.5 ), y ) );
		vec4 v2 = texture2D( boneTexture, vec2( dx * ( x + 1.5 ), y ) );
		vec4 v3 = texture2D( boneTexture, vec2( dx * ( x + 2.5 ), y ) );
		vec4 v4 = texture2D( boneTexture, vec2( dx * ( x + 3.5 ), y ) );
		mat4 bone = mat4( v1, v2, v3, v4 );
		return bone;
	}
#endif`, Wl = `#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`, Vl = `#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`, Hl = `float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`, ql = `#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`, Xl = `#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`, jl = `#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return toneMappingExposure * color;
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 OptimizedCineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`, Yl = `#ifdef USE_TRANSMISSION
	float transmissionAlpha = 1.0;
	float transmissionFactor = transmission;
	float thicknessFactor = thickness;
	#ifdef USE_TRANSMISSIONMAP
		transmissionFactor *= texture2D( transmissionMap, vUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		thicknessFactor *= texture2D( thicknessMap, vUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmission = getIBLVolumeRefraction(
		n, v, roughnessFactor, material.diffuseColor, material.specularColor, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, ior, thicknessFactor,
		attenuationColor, attenuationDistance );
	totalDiffuse = mix( totalDiffuse, transmission.rgb, transmissionFactor );
	transmissionAlpha = mix( transmissionAlpha, transmission.a, transmissionFactor );
#endif`, Zl = `#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float framebufferLod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		#ifdef texture2DLodEXT
			return texture2DLodEXT( transmissionSamplerMap, fragCoord.xy, framebufferLod );
		#else
			return texture2D( transmissionSamplerMap, fragCoord.xy, framebufferLod );
		#endif
	}
	vec3 applyVolumeAttenuation( const in vec3 radiance, const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( attenuationDistance == 0.0 ) {
			return radiance;
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance * radiance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
		vec3 refractedRayExit = position + transmissionRay;
		vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
		vec2 refractionCoords = ndcPos.xy / ndcPos.w;
		refractionCoords += 1.0;
		refractionCoords /= 2.0;
		vec4 transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
		vec3 attenuatedColor = applyVolumeAttenuation( transmittedLight.rgb, length( transmissionRay ), attenuationColor, attenuationDistance );
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		return vec4( ( 1.0 - F ) * attenuatedColor * diffuseColor, transmittedLight.a );
	}
#endif`, $l = `#if ( defined( USE_UV ) && ! defined( UVS_VERTEX_ONLY ) )
	varying vec2 vUv;
#endif`, Kl = `#ifdef USE_UV
	#ifdef UVS_VERTEX_ONLY
		vec2 vUv;
	#else
		varying vec2 vUv;
	#endif
	uniform mat3 uvTransform;
#endif`, Jl = `#ifdef USE_UV
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
#endif`, Ql = `#if defined( USE_LIGHTMAP ) || defined( USE_AOMAP )
	varying vec2 vUv2;
#endif`, ec = `#if defined( USE_LIGHTMAP ) || defined( USE_AOMAP )
	attribute vec2 uv2;
	varying vec2 vUv2;
	uniform mat3 uv2Transform;
#endif`, tc = `#if defined( USE_LIGHTMAP ) || defined( USE_AOMAP )
	vUv2 = ( uv2Transform * vec3( uv2, 1 ) ).xy;
#endif`, nc = `#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION )
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;
const ic = `varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`, sc = `uniform sampler2D t2D;
varying vec2 vUv;
void main() {
	gl_FragColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		gl_FragColor = vec4( mix( pow( gl_FragColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), gl_FragColor.rgb * 0.0773993808, vec3( lessThanEqual( gl_FragColor.rgb, vec3( 0.04045 ) ) ) ), gl_FragColor.w );
	#endif
	#include <tonemapping_fragment>
	#include <encodings_fragment>
}`, rc = `varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`, oc = `#include <envmap_common_pars_fragment>
uniform float opacity;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	vec3 vReflect = vWorldDirection;
	#include <envmap_fragment>
	gl_FragColor = envColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <encodings_fragment>
}`, ac = `#include <common>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <skinbase_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`, lc = `#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( 1.0 );
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <logdepthbuf_fragment>
	float fragCoordZ = 0.5 * vHighPrecisionZW[0] / vHighPrecisionZW[1] + 0.5;
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#endif
}`, cc = `#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <skinbase_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`, hc = `#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( 1.0 );
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = packDepthToRGBA( dist );
}`, uc = `varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`, dc = `uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <encodings_fragment>
}`, fc = `uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`, pc = `uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <logdepthbuf_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`, mc = `#include <common>
#include <uv_pars_vertex>
#include <uv2_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <uv2_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`, gc = `uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <uv2_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vUv2 );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`, _c = `#define LAMBERT
varying vec3 vLightFront;
varying vec3 vIndirectFront;
#ifdef DOUBLE_SIDED
	varying vec3 vLightBack;
	varying vec3 vIndirectBack;
#endif
#include <common>
#include <uv_pars_vertex>
#include <uv2_pars_vertex>
#include <envmap_pars_vertex>
#include <bsdfs>
#include <lights_pars_begin>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <uv2_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <lights_lambert_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`, vc = `uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
varying vec3 vLightFront;
varying vec3 vIndirectFront;
#ifdef DOUBLE_SIDED
	varying vec3 vLightBack;
	varying vec3 vIndirectBack;
#endif
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <uv2_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <fog_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( diffuse, opacity );
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <specularmap_fragment>
	#include <emissivemap_fragment>
	#ifdef DOUBLE_SIDED
		reflectedLight.indirectDiffuse += ( gl_FrontFacing ) ? vIndirectFront : vIndirectBack;
	#else
		reflectedLight.indirectDiffuse += vIndirectFront;
	#endif
	#include <lightmap_fragment>
	reflectedLight.indirectDiffuse *= BRDF_Lambert( diffuseColor.rgb );
	#ifdef DOUBLE_SIDED
		reflectedLight.directDiffuse = ( gl_FrontFacing ) ? vLightFront : vLightBack;
	#else
		reflectedLight.directDiffuse = vLightFront;
	#endif
	reflectedLight.directDiffuse *= BRDF_Lambert( diffuseColor.rgb ) * getShadowMask();
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`, xc = `#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`, yc = `#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`, bc = `#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( TANGENTSPACE_NORMALMAP )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( TANGENTSPACE_NORMALMAP )
	vViewPosition = - mvPosition.xyz;
#endif
}`, wc = `#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( TANGENTSPACE_NORMALMAP )
	varying vec3 vViewPosition;
#endif
#include <packing>
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( packNormalToRGB( normal ), opacity );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`, Mc = `#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <uv_pars_vertex>
#include <uv2_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <uv2_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`, Sc = `#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <uv2_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( diffuse, opacity );
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`, Ec = `#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <uv_pars_vertex>
#include <uv2_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <uv2_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`, Tc = `#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULARINTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
	#ifdef USE_SPECULARCOLORMAP
		uniform sampler2D specularColorMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEENCOLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEENROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <uv2_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <bsdfs>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( diffuse, opacity );
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
		float sheenEnergyComp = 1.0 - 0.157 * max3( material.sheenColor );
		outgoingLight = outgoingLight * sheenEnergyComp + sheenSpecular;
	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometry.clearcoatNormal, geometry.viewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + clearcoatSpecular * material.clearcoat;
	#endif
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`, Ac = `#define TOON
varying vec3 vViewPosition;
#include <common>
#include <uv_pars_vertex>
#include <uv2_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <uv2_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`, Cc = `#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <uv2_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec4 diffuseColor = vec4( diffuse, opacity );
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`, Lc = `uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`, Rc = `uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`, Fc = `#include <common>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`, Dc = `uniform vec3 color;
uniform float opacity;
#include <common>
#include <packing>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
}`, Pc = `uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix * vec4( 0.0, 0.0, 0.0, 1.0 );
	vec2 scale;
	scale.x = length( vec3( modelMatrix[ 0 ].x, modelMatrix[ 0 ].y, modelMatrix[ 0 ].z ) );
	scale.y = length( vec3( modelMatrix[ 1 ].x, modelMatrix[ 1 ].y, modelMatrix[ 1 ].z ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`, Ic = `uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <output_fragment>
	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
}`, Te = {
  alphamap_fragment: oa,
  alphamap_pars_fragment: aa,
  alphatest_fragment: la,
  alphatest_pars_fragment: ca,
  aomap_fragment: ha,
  aomap_pars_fragment: ua,
  begin_vertex: da,
  beginnormal_vertex: fa,
  bsdfs: pa,
  iridescence_fragment: ma,
  bumpmap_pars_fragment: ga,
  clipping_planes_fragment: _a,
  clipping_planes_pars_fragment: va,
  clipping_planes_pars_vertex: xa,
  clipping_planes_vertex: ya,
  color_fragment: ba,
  color_pars_fragment: wa,
  color_pars_vertex: Ma,
  color_vertex: Sa,
  common: Ea,
  cube_uv_reflection_fragment: Ta,
  defaultnormal_vertex: Aa,
  displacementmap_pars_vertex: Ca,
  displacementmap_vertex: La,
  emissivemap_fragment: Ra,
  emissivemap_pars_fragment: Fa,
  encodings_fragment: Da,
  encodings_pars_fragment: Pa,
  envmap_fragment: Ia,
  envmap_common_pars_fragment: za,
  envmap_pars_fragment: Ba,
  envmap_pars_vertex: Na,
  envmap_physical_pars_fragment: Ya,
  envmap_vertex: Oa,
  fog_vertex: Ua,
  fog_pars_vertex: Ga,
  fog_fragment: ka,
  fog_pars_fragment: Wa,
  gradientmap_pars_fragment: Va,
  lightmap_fragment: Ha,
  lightmap_pars_fragment: qa,
  lights_lambert_vertex: Xa,
  lights_pars_begin: ja,
  lights_toon_fragment: Za,
  lights_toon_pars_fragment: $a,
  lights_phong_fragment: Ka,
  lights_phong_pars_fragment: Ja,
  lights_physical_fragment: Qa,
  lights_physical_pars_fragment: el,
  lights_fragment_begin: tl,
  lights_fragment_maps: nl,
  lights_fragment_end: il,
  logdepthbuf_fragment: sl,
  logdepthbuf_pars_fragment: rl,
  logdepthbuf_pars_vertex: ol,
  logdepthbuf_vertex: al,
  map_fragment: ll,
  map_pars_fragment: cl,
  map_particle_fragment: hl,
  map_particle_pars_fragment: ul,
  metalnessmap_fragment: dl,
  metalnessmap_pars_fragment: fl,
  morphcolor_vertex: pl,
  morphnormal_vertex: ml,
  morphtarget_pars_vertex: gl,
  morphtarget_vertex: _l,
  normal_fragment_begin: vl,
  normal_fragment_maps: xl,
  normal_pars_fragment: yl,
  normal_pars_vertex: bl,
  normal_vertex: wl,
  normalmap_pars_fragment: Ml,
  clearcoat_normal_fragment_begin: Sl,
  clearcoat_normal_fragment_maps: El,
  clearcoat_pars_fragment: Tl,
  iridescence_pars_fragment: Al,
  output_fragment: Cl,
  packing: Ll,
  premultiplied_alpha_fragment: Rl,
  project_vertex: Fl,
  dithering_fragment: Dl,
  dithering_pars_fragment: Pl,
  roughnessmap_fragment: Il,
  roughnessmap_pars_fragment: zl,
  shadowmap_pars_fragment: Bl,
  shadowmap_pars_vertex: Nl,
  shadowmap_vertex: Ol,
  shadowmask_pars_fragment: Ul,
  skinbase_vertex: Gl,
  skinning_pars_vertex: kl,
  skinning_vertex: Wl,
  skinnormal_vertex: Vl,
  specularmap_fragment: Hl,
  specularmap_pars_fragment: ql,
  tonemapping_fragment: Xl,
  tonemapping_pars_fragment: jl,
  transmission_fragment: Yl,
  transmission_pars_fragment: Zl,
  uv_pars_fragment: $l,
  uv_pars_vertex: Kl,
  uv_vertex: Jl,
  uv2_pars_fragment: Ql,
  uv2_pars_vertex: ec,
  uv2_vertex: tc,
  worldpos_vertex: nc,
  background_vert: ic,
  background_frag: sc,
  cube_vert: rc,
  cube_frag: oc,
  depth_vert: ac,
  depth_frag: lc,
  distanceRGBA_vert: cc,
  distanceRGBA_frag: hc,
  equirect_vert: uc,
  equirect_frag: dc,
  linedashed_vert: fc,
  linedashed_frag: pc,
  meshbasic_vert: mc,
  meshbasic_frag: gc,
  meshlambert_vert: _c,
  meshlambert_frag: vc,
  meshmatcap_vert: xc,
  meshmatcap_frag: yc,
  meshnormal_vert: bc,
  meshnormal_frag: wc,
  meshphong_vert: Mc,
  meshphong_frag: Sc,
  meshphysical_vert: Ec,
  meshphysical_frag: Tc,
  meshtoon_vert: Ac,
  meshtoon_frag: Cc,
  points_vert: Lc,
  points_frag: Rc,
  shadow_vert: Fc,
  shadow_frag: Dc,
  sprite_vert: Pc,
  sprite_frag: Ic
}, ne = {
  common: {
    diffuse: { value: /* @__PURE__ */ new Ae(16777215) },
    opacity: { value: 1 },
    map: { value: null },
    uvTransform: { value: /* @__PURE__ */ new Mt() },
    uv2Transform: { value: /* @__PURE__ */ new Mt() },
    alphaMap: { value: null },
    alphaTest: { value: 0 }
  },
  specularmap: {
    specularMap: { value: null }
  },
  envmap: {
    envMap: { value: null },
    flipEnvMap: { value: -1 },
    reflectivity: { value: 1 },
    ior: { value: 1.5 },
    refractionRatio: { value: 0.98 }
  },
  aomap: {
    aoMap: { value: null },
    aoMapIntensity: { value: 1 }
  },
  lightmap: {
    lightMap: { value: null },
    lightMapIntensity: { value: 1 }
  },
  emissivemap: {
    emissiveMap: { value: null }
  },
  bumpmap: {
    bumpMap: { value: null },
    bumpScale: { value: 1 }
  },
  normalmap: {
    normalMap: { value: null },
    normalScale: { value: /* @__PURE__ */ new Ce(1, 1) }
  },
  displacementmap: {
    displacementMap: { value: null },
    displacementScale: { value: 1 },
    displacementBias: { value: 0 }
  },
  roughnessmap: {
    roughnessMap: { value: null }
  },
  metalnessmap: {
    metalnessMap: { value: null }
  },
  gradientmap: {
    gradientMap: { value: null }
  },
  fog: {
    fogDensity: { value: 25e-5 },
    fogNear: { value: 1 },
    fogFar: { value: 2e3 },
    fogColor: { value: /* @__PURE__ */ new Ae(16777215) }
  },
  lights: {
    ambientLightColor: { value: [] },
    lightProbe: { value: [] },
    directionalLights: { value: [], properties: {
      direction: {},
      color: {}
    } },
    directionalLightShadows: { value: [], properties: {
      shadowBias: {},
      shadowNormalBias: {},
      shadowRadius: {},
      shadowMapSize: {}
    } },
    directionalShadowMap: { value: [] },
    directionalShadowMatrix: { value: [] },
    spotLights: { value: [], properties: {
      color: {},
      position: {},
      direction: {},
      distance: {},
      coneCos: {},
      penumbraCos: {},
      decay: {}
    } },
    spotLightShadows: { value: [], properties: {
      shadowBias: {},
      shadowNormalBias: {},
      shadowRadius: {},
      shadowMapSize: {}
    } },
    spotShadowMap: { value: [] },
    spotShadowMatrix: { value: [] },
    pointLights: { value: [], properties: {
      color: {},
      position: {},
      decay: {},
      distance: {}
    } },
    pointLightShadows: { value: [], properties: {
      shadowBias: {},
      shadowNormalBias: {},
      shadowRadius: {},
      shadowMapSize: {},
      shadowCameraNear: {},
      shadowCameraFar: {}
    } },
    pointShadowMap: { value: [] },
    pointShadowMatrix: { value: [] },
    hemisphereLights: { value: [], properties: {
      direction: {},
      skyColor: {},
      groundColor: {}
    } },
    rectAreaLights: { value: [], properties: {
      color: {},
      position: {},
      width: {},
      height: {}
    } },
    ltc_1: { value: null },
    ltc_2: { value: null }
  },
  points: {
    diffuse: { value: /* @__PURE__ */ new Ae(16777215) },
    opacity: { value: 1 },
    size: { value: 1 },
    scale: { value: 1 },
    map: { value: null },
    alphaMap: { value: null },
    alphaTest: { value: 0 },
    uvTransform: { value: /* @__PURE__ */ new Mt() }
  },
  sprite: {
    diffuse: { value: /* @__PURE__ */ new Ae(16777215) },
    opacity: { value: 1 },
    center: { value: /* @__PURE__ */ new Ce(0.5, 0.5) },
    rotation: { value: 0 },
    map: { value: null },
    alphaMap: { value: null },
    alphaTest: { value: 0 },
    uvTransform: { value: /* @__PURE__ */ new Mt() }
  }
}, Bt = {
  basic: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.specularmap,
      ne.envmap,
      ne.aomap,
      ne.lightmap,
      ne.fog
    ]),
    vertexShader: Te.meshbasic_vert,
    fragmentShader: Te.meshbasic_frag
  },
  lambert: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.specularmap,
      ne.envmap,
      ne.aomap,
      ne.lightmap,
      ne.emissivemap,
      ne.fog,
      ne.lights,
      {
        emissive: { value: /* @__PURE__ */ new Ae(0) }
      }
    ]),
    vertexShader: Te.meshlambert_vert,
    fragmentShader: Te.meshlambert_frag
  },
  phong: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.specularmap,
      ne.envmap,
      ne.aomap,
      ne.lightmap,
      ne.emissivemap,
      ne.bumpmap,
      ne.normalmap,
      ne.displacementmap,
      ne.fog,
      ne.lights,
      {
        emissive: { value: /* @__PURE__ */ new Ae(0) },
        specular: { value: /* @__PURE__ */ new Ae(1118481) },
        shininess: { value: 30 }
      }
    ]),
    vertexShader: Te.meshphong_vert,
    fragmentShader: Te.meshphong_frag
  },
  standard: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.envmap,
      ne.aomap,
      ne.lightmap,
      ne.emissivemap,
      ne.bumpmap,
      ne.normalmap,
      ne.displacementmap,
      ne.roughnessmap,
      ne.metalnessmap,
      ne.fog,
      ne.lights,
      {
        emissive: { value: /* @__PURE__ */ new Ae(0) },
        roughness: { value: 1 },
        metalness: { value: 0 },
        envMapIntensity: { value: 1 }
      }
    ]),
    vertexShader: Te.meshphysical_vert,
    fragmentShader: Te.meshphysical_frag
  },
  toon: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.aomap,
      ne.lightmap,
      ne.emissivemap,
      ne.bumpmap,
      ne.normalmap,
      ne.displacementmap,
      ne.gradientmap,
      ne.fog,
      ne.lights,
      {
        emissive: { value: /* @__PURE__ */ new Ae(0) }
      }
    ]),
    vertexShader: Te.meshtoon_vert,
    fragmentShader: Te.meshtoon_frag
  },
  matcap: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.bumpmap,
      ne.normalmap,
      ne.displacementmap,
      ne.fog,
      {
        matcap: { value: null }
      }
    ]),
    vertexShader: Te.meshmatcap_vert,
    fragmentShader: Te.meshmatcap_frag
  },
  points: {
    uniforms: /* @__PURE__ */ it([
      ne.points,
      ne.fog
    ]),
    vertexShader: Te.points_vert,
    fragmentShader: Te.points_frag
  },
  dashed: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.fog,
      {
        scale: { value: 1 },
        dashSize: { value: 1 },
        totalSize: { value: 2 }
      }
    ]),
    vertexShader: Te.linedashed_vert,
    fragmentShader: Te.linedashed_frag
  },
  depth: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.displacementmap
    ]),
    vertexShader: Te.depth_vert,
    fragmentShader: Te.depth_frag
  },
  normal: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.bumpmap,
      ne.normalmap,
      ne.displacementmap,
      {
        opacity: { value: 1 }
      }
    ]),
    vertexShader: Te.meshnormal_vert,
    fragmentShader: Te.meshnormal_frag
  },
  sprite: {
    uniforms: /* @__PURE__ */ it([
      ne.sprite,
      ne.fog
    ]),
    vertexShader: Te.sprite_vert,
    fragmentShader: Te.sprite_frag
  },
  background: {
    uniforms: {
      uvTransform: { value: /* @__PURE__ */ new Mt() },
      t2D: { value: null }
    },
    vertexShader: Te.background_vert,
    fragmentShader: Te.background_frag
  },
  cube: {
    uniforms: /* @__PURE__ */ it([
      ne.envmap,
      {
        opacity: { value: 1 }
      }
    ]),
    vertexShader: Te.cube_vert,
    fragmentShader: Te.cube_frag
  },
  equirect: {
    uniforms: {
      tEquirect: { value: null }
    },
    vertexShader: Te.equirect_vert,
    fragmentShader: Te.equirect_frag
  },
  distanceRGBA: {
    uniforms: /* @__PURE__ */ it([
      ne.common,
      ne.displacementmap,
      {
        referencePosition: { value: /* @__PURE__ */ new O() },
        nearDistance: { value: 1 },
        farDistance: { value: 1e3 }
      }
    ]),
    vertexShader: Te.distanceRGBA_vert,
    fragmentShader: Te.distanceRGBA_frag
  },
  shadow: {
    uniforms: /* @__PURE__ */ it([
      ne.lights,
      ne.fog,
      {
        color: { value: /* @__PURE__ */ new Ae(0) },
        opacity: { value: 1 }
      }
    ]),
    vertexShader: Te.shadow_vert,
    fragmentShader: Te.shadow_frag
  }
};
Bt.physical = {
  uniforms: /* @__PURE__ */ it([
    Bt.standard.uniforms,
    {
      clearcoat: { value: 0 },
      clearcoatMap: { value: null },
      clearcoatRoughness: { value: 0 },
      clearcoatRoughnessMap: { value: null },
      clearcoatNormalScale: { value: /* @__PURE__ */ new Ce(1, 1) },
      clearcoatNormalMap: { value: null },
      iridescence: { value: 0 },
      iridescenceMap: { value: null },
      iridescenceIOR: { value: 1.3 },
      iridescenceThicknessMinimum: { value: 100 },
      iridescenceThicknessMaximum: { value: 400 },
      iridescenceThicknessMap: { value: null },
      sheen: { value: 0 },
      sheenColor: { value: /* @__PURE__ */ new Ae(0) },
      sheenColorMap: { value: null },
      sheenRoughness: { value: 1 },
      sheenRoughnessMap: { value: null },
      transmission: { value: 0 },
      transmissionMap: { value: null },
      transmissionSamplerSize: { value: /* @__PURE__ */ new Ce() },
      transmissionSamplerMap: { value: null },
      thickness: { value: 0 },
      thicknessMap: { value: null },
      attenuationDistance: { value: 0 },
      attenuationColor: { value: /* @__PURE__ */ new Ae(0) },
      specularIntensity: { value: 1 },
      specularIntensityMap: { value: null },
      specularColor: { value: /* @__PURE__ */ new Ae(1, 1, 1) },
      specularColorMap: { value: null }
    }
  ]),
  vertexShader: Te.meshphysical_vert,
  fragmentShader: Te.meshphysical_frag
};
function zc(h, e, t, n, i, s) {
  const o = new Ae(0);
  let r = i === !0 ? 0 : 1, l, a, c = null, d = 0, u = null;
  function m(p, f) {
    let v = !1, _ = f.isScene === !0 ? f.background : null;
    _ && _.isTexture && (_ = e.get(_));
    const w = h.xr, x = w.getSession && w.getSession();
    x && x.environmentBlendMode === "additive" && (_ = null), _ === null ? g(o, r) : _ && _.isColor && (g(_, 1), v = !0), (h.autoClear || v) && h.clear(h.autoClearColor, h.autoClearDepth, h.autoClearStencil), _ && (_.isCubeTexture || _.mapping === 306) ? (a === void 0 && (a = new Nt(
      new pi(1, 1, 1),
      new Tn({
        name: "BackgroundCubeMaterial",
        uniforms: Zn(Bt.cube.uniforms),
        vertexShader: Bt.cube.vertexShader,
        fragmentShader: Bt.cube.fragmentShader,
        side: 1,
        depthTest: !1,
        depthWrite: !1,
        fog: !1
      })
    ), a.geometry.deleteAttribute("normal"), a.geometry.deleteAttribute("uv"), a.onBeforeRender = function(M, E, R) {
      this.matrixWorld.copyPosition(R.matrixWorld);
    }, Object.defineProperty(a.material, "envMap", {
      get: function() {
        return this.uniforms.envMap.value;
      }
    }), n.update(a)), a.material.uniforms.envMap.value = _, a.material.uniforms.flipEnvMap.value = _.isCubeTexture && _.isRenderTargetTexture === !1 ? -1 : 1, (c !== _ || d !== _.version || u !== h.toneMapping) && (a.material.needsUpdate = !0, c = _, d = _.version, u = h.toneMapping), a.layers.enableAll(), p.unshift(a, a.geometry, a.material, 0, 0, null)) : _ && _.isTexture && (l === void 0 && (l = new Nt(
      new ji(2, 2),
      new Tn({
        name: "BackgroundMaterial",
        uniforms: Zn(Bt.background.uniforms),
        vertexShader: Bt.background.vertexShader,
        fragmentShader: Bt.background.fragmentShader,
        side: 0,
        depthTest: !1,
        depthWrite: !1,
        fog: !1
      })
    ), l.geometry.deleteAttribute("normal"), Object.defineProperty(l.material, "map", {
      get: function() {
        return this.uniforms.t2D.value;
      }
    }), n.update(l)), l.material.uniforms.t2D.value = _, _.matrixAutoUpdate === !0 && _.updateMatrix(), l.material.uniforms.uvTransform.value.copy(_.matrix), (c !== _ || d !== _.version || u !== h.toneMapping) && (l.material.needsUpdate = !0, c = _, d = _.version, u = h.toneMapping), l.layers.enableAll(), p.unshift(l, l.geometry, l.material, 0, 0, null));
  }
  function g(p, f) {
    t.buffers.color.setClear(p.r, p.g, p.b, f, s);
  }
  return {
    getClearColor: function() {
      return o;
    },
    setClearColor: function(p, f = 1) {
      o.set(p), r = f, g(o, r);
    },
    getClearAlpha: function() {
      return r;
    },
    setClearAlpha: function(p) {
      r = p, g(o, r);
    },
    render: m
  };
}
function Bc(h, e, t, n) {
  const i = h.getParameter(34921), s = n.isWebGL2 ? null : e.get("OES_vertex_array_object"), o = n.isWebGL2 || s !== null, r = {}, l = f(null);
  let a = l, c = !1;
  function d(L, I, D, q, k) {
    let N = !1;
    if (o) {
      const H = p(q, D, I);
      a !== H && (a = H, m(a.object)), N = v(L, q, D, k), N && _(L, q, D, k);
    } else {
      const H = I.wireframe === !0;
      (a.geometry !== q.id || a.program !== D.id || a.wireframe !== H) && (a.geometry = q.id, a.program = D.id, a.wireframe = H, N = !0);
    }
    k !== null && t.update(k, 34963), (N || c) && (c = !1, y(L, I, D, q), k !== null && h.bindBuffer(34963, t.get(k).buffer));
  }
  function u() {
    return n.isWebGL2 ? h.createVertexArray() : s.createVertexArrayOES();
  }
  function m(L) {
    return n.isWebGL2 ? h.bindVertexArray(L) : s.bindVertexArrayOES(L);
  }
  function g(L) {
    return n.isWebGL2 ? h.deleteVertexArray(L) : s.deleteVertexArrayOES(L);
  }
  function p(L, I, D) {
    const q = D.wireframe === !0;
    let k = r[L.id];
    k === void 0 && (k = {}, r[L.id] = k);
    let N = k[I.id];
    N === void 0 && (N = {}, k[I.id] = N);
    let H = N[q];
    return H === void 0 && (H = f(u()), N[q] = H), H;
  }
  function f(L) {
    const I = [], D = [], q = [];
    for (let k = 0; k < i; k++)
      I[k] = 0, D[k] = 0, q[k] = 0;
    return {
      geometry: null,
      program: null,
      wireframe: !1,
      newAttributes: I,
      enabledAttributes: D,
      attributeDivisors: q,
      object: L,
      attributes: {},
      index: null
    };
  }
  function v(L, I, D, q) {
    const k = a.attributes, N = I.attributes;
    let H = 0;
    const J = D.getAttributes();
    for (const V in J)
      if (J[V].location >= 0) {
        const ce = k[V];
        let ge = N[V];
        if (ge === void 0 && (V === "instanceMatrix" && L.instanceMatrix && (ge = L.instanceMatrix), V === "instanceColor" && L.instanceColor && (ge = L.instanceColor)), ce === void 0 || ce.attribute !== ge || ge && ce.data !== ge.data)
          return !0;
        H++;
      }
    return a.attributesNum !== H || a.index !== q;
  }
  function _(L, I, D, q) {
    const k = {}, N = I.attributes;
    let H = 0;
    const J = D.getAttributes();
    for (const V in J)
      if (J[V].location >= 0) {
        let ce = N[V];
        ce === void 0 && (V === "instanceMatrix" && L.instanceMatrix && (ce = L.instanceMatrix), V === "instanceColor" && L.instanceColor && (ce = L.instanceColor));
        const ge = {};
        ge.attribute = ce, ce && ce.data && (ge.data = ce.data), k[V] = ge, H++;
      }
    a.attributes = k, a.attributesNum = H, a.index = q;
  }
  function w() {
    const L = a.newAttributes;
    for (let I = 0, D = L.length; I < D; I++)
      L[I] = 0;
  }
  function x(L) {
    M(L, 0);
  }
  function M(L, I) {
    const D = a.newAttributes, q = a.enabledAttributes, k = a.attributeDivisors;
    D[L] = 1, q[L] === 0 && (h.enableVertexAttribArray(L), q[L] = 1), k[L] !== I && ((n.isWebGL2 ? h : e.get("ANGLE_instanced_arrays"))[n.isWebGL2 ? "vertexAttribDivisor" : "vertexAttribDivisorANGLE"](L, I), k[L] = I);
  }
  function E() {
    const L = a.newAttributes, I = a.enabledAttributes;
    for (let D = 0, q = I.length; D < q; D++)
      I[D] !== L[D] && (h.disableVertexAttribArray(D), I[D] = 0);
  }
  function R(L, I, D, q, k, N) {
    n.isWebGL2 === !0 && (D === 5124 || D === 5125) ? h.vertexAttribIPointer(L, I, D, k, N) : h.vertexAttribPointer(L, I, D, q, k, N);
  }
  function y(L, I, D, q) {
    if (n.isWebGL2 === !1 && (L.isInstancedMesh || q.isInstancedBufferGeometry) && e.get("ANGLE_instanced_arrays") === null)
      return;
    w();
    const k = q.attributes, N = D.getAttributes(), H = I.defaultAttributeValues;
    for (const J in N) {
      const V = N[J];
      if (V.location >= 0) {
        let ee = k[J];
        if (ee === void 0 && (J === "instanceMatrix" && L.instanceMatrix && (ee = L.instanceMatrix), J === "instanceColor" && L.instanceColor && (ee = L.instanceColor)), ee !== void 0) {
          const ce = ee.normalized, ge = ee.itemSize, $ = t.get(ee);
          if ($ === void 0)
            continue;
          const De = $.buffer, ve = $.type, xe = $.bytesPerElement;
          if (ee.isInterleavedBufferAttribute) {
            const ue = ee.data, Oe = ue.stride, Ee = ee.offset;
            if (ue.isInstancedInterleavedBuffer) {
              for (let me = 0; me < V.locationSize; me++)
                M(V.location + me, ue.meshPerAttribute);
              L.isInstancedMesh !== !0 && q._maxInstanceCount === void 0 && (q._maxInstanceCount = ue.meshPerAttribute * ue.count);
            } else
              for (let me = 0; me < V.locationSize; me++)
                x(V.location + me);
            h.bindBuffer(34962, De);
            for (let me = 0; me < V.locationSize; me++)
              R(
                V.location + me,
                ge / V.locationSize,
                ve,
                ce,
                Oe * xe,
                (Ee + ge / V.locationSize * me) * xe
              );
          } else {
            if (ee.isInstancedBufferAttribute) {
              for (let ue = 0; ue < V.locationSize; ue++)
                M(V.location + ue, ee.meshPerAttribute);
              L.isInstancedMesh !== !0 && q._maxInstanceCount === void 0 && (q._maxInstanceCount = ee.meshPerAttribute * ee.count);
            } else
              for (let ue = 0; ue < V.locationSize; ue++)
                x(V.location + ue);
            h.bindBuffer(34962, De);
            for (let ue = 0; ue < V.locationSize; ue++)
              R(
                V.location + ue,
                ge / V.locationSize,
                ve,
                ce,
                ge * xe,
                ge / V.locationSize * ue * xe
              );
          }
        } else if (H !== void 0) {
          const ce = H[J];
          if (ce !== void 0)
            switch (ce.length) {
              case 2:
                h.vertexAttrib2fv(V.location, ce);
                break;
              case 3:
                h.vertexAttrib3fv(V.location, ce);
                break;
              case 4:
                h.vertexAttrib4fv(V.location, ce);
                break;
              default:
                h.vertexAttrib1fv(V.location, ce);
            }
        }
      }
    }
    E();
  }
  function A() {
    G();
    for (const L in r) {
      const I = r[L];
      for (const D in I) {
        const q = I[D];
        for (const k in q)
          g(q[k].object), delete q[k];
        delete I[D];
      }
      delete r[L];
    }
  }
  function F(L) {
    if (r[L.id] === void 0)
      return;
    const I = r[L.id];
    for (const D in I) {
      const q = I[D];
      for (const k in q)
        g(q[k].object), delete q[k];
      delete I[D];
    }
    delete r[L.id];
  }
  function P(L) {
    for (const I in r) {
      const D = r[I];
      if (D[L.id] === void 0)
        continue;
      const q = D[L.id];
      for (const k in q)
        g(q[k].object), delete q[k];
      delete D[L.id];
    }
  }
  function G() {
    z(), c = !0, a !== l && (a = l, m(a.object));
  }
  function z() {
    l.geometry = null, l.program = null, l.wireframe = !1;
  }
  return {
    setup: d,
    reset: G,
    resetDefaultState: z,
    dispose: A,
    releaseStatesOfGeometry: F,
    releaseStatesOfProgram: P,
    initAttributes: w,
    enableAttribute: x,
    disableUnusedAttributes: E
  };
}
function Nc(h, e, t, n) {
  const i = n.isWebGL2;
  let s;
  function o(a) {
    s = a;
  }
  function r(a, c) {
    h.drawArrays(s, a, c), t.update(c, s, 1);
  }
  function l(a, c, d) {
    if (d === 0)
      return;
    let u, m;
    if (i)
      u = h, m = "drawArraysInstanced";
    else if (u = e.get("ANGLE_instanced_arrays"), m = "drawArraysInstancedANGLE", u === null) {
      console.error("THREE.WebGLBufferRenderer: using THREE.InstancedBufferGeometry but hardware does not support extension ANGLE_instanced_arrays.");
      return;
    }
    u[m](s, a, c, d), t.update(c, s, d);
  }
  this.setMode = o, this.render = r, this.renderInstances = l;
}
function Oc(h, e, t) {
  let n;
  function i() {
    if (n !== void 0)
      return n;
    if (e.has("EXT_texture_filter_anisotropic") === !0) {
      const R = e.get("EXT_texture_filter_anisotropic");
      n = h.getParameter(R.MAX_TEXTURE_MAX_ANISOTROPY_EXT);
    } else
      n = 0;
    return n;
  }
  function s(R) {
    if (R === "highp") {
      if (h.getShaderPrecisionFormat(35633, 36338).precision > 0 && h.getShaderPrecisionFormat(35632, 36338).precision > 0)
        return "highp";
      R = "mediump";
    }
    return R === "mediump" && h.getShaderPrecisionFormat(35633, 36337).precision > 0 && h.getShaderPrecisionFormat(35632, 36337).precision > 0 ? "mediump" : "lowp";
  }
  const o = typeof WebGL2RenderingContext < "u" && h instanceof WebGL2RenderingContext || typeof WebGL2ComputeRenderingContext < "u" && h instanceof WebGL2ComputeRenderingContext;
  let r = t.precision !== void 0 ? t.precision : "highp";
  const l = s(r);
  l !== r && (console.warn("THREE.WebGLRenderer:", r, "not supported, using", l, "instead."), r = l);
  const a = o || e.has("WEBGL_draw_buffers"), c = t.logarithmicDepthBuffer === !0, d = h.getParameter(34930), u = h.getParameter(35660), m = h.getParameter(3379), g = h.getParameter(34076), p = h.getParameter(34921), f = h.getParameter(36347), v = h.getParameter(36348), _ = h.getParameter(36349), w = u > 0, x = o || e.has("OES_texture_float"), M = w && x, E = o ? h.getParameter(36183) : 0;
  return {
    isWebGL2: o,
    drawBuffers: a,
    getMaxAnisotropy: i,
    getMaxPrecision: s,
    precision: r,
    logarithmicDepthBuffer: c,
    maxTextures: d,
    maxVertexTextures: u,
    maxTextureSize: m,
    maxCubemapSize: g,
    maxAttributes: p,
    maxVertexUniforms: f,
    maxVaryings: v,
    maxFragmentUniforms: _,
    vertexTextures: w,
    floatFragmentTextures: x,
    floatVertexTextures: M,
    maxSamples: E
  };
}
function Uc(h) {
  const e = this;
  let t = null, n = 0, i = !1, s = !1;
  const o = new gn(), r = new Mt(), l = { value: null, needsUpdate: !1 };
  this.uniform = l, this.numPlanes = 0, this.numIntersection = 0, this.init = function(d, u, m) {
    const g = d.length !== 0 || u || n !== 0 || i;
    return i = u, t = c(d, m, 0), n = d.length, g;
  }, this.beginShadows = function() {
    s = !0, c(null);
  }, this.endShadows = function() {
    s = !1, a();
  }, this.setState = function(d, u, m) {
    const g = d.clippingPlanes, p = d.clipIntersection, f = d.clipShadows, v = h.get(d);
    if (!i || g === null || g.length === 0 || s && !f)
      s ? c(null) : a();
    else {
      const _ = s ? 0 : n, w = _ * 4;
      let x = v.clippingState || null;
      l.value = x, x = c(g, u, w, m);
      for (let M = 0; M !== w; ++M)
        x[M] = t[M];
      v.clippingState = x, this.numIntersection = p ? this.numPlanes : 0, this.numPlanes += _;
    }
  };
  function a() {
    l.value !== t && (l.value = t, l.needsUpdate = n > 0), e.numPlanes = n, e.numIntersection = 0;
  }
  function c(d, u, m, g) {
    const p = d !== null ? d.length : 0;
    let f = null;
    if (p !== 0) {
      if (f = l.value, g !== !0 || f === null) {
        const v = m + p * 4, _ = u.matrixWorldInverse;
        r.getNormalMatrix(_), (f === null || f.length < v) && (f = new Float32Array(v));
        for (let w = 0, x = m; w !== p; ++w, x += 4)
          o.copy(d[w]).applyMatrix4(_, r), o.normal.toArray(f, x), f[x + 3] = o.constant;
      }
      l.value = f, l.needsUpdate = !0;
    }
    return e.numPlanes = p, e.numIntersection = 0, f;
  }
}
function Gc(h) {
  let e = /* @__PURE__ */ new WeakMap();
  function t(o, r) {
    return r === 303 ? o.mapping = 301 : r === 304 && (o.mapping = 302), o;
  }
  function n(o) {
    if (o && o.isTexture && o.isRenderTargetTexture === !1) {
      const r = o.mapping;
      if (r === 303 || r === 304)
        if (e.has(o)) {
          const l = e.get(o).texture;
          return t(l, o.mapping);
        } else {
          const l = o.image;
          if (l && l.height > 0) {
            const a = new na(l.height / 2);
            return a.fromEquirectangularTexture(h, o), e.set(o, a), o.addEventListener("dispose", i), t(a.texture, o.mapping);
          } else
            return null;
        }
    }
    return o;
  }
  function i(o) {
    const r = o.target;
    r.removeEventListener("dispose", i);
    const l = e.get(r);
    l !== void 0 && (e.delete(r), l.dispose());
  }
  function s() {
    e = /* @__PURE__ */ new WeakMap();
  }
  return {
    get: n,
    dispose: s
  };
}
class kc extends ho {
  constructor(e = -1, t = 1, n = 1, i = -1, s = 0.1, o = 2e3) {
    super(), this.isOrthographicCamera = !0, this.type = "OrthographicCamera", this.zoom = 1, this.view = null, this.left = e, this.right = t, this.top = n, this.bottom = i, this.near = s, this.far = o, this.updateProjectionMatrix();
  }
  copy(e, t) {
    return super.copy(e, t), this.left = e.left, this.right = e.right, this.top = e.top, this.bottom = e.bottom, this.near = e.near, this.far = e.far, this.zoom = e.zoom, this.view = e.view === null ? null : Object.assign({}, e.view), this;
  }
  setViewOffset(e, t, n, i, s, o) {
    this.view === null && (this.view = {
      enabled: !0,
      fullWidth: 1,
      fullHeight: 1,
      offsetX: 0,
      offsetY: 0,
      width: 1,
      height: 1
    }), this.view.enabled = !0, this.view.fullWidth = e, this.view.fullHeight = t, this.view.offsetX = n, this.view.offsetY = i, this.view.width = s, this.view.height = o, this.updateProjectionMatrix();
  }
  clearViewOffset() {
    this.view !== null && (this.view.enabled = !1), this.updateProjectionMatrix();
  }
  updateProjectionMatrix() {
    const e = (this.right - this.left) / (2 * this.zoom), t = (this.top - this.bottom) / (2 * this.zoom), n = (this.right + this.left) / 2, i = (this.top + this.bottom) / 2;
    let s = n - e, o = n + e, r = i + t, l = i - t;
    if (this.view !== null && this.view.enabled) {
      const a = (this.right - this.left) / this.view.fullWidth / this.zoom, c = (this.top - this.bottom) / this.view.fullHeight / this.zoom;
      s += a * this.view.offsetX, o = s + a * this.view.width, r -= c * this.view.offsetY, l = r - c * this.view.height;
    }
    this.projectionMatrix.makeOrthographic(s, o, r, l, this.near, this.far), this.projectionMatrixInverse.copy(this.projectionMatrix).invert();
  }
  toJSON(e) {
    const t = super.toJSON(e);
    return t.object.zoom = this.zoom, t.object.left = this.left, t.object.right = this.right, t.object.top = this.top, t.object.bottom = this.bottom, t.object.near = this.near, t.object.far = this.far, this.view !== null && (t.object.view = Object.assign({}, this.view)), t;
  }
}
const jn = 4, lr = [0.125, 0.215, 0.35, 0.446, 0.526, 0.582], vn = 20, ws = /* @__PURE__ */ new kc(), cr = /* @__PURE__ */ new Ae();
let Ms = null;
const _n = (1 + Math.sqrt(5)) / 2, Hn = 1 / _n, hr = [
  /* @__PURE__ */ new O(1, 1, 1),
  /* @__PURE__ */ new O(-1, 1, 1),
  /* @__PURE__ */ new O(1, 1, -1),
  /* @__PURE__ */ new O(-1, 1, -1),
  /* @__PURE__ */ new O(0, _n, Hn),
  /* @__PURE__ */ new O(0, _n, -Hn),
  /* @__PURE__ */ new O(Hn, 0, _n),
  /* @__PURE__ */ new O(-Hn, 0, _n),
  /* @__PURE__ */ new O(_n, Hn, 0),
  /* @__PURE__ */ new O(-_n, Hn, 0)
];
class ur {
  constructor(e) {
    this._renderer = e, this._pingPongRenderTarget = null, this._lodMax = 0, this._cubeSize = 0, this._lodPlanes = [], this._sizeLods = [], this._sigmas = [], this._blurMaterial = null, this._cubemapMaterial = null, this._equirectMaterial = null, this._compileMaterial(this._blurMaterial);
  }
  fromScene(e, t = 0, n = 0.1, i = 100) {
    Ms = this._renderer.getRenderTarget(), this._setSize(256);
    const s = this._allocateTargets();
    return s.depthBuffer = !0, this._sceneToCubeUV(e, n, i, s), t > 0 && this._blur(s, 0, 0, t), this._applyPMREM(s), this._cleanup(s), s;
  }
  fromEquirectangular(e, t = null) {
    return this._fromTexture(e, t);
  }
  fromCubemap(e, t = null) {
    return this._fromTexture(e, t);
  }
  compileCubemapShader() {
    this._cubemapMaterial === null && (this._cubemapMaterial = pr(), this._compileMaterial(this._cubemapMaterial));
  }
  compileEquirectangularShader() {
    this._equirectMaterial === null && (this._equirectMaterial = fr(), this._compileMaterial(this._equirectMaterial));
  }
  dispose() {
    this._dispose(), this._cubemapMaterial !== null && this._cubemapMaterial.dispose(), this._equirectMaterial !== null && this._equirectMaterial.dispose();
  }
  _setSize(e) {
    this._lodMax = Math.floor(Math.log2(e)), this._cubeSize = Math.pow(2, this._lodMax);
  }
  _dispose() {
    this._blurMaterial !== null && this._blurMaterial.dispose(), this._pingPongRenderTarget !== null && this._pingPongRenderTarget.dispose();
    for (let e = 0; e < this._lodPlanes.length; e++)
      this._lodPlanes[e].dispose();
  }
  _cleanup(e) {
    this._renderer.setRenderTarget(Ms), e.scissorTest = !1, zi(e, 0, 0, e.width, e.height);
  }
  _fromTexture(e, t) {
    e.mapping === 301 || e.mapping === 302 ? this._setSize(e.image.length === 0 ? 16 : e.image[0].width || e.image[0].image.width) : this._setSize(e.image.width / 4), Ms = this._renderer.getRenderTarget();
    const n = t || this._allocateTargets();
    return this._textureToCubeUV(e, n), this._applyPMREM(n), this._cleanup(n), n;
  }
  _allocateTargets() {
    const e = 3 * Math.max(this._cubeSize, 112), t = 4 * this._cubeSize, n = {
      magFilter: 1006,
      minFilter: 1006,
      generateMipmaps: !1,
      type: 1016,
      format: 1023,
      encoding: 3e3,
      depthBuffer: !1
    }, i = dr(e, t, n);
    if (this._pingPongRenderTarget === null || this._pingPongRenderTarget.width !== e) {
      this._pingPongRenderTarget !== null && this._dispose(), this._pingPongRenderTarget = dr(e, t, n);
      const { _lodMax: s } = this;
      ({ sizeLods: this._sizeLods, lodPlanes: this._lodPlanes, sigmas: this._sigmas } = Wc(s)), this._blurMaterial = Vc(s, e, t);
    }
    return i;
  }
  _compileMaterial(e) {
    const t = new Nt(this._lodPlanes[0], e);
    this._renderer.compile(t, ws);
  }
  _sceneToCubeUV(e, t, n, i) {
    const r = new gt(90, 1, t, n), l = [1, -1, 1, 1, 1, 1], a = [1, 1, 1, -1, -1, -1], c = this._renderer, d = c.autoClear, u = c.toneMapping;
    c.getClearColor(cr), c.toneMapping = 0, c.autoClear = !1;
    const m = new ao({
      name: "PMREM.Background",
      side: 1,
      depthWrite: !1,
      depthTest: !1
    }), g = new Nt(new pi(), m);
    let p = !1;
    const f = e.background;
    f ? f.isColor && (m.color.copy(f), e.background = null, p = !0) : (m.color.copy(cr), p = !0);
    for (let v = 0; v < 6; v++) {
      const _ = v % 3;
      _ === 0 ? (r.up.set(0, l[v], 0), r.lookAt(a[v], 0, 0)) : _ === 1 ? (r.up.set(0, 0, l[v]), r.lookAt(0, a[v], 0)) : (r.up.set(0, l[v], 0), r.lookAt(0, 0, a[v]));
      const w = this._cubeSize;
      zi(i, _ * w, v > 2 ? w : 0, w, w), c.setRenderTarget(i), p && c.render(g, r), c.render(e, r);
    }
    g.geometry.dispose(), g.material.dispose(), c.toneMapping = u, c.autoClear = d, e.background = f;
  }
  _textureToCubeUV(e, t) {
    const n = this._renderer, i = e.mapping === 301 || e.mapping === 302;
    i ? (this._cubemapMaterial === null && (this._cubemapMaterial = pr()), this._cubemapMaterial.uniforms.flipEnvMap.value = e.isRenderTargetTexture === !1 ? -1 : 1) : this._equirectMaterial === null && (this._equirectMaterial = fr());
    const s = i ? this._cubemapMaterial : this._equirectMaterial, o = new Nt(this._lodPlanes[0], s), r = s.uniforms;
    r.envMap.value = e;
    const l = this._cubeSize;
    zi(t, 0, 0, 3 * l, 2 * l), n.setRenderTarget(t), n.render(o, ws);
  }
  _applyPMREM(e) {
    const t = this._renderer, n = t.autoClear;
    t.autoClear = !1;
    for (let i = 1; i < this._lodPlanes.length; i++) {
      const s = Math.sqrt(this._sigmas[i] * this._sigmas[i] - this._sigmas[i - 1] * this._sigmas[i - 1]), o = hr[(i - 1) % hr.length];
      this._blur(e, i - 1, i, s, o);
    }
    t.autoClear = n;
  }
  _blur(e, t, n, i, s) {
    const o = this._pingPongRenderTarget;
    this._halfBlur(
      e,
      o,
      t,
      n,
      i,
      "latitudinal",
      s
    ), this._halfBlur(
      o,
      e,
      n,
      n,
      i,
      "longitudinal",
      s
    );
  }
  _halfBlur(e, t, n, i, s, o, r) {
    const l = this._renderer, a = this._blurMaterial;
    o !== "latitudinal" && o !== "longitudinal" && console.error(
      "blur direction must be either latitudinal or longitudinal!"
    );
    const c = 3, d = new Nt(this._lodPlanes[i], a), u = a.uniforms, m = this._sizeLods[n] - 1, g = isFinite(s) ? Math.PI / (2 * m) : 2 * Math.PI / (2 * vn - 1), p = s / g, f = isFinite(s) ? 1 + Math.floor(c * p) : vn;
    f > vn && console.warn(`sigmaRadians, ${s}, is too large and will clip, as it requested ${f} samples when the maximum is set to ${vn}`);
    const v = [];
    let _ = 0;
    for (let R = 0; R < vn; ++R) {
      const y = R / p, A = Math.exp(-y * y / 2);
      v.push(A), R === 0 ? _ += A : R < f && (_ += 2 * A);
    }
    for (let R = 0; R < v.length; R++)
      v[R] = v[R] / _;
    u.envMap.value = e.texture, u.samples.value = f, u.weights.value = v, u.latitudinal.value = o === "latitudinal", r && (u.poleAxis.value = r);
    const { _lodMax: w } = this;
    u.dTheta.value = g, u.mipInt.value = w - n;
    const x = this._sizeLods[i], M = 3 * x * (i > w - jn ? i - w + jn : 0), E = 4 * (this._cubeSize - x);
    zi(t, M, E, 3 * x, 2 * x), l.setRenderTarget(t), l.render(d, ws);
  }
}
function Wc(h) {
  const e = [], t = [], n = [];
  let i = h;
  const s = h - jn + 1 + lr.length;
  for (let o = 0; o < s; o++) {
    const r = Math.pow(2, i);
    t.push(r);
    let l = 1 / r;
    o > h - jn ? l = lr[o - h + jn - 1] : o === 0 && (l = 0), n.push(l);
    const a = 1 / (r - 2), c = -a, d = 1 + a, u = [c, c, d, c, d, d, c, c, d, d, c, d], m = 6, g = 6, p = 3, f = 2, v = 1, _ = new Float32Array(p * g * m), w = new Float32Array(f * g * m), x = new Float32Array(v * g * m);
    for (let E = 0; E < m; E++) {
      const R = E % 3 * 2 / 3 - 1, y = E > 2 ? 0 : -1, A = [
        R,
        y,
        0,
        R + 2 / 3,
        y,
        0,
        R + 2 / 3,
        y + 1,
        0,
        R,
        y,
        0,
        R + 2 / 3,
        y + 1,
        0,
        R,
        y + 1,
        0
      ];
      _.set(A, p * g * E), w.set(u, f * g * E);
      const F = [E, E, E, E, E, E];
      x.set(F, v * g * E);
    }
    const M = new Ut();
    M.setAttribute("position", new Ot(_, p)), M.setAttribute("uv", new Ot(w, f)), M.setAttribute("faceIndex", new Ot(x, v)), e.push(M), i > jn && i--;
  }
  return { lodPlanes: e, sizeLods: t, sigmas: n };
}
function dr(h, e, t) {
  const n = new En(h, e, t);
  return n.texture.mapping = 306, n.texture.name = "PMREM.cubeUv", n.scissorTest = !0, n;
}
function zi(h, e, t, n, i) {
  h.viewport.set(e, t, n, i), h.scissor.set(e, t, n, i);
}
function Vc(h, e, t) {
  const n = new Float32Array(vn), i = new O(0, 1, 0);
  return new Tn({
    name: "SphericalGaussianBlur",
    defines: {
      n: vn,
      CUBEUV_TEXEL_WIDTH: 1 / e,
      CUBEUV_TEXEL_HEIGHT: 1 / t,
      CUBEUV_MAX_MIP: `${h}.0`
    },
    uniforms: {
      envMap: { value: null },
      samples: { value: 1 },
      weights: { value: n },
      latitudinal: { value: !1 },
      dTheta: { value: 0 },
      mipInt: { value: 0 },
      poleAxis: { value: i }
    },
    vertexShader: Gs(),
    fragmentShader: `

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,
    blending: 0,
    depthTest: !1,
    depthWrite: !1
  });
}
function fr() {
  return new Tn({
    name: "EquirectangularToCubeUV",
    uniforms: {
      envMap: { value: null }
    },
    vertexShader: Gs(),
    fragmentShader: `

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,
    blending: 0,
    depthTest: !1,
    depthWrite: !1
  });
}
function pr() {
  return new Tn({
    name: "CubemapToCubeUV",
    uniforms: {
      envMap: { value: null },
      flipEnvMap: { value: -1 }
    },
    vertexShader: Gs(),
    fragmentShader: `

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,
    blending: 0,
    depthTest: !1,
    depthWrite: !1
  });
}
function Gs() {
  return `

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`;
}
function Hc(h) {
  let e = /* @__PURE__ */ new WeakMap(), t = null;
  function n(r) {
    if (r && r.isTexture) {
      const l = r.mapping, a = l === 303 || l === 304, c = l === 301 || l === 302;
      if (a || c)
        if (r.isRenderTargetTexture && r.needsPMREMUpdate === !0) {
          r.needsPMREMUpdate = !1;
          let d = e.get(r);
          return t === null && (t = new ur(h)), d = a ? t.fromEquirectangular(r, d) : t.fromCubemap(r, d), e.set(r, d), d.texture;
        } else {
          if (e.has(r))
            return e.get(r).texture;
          {
            const d = r.image;
            if (a && d && d.height > 0 || c && d && i(d)) {
              t === null && (t = new ur(h));
              const u = a ? t.fromEquirectangular(r) : t.fromCubemap(r);
              return e.set(r, u), r.addEventListener("dispose", s), u.texture;
            } else
              return null;
          }
        }
    }
    return r;
  }
  function i(r) {
    let l = 0;
    const a = 6;
    for (let c = 0; c < a; c++)
      r[c] !== void 0 && l++;
    return l === a;
  }
  function s(r) {
    const l = r.target;
    l.removeEventListener("dispose", s);
    const a = e.get(l);
    a !== void 0 && (e.delete(l), a.dispose());
  }
  function o() {
    e = /* @__PURE__ */ new WeakMap(), t !== null && (t.dispose(), t = null);
  }
  return {
    get: n,
    dispose: o
  };
}
function qc(h) {
  const e = {};
  function t(n) {
    if (e[n] !== void 0)
      return e[n];
    let i;
    switch (n) {
      case "WEBGL_depth_texture":
        i = h.getExtension("WEBGL_depth_texture") || h.getExtension("MOZ_WEBGL_depth_texture") || h.getExtension("WEBKIT_WEBGL_depth_texture");
        break;
      case "EXT_texture_filter_anisotropic":
        i = h.getExtension("EXT_texture_filter_anisotropic") || h.getExtension("MOZ_EXT_texture_filter_anisotropic") || h.getExtension("WEBKIT_EXT_texture_filter_anisotropic");
        break;
      case "WEBGL_compressed_texture_s3tc":
        i = h.getExtension("WEBGL_compressed_texture_s3tc") || h.getExtension("MOZ_WEBGL_compressed_texture_s3tc") || h.getExtension("WEBKIT_WEBGL_compressed_texture_s3tc");
        break;
      case "WEBGL_compressed_texture_pvrtc":
        i = h.getExtension("WEBGL_compressed_texture_pvrtc") || h.getExtension("WEBKIT_WEBGL_compressed_texture_pvrtc");
        break;
      default:
        i = h.getExtension(n);
    }
    return e[n] = i, i;
  }
  return {
    has: function(n) {
      return t(n) !== null;
    },
    init: function(n) {
      n.isWebGL2 ? t("EXT_color_buffer_float") : (t("WEBGL_depth_texture"), t("OES_texture_float"), t("OES_texture_half_float"), t("OES_texture_half_float_linear"), t("OES_standard_derivatives"), t("OES_element_index_uint"), t("OES_vertex_array_object"), t("ANGLE_instanced_arrays")), t("OES_texture_float_linear"), t("EXT_color_buffer_half_float"), t("WEBGL_multisampled_render_to_texture");
    },
    get: function(n) {
      const i = t(n);
      return i === null && console.warn("THREE.WebGLRenderer: " + n + " extension not supported."), i;
    }
  };
}
function Xc(h, e, t, n) {
  const i = {}, s = /* @__PURE__ */ new WeakMap();
  function o(d) {
    const u = d.target;
    u.index !== null && e.remove(u.index);
    for (const g in u.attributes)
      e.remove(u.attributes[g]);
    u.removeEventListener("dispose", o), delete i[u.id];
    const m = s.get(u);
    m && (e.remove(m), s.delete(u)), n.releaseStatesOfGeometry(u), u.isInstancedBufferGeometry === !0 && delete u._maxInstanceCount, t.memory.geometries--;
  }
  function r(d, u) {
    return i[u.id] === !0 || (u.addEventListener("dispose", o), i[u.id] = !0, t.memory.geometries++), u;
  }
  function l(d) {
    const u = d.attributes;
    for (const g in u)
      e.update(u[g], 34962);
    const m = d.morphAttributes;
    for (const g in m) {
      const p = m[g];
      for (let f = 0, v = p.length; f < v; f++)
        e.update(p[f], 34962);
    }
  }
  function a(d) {
    const u = [], m = d.index, g = d.attributes.position;
    let p = 0;
    if (m !== null) {
      const _ = m.array;
      p = m.version;
      for (let w = 0, x = _.length; w < x; w += 3) {
        const M = _[w + 0], E = _[w + 1], R = _[w + 2];
        u.push(M, E, E, R, R, M);
      }
    } else {
      const _ = g.array;
      p = g.version;
      for (let w = 0, x = _.length / 3 - 1; w < x; w += 3) {
        const M = w + 0, E = w + 1, R = w + 2;
        u.push(M, E, E, R, R, M);
      }
    }
    const f = new (to(u) ? co : lo)(u, 1);
    f.version = p;
    const v = s.get(d);
    v && e.remove(v), s.set(d, f);
  }
  function c(d) {
    const u = s.get(d);
    if (u) {
      const m = d.index;
      m !== null && u.version < m.version && a(d);
    } else
      a(d);
    return s.get(d);
  }
  return {
    get: r,
    update: l,
    getWireframeAttribute: c
  };
}
function jc(h, e, t, n) {
  const i = n.isWebGL2;
  let s;
  function o(u) {
    s = u;
  }
  let r, l;
  function a(u) {
    r = u.type, l = u.bytesPerElement;
  }
  function c(u, m) {
    h.drawElements(s, m, r, u * l), t.update(m, s, 1);
  }
  function d(u, m, g) {
    if (g === 0)
      return;
    let p, f;
    if (i)
      p = h, f = "drawElementsInstanced";
    else if (p = e.get("ANGLE_instanced_arrays"), f = "drawElementsInstancedANGLE", p === null) {
      console.error("THREE.WebGLIndexedBufferRenderer: using THREE.InstancedBufferGeometry but hardware does not support extension ANGLE_instanced_arrays.");
      return;
    }
    p[f](s, m, r, u * l, g), t.update(m, s, g);
  }
  this.setMode = o, this.setIndex = a, this.render = c, this.renderInstances = d;
}
function Yc(h) {
  const e = {
    geometries: 0,
    textures: 0
  }, t = {
    frame: 0,
    calls: 0,
    triangles: 0,
    points: 0,
    lines: 0
  };
  function n(s, o, r) {
    switch (t.calls++, o) {
      case 4:
        t.triangles += r * (s / 3);
        break;
      case 1:
        t.lines += r * (s / 2);
        break;
      case 3:
        t.lines += r * (s - 1);
        break;
      case 2:
        t.lines += r * s;
        break;
      case 0:
        t.points += r * s;
        break;
      default:
        console.error("THREE.WebGLInfo: Unknown draw mode:", o);
        break;
    }
  }
  function i() {
    t.frame++, t.calls = 0, t.triangles = 0, t.points = 0, t.lines = 0;
  }
  return {
    memory: e,
    render: t,
    programs: null,
    autoReset: !0,
    reset: i,
    update: n
  };
}
function Zc(h, e) {
  return h[0] - e[0];
}
function $c(h, e) {
  return Math.abs(e[1]) - Math.abs(h[1]);
}
function Ss(h, e) {
  let t = 1;
  const n = e.isInterleavedBufferAttribute ? e.data.array : e.array;
  n instanceof Int8Array ? t = 127 : n instanceof Uint8Array ? t = 255 : n instanceof Uint16Array ? t = 65535 : n instanceof Int16Array ? t = 32767 : n instanceof Int32Array ? t = 2147483647 : console.error("THREE.WebGLMorphtargets: Unsupported morph attribute data type: ", n), h.divideScalar(t);
}
function Kc(h, e, t) {
  const n = {}, i = new Float32Array(8), s = /* @__PURE__ */ new WeakMap(), o = new $e(), r = [];
  for (let a = 0; a < 8; a++)
    r[a] = [a, 0];
  function l(a, c, d, u) {
    const m = a.morphTargetInfluences;
    if (e.isWebGL2 === !0) {
      const g = c.morphAttributes.position || c.morphAttributes.normal || c.morphAttributes.color, p = g !== void 0 ? g.length : 0;
      let f = s.get(c);
      if (f === void 0 || f.count !== p) {
        let I = function() {
          z.dispose(), s.delete(c), c.removeEventListener("dispose", I);
        };
        f !== void 0 && f.texture.dispose();
        const w = c.morphAttributes.position !== void 0, x = c.morphAttributes.normal !== void 0, M = c.morphAttributes.color !== void 0, E = c.morphAttributes.position || [], R = c.morphAttributes.normal || [], y = c.morphAttributes.color || [];
        let A = 0;
        w === !0 && (A = 1), x === !0 && (A = 2), M === !0 && (A = 3);
        let F = c.attributes.position.count * A, P = 1;
        F > e.maxTextureSize && (P = Math.ceil(F / e.maxTextureSize), F = e.maxTextureSize);
        const G = new Float32Array(F * P * 4 * p), z = new ro(G, F, P, p);
        z.type = 1015, z.needsUpdate = !0;
        const L = A * 4;
        for (let D = 0; D < p; D++) {
          const q = E[D], k = R[D], N = y[D], H = F * P * 4 * D;
          for (let J = 0; J < q.count; J++) {
            const V = J * L;
            w === !0 && (o.fromBufferAttribute(q, J), q.normalized === !0 && Ss(o, q), G[H + V + 0] = o.x, G[H + V + 1] = o.y, G[H + V + 2] = o.z, G[H + V + 3] = 0), x === !0 && (o.fromBufferAttribute(k, J), k.normalized === !0 && Ss(o, k), G[H + V + 4] = o.x, G[H + V + 5] = o.y, G[H + V + 6] = o.z, G[H + V + 7] = 0), M === !0 && (o.fromBufferAttribute(N, J), N.normalized === !0 && Ss(o, N), G[H + V + 8] = o.x, G[H + V + 9] = o.y, G[H + V + 10] = o.z, G[H + V + 11] = N.itemSize === 4 ? o.w : 1);
          }
        }
        f = {
          count: p,
          texture: z,
          size: new Ce(F, P)
        }, s.set(c, f), c.addEventListener("dispose", I);
      }
      let v = 0;
      for (let w = 0; w < m.length; w++)
        v += m[w];
      const _ = c.morphTargetsRelative ? 1 : 1 - v;
      u.getUniforms().setValue(h, "morphTargetBaseInfluence", _), u.getUniforms().setValue(h, "morphTargetInfluences", m), u.getUniforms().setValue(h, "morphTargetsTexture", f.texture, t), u.getUniforms().setValue(h, "morphTargetsTextureSize", f.size);
    } else {
      const g = m === void 0 ? 0 : m.length;
      let p = n[c.id];
      if (p === void 0 || p.length !== g) {
        p = [];
        for (let x = 0; x < g; x++)
          p[x] = [x, 0];
        n[c.id] = p;
      }
      for (let x = 0; x < g; x++) {
        const M = p[x];
        M[0] = x, M[1] = m[x];
      }
      p.sort($c);
      for (let x = 0; x < 8; x++)
        x < g && p[x][1] ? (r[x][0] = p[x][0], r[x][1] = p[x][1]) : (r[x][0] = Number.MAX_SAFE_INTEGER, r[x][1] = 0);
      r.sort(Zc);
      const f = c.morphAttributes.position, v = c.morphAttributes.normal;
      let _ = 0;
      for (let x = 0; x < 8; x++) {
        const M = r[x], E = M[0], R = M[1];
        E !== Number.MAX_SAFE_INTEGER && R ? (f && c.getAttribute("morphTarget" + x) !== f[E] && c.setAttribute("morphTarget" + x, f[E]), v && c.getAttribute("morphNormal" + x) !== v[E] && c.setAttribute("morphNormal" + x, v[E]), i[x] = R, _ += R) : (f && c.hasAttribute("morphTarget" + x) === !0 && c.deleteAttribute("morphTarget" + x), v && c.hasAttribute("morphNormal" + x) === !0 && c.deleteAttribute("morphNormal" + x), i[x] = 0);
      }
      const w = c.morphTargetsRelative ? 1 : 1 - _;
      u.getUniforms().setValue(h, "morphTargetBaseInfluence", w), u.getUniforms().setValue(h, "morphTargetInfluences", i);
    }
  }
  return {
    update: l
  };
}
function Jc(h, e, t, n) {
  let i = /* @__PURE__ */ new WeakMap();
  function s(l) {
    const a = n.render.frame, c = l.geometry, d = e.get(l, c);
    return i.get(d) !== a && (e.update(d), i.set(d, a)), l.isInstancedMesh && (l.hasEventListener("dispose", r) === !1 && l.addEventListener("dispose", r), t.update(l.instanceMatrix, 34962), l.instanceColor !== null && t.update(l.instanceColor, 34962)), d;
  }
  function o() {
    i = /* @__PURE__ */ new WeakMap();
  }
  function r(l) {
    const a = l.target;
    a.removeEventListener("dispose", r), t.remove(a.instanceMatrix), a.instanceColor !== null && t.remove(a.instanceColor);
  }
  return {
    update: s,
    dispose: o
  };
}
const po = /* @__PURE__ */ new _t(), mo = /* @__PURE__ */ new ro(), go = /* @__PURE__ */ new Uo(), _o = /* @__PURE__ */ new uo(), mr = [], gr = [], _r = new Float32Array(16), vr = new Float32Array(9), xr = new Float32Array(4);
function Kn(h, e, t) {
  const n = h[0];
  if (n <= 0 || n > 0)
    return h;
  const i = e * t;
  let s = mr[i];
  if (s === void 0 && (s = new Float32Array(i), mr[i] = s), e !== 0) {
    n.toArray(s, 0);
    for (let o = 1, r = 0; o !== e; ++o)
      r += t, h[o].toArray(s, r);
  }
  return s;
}
function lt(h, e) {
  if (h.length !== e.length)
    return !1;
  for (let t = 0, n = h.length; t < n; t++)
    if (h[t] !== e[t])
      return !1;
  return !0;
}
function ct(h, e) {
  for (let t = 0, n = e.length; t < n; t++)
    h[t] = e[t];
}
function Yi(h, e) {
  let t = gr[e];
  t === void 0 && (t = new Int32Array(e), gr[e] = t);
  for (let n = 0; n !== e; ++n)
    t[n] = h.allocateTextureUnit();
  return t;
}
function Qc(h, e) {
  const t = this.cache;
  t[0] !== e && (h.uniform1f(this.addr, e), t[0] = e);
}
function eh(h, e) {
  const t = this.cache;
  if (e.x !== void 0)
    (t[0] !== e.x || t[1] !== e.y) && (h.uniform2f(this.addr, e.x, e.y), t[0] = e.x, t[1] = e.y);
  else {
    if (lt(t, e))
      return;
    h.uniform2fv(this.addr, e), ct(t, e);
  }
}
function th(h, e) {
  const t = this.cache;
  if (e.x !== void 0)
    (t[0] !== e.x || t[1] !== e.y || t[2] !== e.z) && (h.uniform3f(this.addr, e.x, e.y, e.z), t[0] = e.x, t[1] = e.y, t[2] = e.z);
  else if (e.r !== void 0)
    (t[0] !== e.r || t[1] !== e.g || t[2] !== e.b) && (h.uniform3f(this.addr, e.r, e.g, e.b), t[0] = e.r, t[1] = e.g, t[2] = e.b);
  else {
    if (lt(t, e))
      return;
    h.uniform3fv(this.addr, e), ct(t, e);
  }
}
function nh(h, e) {
  const t = this.cache;
  if (e.x !== void 0)
    (t[0] !== e.x || t[1] !== e.y || t[2] !== e.z || t[3] !== e.w) && (h.uniform4f(this.addr, e.x, e.y, e.z, e.w), t[0] = e.x, t[1] = e.y, t[2] = e.z, t[3] = e.w);
  else {
    if (lt(t, e))
      return;
    h.uniform4fv(this.addr, e), ct(t, e);
  }
}
function ih(h, e) {
  const t = this.cache, n = e.elements;
  if (n === void 0) {
    if (lt(t, e))
      return;
    h.uniformMatrix2fv(this.addr, !1, e), ct(t, e);
  } else {
    if (lt(t, n))
      return;
    xr.set(n), h.uniformMatrix2fv(this.addr, !1, xr), ct(t, n);
  }
}
function sh(h, e) {
  const t = this.cache, n = e.elements;
  if (n === void 0) {
    if (lt(t, e))
      return;
    h.uniformMatrix3fv(this.addr, !1, e), ct(t, e);
  } else {
    if (lt(t, n))
      return;
    vr.set(n), h.uniformMatrix3fv(this.addr, !1, vr), ct(t, n);
  }
}
function rh(h, e) {
  const t = this.cache, n = e.elements;
  if (n === void 0) {
    if (lt(t, e))
      return;
    h.uniformMatrix4fv(this.addr, !1, e), ct(t, e);
  } else {
    if (lt(t, n))
      return;
    _r.set(n), h.uniformMatrix4fv(this.addr, !1, _r), ct(t, n);
  }
}
function oh(h, e) {
  const t = this.cache;
  t[0] !== e && (h.uniform1i(this.addr, e), t[0] = e);
}
function ah(h, e) {
  const t = this.cache;
  lt(t, e) || (h.uniform2iv(this.addr, e), ct(t, e));
}
function lh(h, e) {
  const t = this.cache;
  lt(t, e) || (h.uniform3iv(this.addr, e), ct(t, e));
}
function ch(h, e) {
  const t = this.cache;
  lt(t, e) || (h.uniform4iv(this.addr, e), ct(t, e));
}
function hh(h, e) {
  const t = this.cache;
  t[0] !== e && (h.uniform1ui(this.addr, e), t[0] = e);
}
function uh(h, e) {
  const t = this.cache;
  lt(t, e) || (h.uniform2uiv(this.addr, e), ct(t, e));
}
function dh(h, e) {
  const t = this.cache;
  lt(t, e) || (h.uniform3uiv(this.addr, e), ct(t, e));
}
function fh(h, e) {
  const t = this.cache;
  lt(t, e) || (h.uniform4uiv(this.addr, e), ct(t, e));
}
function ph(h, e, t) {
  const n = this.cache, i = t.allocateTextureUnit();
  n[0] !== i && (h.uniform1i(this.addr, i), n[0] = i), t.setTexture2D(e || po, i);
}
function mh(h, e, t) {
  const n = this.cache, i = t.allocateTextureUnit();
  n[0] !== i && (h.uniform1i(this.addr, i), n[0] = i), t.setTexture3D(e || go, i);
}
function gh(h, e, t) {
  const n = this.cache, i = t.allocateTextureUnit();
  n[0] !== i && (h.uniform1i(this.addr, i), n[0] = i), t.setTextureCube(e || _o, i);
}
function _h(h, e, t) {
  const n = this.cache, i = t.allocateTextureUnit();
  n[0] !== i && (h.uniform1i(this.addr, i), n[0] = i), t.setTexture2DArray(e || mo, i);
}
function vh(h) {
  switch (h) {
    case 5126:
      return Qc;
    case 35664:
      return eh;
    case 35665:
      return th;
    case 35666:
      return nh;
    case 35674:
      return ih;
    case 35675:
      return sh;
    case 35676:
      return rh;
    case 5124:
    case 35670:
      return oh;
    case 35667:
    case 35671:
      return ah;
    case 35668:
    case 35672:
      return lh;
    case 35669:
    case 35673:
      return ch;
    case 5125:
      return hh;
    case 36294:
      return uh;
    case 36295:
      return dh;
    case 36296:
      return fh;
    case 35678:
    case 36198:
    case 36298:
    case 36306:
    case 35682:
      return ph;
    case 35679:
    case 36299:
    case 36307:
      return mh;
    case 35680:
    case 36300:
    case 36308:
    case 36293:
      return gh;
    case 36289:
    case 36303:
    case 36311:
    case 36292:
      return _h;
  }
}
function xh(h, e) {
  h.uniform1fv(this.addr, e);
}
function yh(h, e) {
  const t = Kn(e, this.size, 2);
  h.uniform2fv(this.addr, t);
}
function bh(h, e) {
  const t = Kn(e, this.size, 3);
  h.uniform3fv(this.addr, t);
}
function wh(h, e) {
  const t = Kn(e, this.size, 4);
  h.uniform4fv(this.addr, t);
}
function Mh(h, e) {
  const t = Kn(e, this.size, 4);
  h.uniformMatrix2fv(this.addr, !1, t);
}
function Sh(h, e) {
  const t = Kn(e, this.size, 9);
  h.uniformMatrix3fv(this.addr, !1, t);
}
function Eh(h, e) {
  const t = Kn(e, this.size, 16);
  h.uniformMatrix4fv(this.addr, !1, t);
}
function Th(h, e) {
  h.uniform1iv(this.addr, e);
}
function Ah(h, e) {
  h.uniform2iv(this.addr, e);
}
function Ch(h, e) {
  h.uniform3iv(this.addr, e);
}
function Lh(h, e) {
  h.uniform4iv(this.addr, e);
}
function Rh(h, e) {
  h.uniform1uiv(this.addr, e);
}
function Fh(h, e) {
  h.uniform2uiv(this.addr, e);
}
function Dh(h, e) {
  h.uniform3uiv(this.addr, e);
}
function Ph(h, e) {
  h.uniform4uiv(this.addr, e);
}
function Ih(h, e, t) {
  const n = e.length, i = Yi(t, n);
  h.uniform1iv(this.addr, i);
  for (let s = 0; s !== n; ++s)
    t.setTexture2D(e[s] || po, i[s]);
}
function zh(h, e, t) {
  const n = e.length, i = Yi(t, n);
  h.uniform1iv(this.addr, i);
  for (let s = 0; s !== n; ++s)
    t.setTexture3D(e[s] || go, i[s]);
}
function Bh(h, e, t) {
  const n = e.length, i = Yi(t, n);
  h.uniform1iv(this.addr, i);
  for (let s = 0; s !== n; ++s)
    t.setTextureCube(e[s] || _o, i[s]);
}
function Nh(h, e, t) {
  const n = e.length, i = Yi(t, n);
  h.uniform1iv(this.addr, i);
  for (let s = 0; s !== n; ++s)
    t.setTexture2DArray(e[s] || mo, i[s]);
}
function Oh(h) {
  switch (h) {
    case 5126:
      return xh;
    case 35664:
      return yh;
    case 35665:
      return bh;
    case 35666:
      return wh;
    case 35674:
      return Mh;
    case 35675:
      return Sh;
    case 35676:
      return Eh;
    case 5124:
    case 35670:
      return Th;
    case 35667:
    case 35671:
      return Ah;
    case 35668:
    case 35672:
      return Ch;
    case 35669:
    case 35673:
      return Lh;
    case 5125:
      return Rh;
    case 36294:
      return Fh;
    case 36295:
      return Dh;
    case 36296:
      return Ph;
    case 35678:
    case 36198:
    case 36298:
    case 36306:
    case 35682:
      return Ih;
    case 35679:
    case 36299:
    case 36307:
      return zh;
    case 35680:
    case 36300:
    case 36308:
    case 36293:
      return Bh;
    case 36289:
    case 36303:
    case 36311:
    case 36292:
      return Nh;
  }
}
class Uh {
  constructor(e, t, n) {
    this.id = e, this.addr = n, this.cache = [], this.setValue = vh(t.type);
  }
}
class Gh {
  constructor(e, t, n) {
    this.id = e, this.addr = n, this.cache = [], this.size = t.size, this.setValue = Oh(t.type);
  }
}
class kh {
  constructor(e) {
    this.id = e, this.seq = [], this.map = {};
  }
  setValue(e, t, n) {
    const i = this.seq;
    for (let s = 0, o = i.length; s !== o; ++s) {
      const r = i[s];
      r.setValue(e, t[r.id], n);
    }
  }
}
const Es = /(\w+)(\])?(\[|\.)?/g;
function yr(h, e) {
  h.seq.push(e), h.map[e.id] = e;
}
function Wh(h, e, t) {
  const n = h.name, i = n.length;
  for (Es.lastIndex = 0; ; ) {
    const s = Es.exec(n), o = Es.lastIndex;
    let r = s[1];
    const l = s[2] === "]", a = s[3];
    if (l && (r = r | 0), a === void 0 || a === "[" && o + 2 === i) {
      yr(t, a === void 0 ? new Uh(r, h, e) : new Gh(r, h, e));
      break;
    } else {
      let d = t.map[r];
      d === void 0 && (d = new kh(r), yr(t, d)), t = d;
    }
  }
}
class Vi {
  constructor(e, t) {
    this.seq = [], this.map = {};
    const n = e.getProgramParameter(t, 35718);
    for (let i = 0; i < n; ++i) {
      const s = e.getActiveUniform(t, i), o = e.getUniformLocation(t, s.name);
      Wh(s, o, this);
    }
  }
  setValue(e, t, n, i) {
    const s = this.map[t];
    s !== void 0 && s.setValue(e, n, i);
  }
  setOptional(e, t, n) {
    const i = t[n];
    i !== void 0 && this.setValue(e, n, i);
  }
  static upload(e, t, n, i) {
    for (let s = 0, o = t.length; s !== o; ++s) {
      const r = t[s], l = n[r.id];
      l.needsUpdate !== !1 && r.setValue(e, l.value, i);
    }
  }
  static seqWithValue(e, t) {
    const n = [];
    for (let i = 0, s = e.length; i !== s; ++i) {
      const o = e[i];
      o.id in t && n.push(o);
    }
    return n;
  }
}
function br(h, e, t) {
  const n = h.createShader(e);
  return h.shaderSource(n, t), h.compileShader(n), n;
}
let Vh = 0;
function Hh(h, e) {
  const t = h.split(`
`), n = [], i = Math.max(e - 6, 0), s = Math.min(e + 6, t.length);
  for (let o = i; o < s; o++) {
    const r = o + 1;
    n.push(`${r === e ? ">" : " "} ${r}: ${t[o]}`);
  }
  return n.join(`
`);
}
function qh(h) {
  switch (h) {
    case 3e3:
      return ["Linear", "( value )"];
    case 3001:
      return ["sRGB", "( value )"];
    default:
      return console.warn("THREE.WebGLProgram: Unsupported encoding:", h), ["Linear", "( value )"];
  }
}
function wr(h, e, t) {
  const n = h.getShaderParameter(e, 35713), i = h.getShaderInfoLog(e).trim();
  if (n && i === "")
    return "";
  const s = /ERROR: 0:(\d+)/.exec(i);
  if (s) {
    const o = parseInt(s[1]);
    return t.toUpperCase() + `

` + i + `

` + Hh(h.getShaderSource(e), o);
  } else
    return i;
}
function Xh(h, e) {
  const t = qh(e);
  return "vec4 " + h + "( vec4 value ) { return LinearTo" + t[0] + t[1] + "; }";
}
function jh(h, e) {
  let t;
  switch (e) {
    case 1:
      t = "Linear";
      break;
    case 2:
      t = "Reinhard";
      break;
    case 3:
      t = "OptimizedCineon";
      break;
    case 4:
      t = "ACESFilmic";
      break;
    case 5:
      t = "Custom";
      break;
    default:
      console.warn("THREE.WebGLProgram: Unsupported toneMapping:", e), t = "Linear";
  }
  return "vec3 " + h + "( vec3 color ) { return " + t + "ToneMapping( color ); }";
}
function Yh(h) {
  return [
    h.extensionDerivatives || !!h.envMapCubeUVHeight || h.bumpMap || h.tangentSpaceNormalMap || h.clearcoatNormalMap || h.flatShading || h.shaderID === "physical" ? "#extension GL_OES_standard_derivatives : enable" : "",
    (h.extensionFragDepth || h.logarithmicDepthBuffer) && h.rendererExtensionFragDepth ? "#extension GL_EXT_frag_depth : enable" : "",
    h.extensionDrawBuffers && h.rendererExtensionDrawBuffers ? "#extension GL_EXT_draw_buffers : require" : "",
    (h.extensionShaderTextureLOD || h.envMap || h.transmission) && h.rendererExtensionShaderTextureLod ? "#extension GL_EXT_shader_texture_lod : enable" : ""
  ].filter(li).join(`
`);
}
function Zh(h) {
  const e = [];
  for (const t in h) {
    const n = h[t];
    n !== !1 && e.push("#define " + t + " " + n);
  }
  return e.join(`
`);
}
function $h(h, e) {
  const t = {}, n = h.getProgramParameter(e, 35721);
  for (let i = 0; i < n; i++) {
    const s = h.getActiveAttrib(e, i), o = s.name;
    let r = 1;
    s.type === 35674 && (r = 2), s.type === 35675 && (r = 3), s.type === 35676 && (r = 4), t[o] = {
      type: s.type,
      location: h.getAttribLocation(e, o),
      locationSize: r
    };
  }
  return t;
}
function li(h) {
  return h !== "";
}
function Mr(h, e) {
  return h.replace(/NUM_DIR_LIGHTS/g, e.numDirLights).replace(/NUM_SPOT_LIGHTS/g, e.numSpotLights).replace(/NUM_RECT_AREA_LIGHTS/g, e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g, e.numPointLights).replace(/NUM_HEMI_LIGHTS/g, e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g, e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS/g, e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g, e.numPointLightShadows);
}
function Sr(h, e) {
  return h.replace(/NUM_CLIPPING_PLANES/g, e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g, e.numClippingPlanes - e.numClipIntersection);
}
const Kh = /^[ \t]*#include +<([\w\d./]+)>/gm;
function Ns(h) {
  return h.replace(Kh, Jh);
}
function Jh(h, e) {
  const t = Te[e];
  if (t === void 0)
    throw new Error("Can not resolve #include <" + e + ">");
  return Ns(t);
}
const Qh = /#pragma unroll_loop[\s]+?for \( int i \= (\d+)\; i < (\d+)\; i \+\+ \) \{([\s\S]+?)(?=\})\}/g, eu = /#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;
function Er(h) {
  return h.replace(eu, vo).replace(Qh, tu);
}
function tu(h, e, t, n) {
  return console.warn("WebGLProgram: #pragma unroll_loop shader syntax is deprecated. Please use #pragma unroll_loop_start syntax instead."), vo(h, e, t, n);
}
function vo(h, e, t, n) {
  let i = "";
  for (let s = parseInt(e); s < parseInt(t); s++)
    i += n.replace(/\[\s*i\s*\]/g, "[ " + s + " ]").replace(/UNROLLED_LOOP_INDEX/g, s);
  return i;
}
function Tr(h) {
  let e = "precision " + h.precision + ` float;
precision ` + h.precision + " int;";
  return h.precision === "highp" ? e += `
#define HIGH_PRECISION` : h.precision === "mediump" ? e += `
#define MEDIUM_PRECISION` : h.precision === "lowp" && (e += `
#define LOW_PRECISION`), e;
}
function nu(h) {
  let e = "SHADOWMAP_TYPE_BASIC";
  return h.shadowMapType === 1 ? e = "SHADOWMAP_TYPE_PCF" : h.shadowMapType === 2 ? e = "SHADOWMAP_TYPE_PCF_SOFT" : h.shadowMapType === 3 && (e = "SHADOWMAP_TYPE_VSM"), e;
}
function iu(h) {
  let e = "ENVMAP_TYPE_CUBE";
  if (h.envMap)
    switch (h.envMapMode) {
      case 301:
      case 302:
        e = "ENVMAP_TYPE_CUBE";
        break;
      case 306:
        e = "ENVMAP_TYPE_CUBE_UV";
        break;
    }
  return e;
}
function su(h) {
  let e = "ENVMAP_MODE_REFLECTION";
  if (h.envMap)
    switch (h.envMapMode) {
      case 302:
        e = "ENVMAP_MODE_REFRACTION";
        break;
    }
  return e;
}
function ru(h) {
  let e = "ENVMAP_BLENDING_NONE";
  if (h.envMap)
    switch (h.combine) {
      case 0:
        e = "ENVMAP_BLENDING_MULTIPLY";
        break;
      case 1:
        e = "ENVMAP_BLENDING_MIX";
        break;
      case 2:
        e = "ENVMAP_BLENDING_ADD";
        break;
    }
  return e;
}
function ou(h) {
  const e = h.envMapCubeUVHeight;
  if (e === null)
    return null;
  const t = Math.log2(e) - 2, n = 1 / e;
  return { texelWidth: 1 / (3 * Math.max(Math.pow(2, t), 7 * 16)), texelHeight: n, maxMip: t };
}
function au(h, e, t, n) {
  const i = h.getContext(), s = t.defines;
  let o = t.vertexShader, r = t.fragmentShader;
  const l = nu(t), a = iu(t), c = su(t), d = ru(t), u = ou(t), m = t.isWebGL2 ? "" : Yh(t), g = Zh(s), p = i.createProgram();
  let f, v, _ = t.glslVersion ? "#version " + t.glslVersion + `
` : "";
  t.isRawShaderMaterial ? (f = [
    g
  ].filter(li).join(`
`), f.length > 0 && (f += `
`), v = [
    m,
    g
  ].filter(li).join(`
`), v.length > 0 && (v += `
`)) : (f = [
    Tr(t),
    "#define SHADER_NAME " + t.shaderName,
    g,
    t.instancing ? "#define USE_INSTANCING" : "",
    t.instancingColor ? "#define USE_INSTANCING_COLOR" : "",
    t.supportsVertexTextures ? "#define VERTEX_TEXTURES" : "",
    t.useFog && t.fog ? "#define USE_FOG" : "",
    t.useFog && t.fogExp2 ? "#define FOG_EXP2" : "",
    t.map ? "#define USE_MAP" : "",
    t.envMap ? "#define USE_ENVMAP" : "",
    t.envMap ? "#define " + c : "",
    t.lightMap ? "#define USE_LIGHTMAP" : "",
    t.aoMap ? "#define USE_AOMAP" : "",
    t.emissiveMap ? "#define USE_EMISSIVEMAP" : "",
    t.bumpMap ? "#define USE_BUMPMAP" : "",
    t.normalMap ? "#define USE_NORMALMAP" : "",
    t.normalMap && t.objectSpaceNormalMap ? "#define OBJECTSPACE_NORMALMAP" : "",
    t.normalMap && t.tangentSpaceNormalMap ? "#define TANGENTSPACE_NORMALMAP" : "",
    t.clearcoatMap ? "#define USE_CLEARCOATMAP" : "",
    t.clearcoatRoughnessMap ? "#define USE_CLEARCOAT_ROUGHNESSMAP" : "",
    t.clearcoatNormalMap ? "#define USE_CLEARCOAT_NORMALMAP" : "",
    t.iridescenceMap ? "#define USE_IRIDESCENCEMAP" : "",
    t.iridescenceThicknessMap ? "#define USE_IRIDESCENCE_THICKNESSMAP" : "",
    t.displacementMap && t.supportsVertexTextures ? "#define USE_DISPLACEMENTMAP" : "",
    t.specularMap ? "#define USE_SPECULARMAP" : "",
    t.specularIntensityMap ? "#define USE_SPECULARINTENSITYMAP" : "",
    t.specularColorMap ? "#define USE_SPECULARCOLORMAP" : "",
    t.roughnessMap ? "#define USE_ROUGHNESSMAP" : "",
    t.metalnessMap ? "#define USE_METALNESSMAP" : "",
    t.alphaMap ? "#define USE_ALPHAMAP" : "",
    t.transmission ? "#define USE_TRANSMISSION" : "",
    t.transmissionMap ? "#define USE_TRANSMISSIONMAP" : "",
    t.thicknessMap ? "#define USE_THICKNESSMAP" : "",
    t.sheenColorMap ? "#define USE_SHEENCOLORMAP" : "",
    t.sheenRoughnessMap ? "#define USE_SHEENROUGHNESSMAP" : "",
    t.vertexTangents ? "#define USE_TANGENT" : "",
    t.vertexColors ? "#define USE_COLOR" : "",
    t.vertexAlphas ? "#define USE_COLOR_ALPHA" : "",
    t.vertexUvs ? "#define USE_UV" : "",
    t.uvsVertexOnly ? "#define UVS_VERTEX_ONLY" : "",
    t.flatShading ? "#define FLAT_SHADED" : "",
    t.skinning ? "#define USE_SKINNING" : "",
    t.morphTargets ? "#define USE_MORPHTARGETS" : "",
    t.morphNormals && t.flatShading === !1 ? "#define USE_MORPHNORMALS" : "",
    t.morphColors && t.isWebGL2 ? "#define USE_MORPHCOLORS" : "",
    t.morphTargetsCount > 0 && t.isWebGL2 ? "#define MORPHTARGETS_TEXTURE" : "",
    t.morphTargetsCount > 0 && t.isWebGL2 ? "#define MORPHTARGETS_TEXTURE_STRIDE " + t.morphTextureStride : "",
    t.morphTargetsCount > 0 && t.isWebGL2 ? "#define MORPHTARGETS_COUNT " + t.morphTargetsCount : "",
    t.doubleSided ? "#define DOUBLE_SIDED" : "",
    t.flipSided ? "#define FLIP_SIDED" : "",
    t.shadowMapEnabled ? "#define USE_SHADOWMAP" : "",
    t.shadowMapEnabled ? "#define " + l : "",
    t.sizeAttenuation ? "#define USE_SIZEATTENUATION" : "",
    t.logarithmicDepthBuffer ? "#define USE_LOGDEPTHBUF" : "",
    t.logarithmicDepthBuffer && t.rendererExtensionFragDepth ? "#define USE_LOGDEPTHBUF_EXT" : "",
    "uniform mat4 modelMatrix;",
    "uniform mat4 modelViewMatrix;",
    "uniform mat4 projectionMatrix;",
    "uniform mat4 viewMatrix;",
    "uniform mat3 normalMatrix;",
    "uniform vec3 cameraPosition;",
    "uniform bool isOrthographic;",
    "#ifdef USE_INSTANCING",
    "	attribute mat4 instanceMatrix;",
    "#endif",
    "#ifdef USE_INSTANCING_COLOR",
    "	attribute vec3 instanceColor;",
    "#endif",
    "attribute vec3 position;",
    "attribute vec3 normal;",
    "attribute vec2 uv;",
    "#ifdef USE_TANGENT",
    "	attribute vec4 tangent;",
    "#endif",
    "#if defined( USE_COLOR_ALPHA )",
    "	attribute vec4 color;",
    "#elif defined( USE_COLOR )",
    "	attribute vec3 color;",
    "#endif",
    "#if ( defined( USE_MORPHTARGETS ) && ! defined( MORPHTARGETS_TEXTURE ) )",
    "	attribute vec3 morphTarget0;",
    "	attribute vec3 morphTarget1;",
    "	attribute vec3 morphTarget2;",
    "	attribute vec3 morphTarget3;",
    "	#ifdef USE_MORPHNORMALS",
    "		attribute vec3 morphNormal0;",
    "		attribute vec3 morphNormal1;",
    "		attribute vec3 morphNormal2;",
    "		attribute vec3 morphNormal3;",
    "	#else",
    "		attribute vec3 morphTarget4;",
    "		attribute vec3 morphTarget5;",
    "		attribute vec3 morphTarget6;",
    "		attribute vec3 morphTarget7;",
    "	#endif",
    "#endif",
    "#ifdef USE_SKINNING",
    "	attribute vec4 skinIndex;",
    "	attribute vec4 skinWeight;",
    "#endif",
    `
`
  ].filter(li).join(`
`), v = [
    m,
    Tr(t),
    "#define SHADER_NAME " + t.shaderName,
    g,
    t.useFog && t.fog ? "#define USE_FOG" : "",
    t.useFog && t.fogExp2 ? "#define FOG_EXP2" : "",
    t.map ? "#define USE_MAP" : "",
    t.matcap ? "#define USE_MATCAP" : "",
    t.envMap ? "#define USE_ENVMAP" : "",
    t.envMap ? "#define " + a : "",
    t.envMap ? "#define " + c : "",
    t.envMap ? "#define " + d : "",
    u ? "#define CUBEUV_TEXEL_WIDTH " + u.texelWidth : "",
    u ? "#define CUBEUV_TEXEL_HEIGHT " + u.texelHeight : "",
    u ? "#define CUBEUV_MAX_MIP " + u.maxMip + ".0" : "",
    t.lightMap ? "#define USE_LIGHTMAP" : "",
    t.aoMap ? "#define USE_AOMAP" : "",
    t.emissiveMap ? "#define USE_EMISSIVEMAP" : "",
    t.bumpMap ? "#define USE_BUMPMAP" : "",
    t.normalMap ? "#define USE_NORMALMAP" : "",
    t.normalMap && t.objectSpaceNormalMap ? "#define OBJECTSPACE_NORMALMAP" : "",
    t.normalMap && t.tangentSpaceNormalMap ? "#define TANGENTSPACE_NORMALMAP" : "",
    t.clearcoat ? "#define USE_CLEARCOAT" : "",
    t.clearcoatMap ? "#define USE_CLEARCOATMAP" : "",
    t.clearcoatRoughnessMap ? "#define USE_CLEARCOAT_ROUGHNESSMAP" : "",
    t.clearcoatNormalMap ? "#define USE_CLEARCOAT_NORMALMAP" : "",
    t.iridescence ? "#define USE_IRIDESCENCE" : "",
    t.iridescenceMap ? "#define USE_IRIDESCENCEMAP" : "",
    t.iridescenceThicknessMap ? "#define USE_IRIDESCENCE_THICKNESSMAP" : "",
    t.specularMap ? "#define USE_SPECULARMAP" : "",
    t.specularIntensityMap ? "#define USE_SPECULARINTENSITYMAP" : "",
    t.specularColorMap ? "#define USE_SPECULARCOLORMAP" : "",
    t.roughnessMap ? "#define USE_ROUGHNESSMAP" : "",
    t.metalnessMap ? "#define USE_METALNESSMAP" : "",
    t.alphaMap ? "#define USE_ALPHAMAP" : "",
    t.alphaTest ? "#define USE_ALPHATEST" : "",
    t.sheen ? "#define USE_SHEEN" : "",
    t.sheenColorMap ? "#define USE_SHEENCOLORMAP" : "",
    t.sheenRoughnessMap ? "#define USE_SHEENROUGHNESSMAP" : "",
    t.transmission ? "#define USE_TRANSMISSION" : "",
    t.transmissionMap ? "#define USE_TRANSMISSIONMAP" : "",
    t.thicknessMap ? "#define USE_THICKNESSMAP" : "",
    t.decodeVideoTexture ? "#define DECODE_VIDEO_TEXTURE" : "",
    t.vertexTangents ? "#define USE_TANGENT" : "",
    t.vertexColors || t.instancingColor ? "#define USE_COLOR" : "",
    t.vertexAlphas ? "#define USE_COLOR_ALPHA" : "",
    t.vertexUvs ? "#define USE_UV" : "",
    t.uvsVertexOnly ? "#define UVS_VERTEX_ONLY" : "",
    t.gradientMap ? "#define USE_GRADIENTMAP" : "",
    t.flatShading ? "#define FLAT_SHADED" : "",
    t.doubleSided ? "#define DOUBLE_SIDED" : "",
    t.flipSided ? "#define FLIP_SIDED" : "",
    t.shadowMapEnabled ? "#define USE_SHADOWMAP" : "",
    t.shadowMapEnabled ? "#define " + l : "",
    t.premultipliedAlpha ? "#define PREMULTIPLIED_ALPHA" : "",
    t.physicallyCorrectLights ? "#define PHYSICALLY_CORRECT_LIGHTS" : "",
    t.logarithmicDepthBuffer ? "#define USE_LOGDEPTHBUF" : "",
    t.logarithmicDepthBuffer && t.rendererExtensionFragDepth ? "#define USE_LOGDEPTHBUF_EXT" : "",
    "uniform mat4 viewMatrix;",
    "uniform vec3 cameraPosition;",
    "uniform bool isOrthographic;",
    t.toneMapping !== 0 ? "#define TONE_MAPPING" : "",
    t.toneMapping !== 0 ? Te.tonemapping_pars_fragment : "",
    t.toneMapping !== 0 ? jh("toneMapping", t.toneMapping) : "",
    t.dithering ? "#define DITHERING" : "",
    t.opaque ? "#define OPAQUE" : "",
    Te.encodings_pars_fragment,
    Xh("linearToOutputTexel", t.outputEncoding),
    t.useDepthPacking ? "#define DEPTH_PACKING " + t.depthPacking : "",
    `
`
  ].filter(li).join(`
`)), o = Ns(o), o = Mr(o, t), o = Sr(o, t), r = Ns(r), r = Mr(r, t), r = Sr(r, t), o = Er(o), r = Er(r), t.isWebGL2 && t.isRawShaderMaterial !== !0 && (_ = `#version 300 es
`, f = [
    "precision mediump sampler2DArray;",
    "#define attribute in",
    "#define varying out",
    "#define texture2D texture"
  ].join(`
`) + `
` + f, v = [
    "#define varying in",
    t.glslVersion === Zs ? "" : "layout(location = 0) out highp vec4 pc_fragColor;",
    t.glslVersion === Zs ? "" : "#define gl_FragColor pc_fragColor",
    "#define gl_FragDepthEXT gl_FragDepth",
    "#define texture2D texture",
    "#define textureCube texture",
    "#define texture2DProj textureProj",
    "#define texture2DLodEXT textureLod",
    "#define texture2DProjLodEXT textureProjLod",
    "#define textureCubeLodEXT textureLod",
    "#define texture2DGradEXT textureGrad",
    "#define texture2DProjGradEXT textureProjGrad",
    "#define textureCubeGradEXT textureGrad"
  ].join(`
`) + `
` + v);
  const w = _ + f + o, x = _ + v + r, M = br(i, 35633, w), E = br(i, 35632, x);
  if (i.attachShader(p, M), i.attachShader(p, E), t.index0AttributeName !== void 0 ? i.bindAttribLocation(p, 0, t.index0AttributeName) : t.morphTargets === !0 && i.bindAttribLocation(p, 0, "position"), i.linkProgram(p), h.debug.checkShaderErrors) {
    const A = i.getProgramInfoLog(p).trim(), F = i.getShaderInfoLog(M).trim(), P = i.getShaderInfoLog(E).trim();
    let G = !0, z = !0;
    if (i.getProgramParameter(p, 35714) === !1) {
      G = !1;
      const L = wr(i, M, "vertex"), I = wr(i, E, "fragment");
      console.error(
        "THREE.WebGLProgram: Shader Error " + i.getError() + " - VALIDATE_STATUS " + i.getProgramParameter(p, 35715) + `

Program Info Log: ` + A + `
` + L + `
` + I
      );
    } else
      A !== "" ? console.warn("THREE.WebGLProgram: Program Info Log:", A) : (F === "" || P === "") && (z = !1);
    z && (this.diagnostics = {
      runnable: G,
      programLog: A,
      vertexShader: {
        log: F,
        prefix: f
      },
      fragmentShader: {
        log: P,
        prefix: v
      }
    });
  }
  i.deleteShader(M), i.deleteShader(E);
  let R;
  this.getUniforms = function() {
    return R === void 0 && (R = new Vi(i, p)), R;
  };
  let y;
  return this.getAttributes = function() {
    return y === void 0 && (y = $h(i, p)), y;
  }, this.destroy = function() {
    n.releaseStatesOfProgram(this), i.deleteProgram(p), this.program = void 0;
  }, this.name = t.shaderName, this.id = Vh++, this.cacheKey = e, this.usedTimes = 1, this.program = p, this.vertexShader = M, this.fragmentShader = E, this;
}
let lu = 0;
class cu {
  constructor() {
    this.shaderCache = /* @__PURE__ */ new Map(), this.materialCache = /* @__PURE__ */ new Map();
  }
  update(e) {
    const t = e.vertexShader, n = e.fragmentShader, i = this._getShaderStage(t), s = this._getShaderStage(n), o = this._getShaderCacheForMaterial(e);
    return o.has(i) === !1 && (o.add(i), i.usedTimes++), o.has(s) === !1 && (o.add(s), s.usedTimes++), this;
  }
  remove(e) {
    const t = this.materialCache.get(e);
    for (const n of t)
      n.usedTimes--, n.usedTimes === 0 && this.shaderCache.delete(n.code);
    return this.materialCache.delete(e), this;
  }
  getVertexShaderID(e) {
    return this._getShaderStage(e.vertexShader).id;
  }
  getFragmentShaderID(e) {
    return this._getShaderStage(e.fragmentShader).id;
  }
  dispose() {
    this.shaderCache.clear(), this.materialCache.clear();
  }
  _getShaderCacheForMaterial(e) {
    const t = this.materialCache;
    return t.has(e) === !1 && t.set(e, /* @__PURE__ */ new Set()), t.get(e);
  }
  _getShaderStage(e) {
    const t = this.shaderCache;
    if (t.has(e) === !1) {
      const n = new hu(e);
      t.set(e, n);
    }
    return t.get(e);
  }
}
class hu {
  constructor(e) {
    this.id = lu++, this.code = e, this.usedTimes = 0;
  }
}
function uu(h, e, t, n, i, s, o) {
  const r = new oo(), l = new cu(), a = [], c = i.isWebGL2, d = i.logarithmicDepthBuffer, u = i.vertexTextures;
  let m = i.precision;
  const g = {
    MeshDepthMaterial: "depth",
    MeshDistanceMaterial: "distanceRGBA",
    MeshNormalMaterial: "normal",
    MeshBasicMaterial: "basic",
    MeshLambertMaterial: "lambert",
    MeshPhongMaterial: "phong",
    MeshToonMaterial: "toon",
    MeshStandardMaterial: "physical",
    MeshPhysicalMaterial: "physical",
    MeshMatcapMaterial: "matcap",
    LineBasicMaterial: "basic",
    LineDashedMaterial: "dashed",
    PointsMaterial: "points",
    ShadowMaterial: "shadow",
    SpriteMaterial: "sprite"
  };
  function p(y, A, F, P, G) {
    const z = P.fog, L = G.geometry, I = y.isMeshStandardMaterial ? P.environment : null, D = (y.isMeshStandardMaterial ? t : e).get(y.envMap || I), q = !!D && D.mapping === 306 ? D.image.height : null, k = g[y.type];
    y.precision !== null && (m = i.getMaxPrecision(y.precision), m !== y.precision && console.warn("THREE.WebGLProgram.getParameters:", y.precision, "not supported, using", m, "instead."));
    const N = L.morphAttributes.position || L.morphAttributes.normal || L.morphAttributes.color, H = N !== void 0 ? N.length : 0;
    let J = 0;
    L.morphAttributes.position !== void 0 && (J = 1), L.morphAttributes.normal !== void 0 && (J = 2), L.morphAttributes.color !== void 0 && (J = 3);
    let V, ee, ce, ge;
    if (k) {
      const Oe = Bt[k];
      V = Oe.vertexShader, ee = Oe.fragmentShader;
    } else
      V = y.vertexShader, ee = y.fragmentShader, l.update(y), ce = l.getVertexShaderID(y), ge = l.getFragmentShaderID(y);
    const $ = h.getRenderTarget(), De = y.alphaTest > 0, ve = y.clearcoat > 0, xe = y.iridescence > 0;
    return {
      isWebGL2: c,
      shaderID: k,
      shaderName: y.type,
      vertexShader: V,
      fragmentShader: ee,
      defines: y.defines,
      customVertexShaderID: ce,
      customFragmentShaderID: ge,
      isRawShaderMaterial: y.isRawShaderMaterial === !0,
      glslVersion: y.glslVersion,
      precision: m,
      instancing: G.isInstancedMesh === !0,
      instancingColor: G.isInstancedMesh === !0 && G.instanceColor !== null,
      supportsVertexTextures: u,
      outputEncoding: $ === null ? h.outputEncoding : $.isXRRenderTarget === !0 ? $.texture.encoding : 3e3,
      map: !!y.map,
      matcap: !!y.matcap,
      envMap: !!D,
      envMapMode: D && D.mapping,
      envMapCubeUVHeight: q,
      lightMap: !!y.lightMap,
      aoMap: !!y.aoMap,
      emissiveMap: !!y.emissiveMap,
      bumpMap: !!y.bumpMap,
      normalMap: !!y.normalMap,
      objectSpaceNormalMap: y.normalMapType === 1,
      tangentSpaceNormalMap: y.normalMapType === 0,
      decodeVideoTexture: !!y.map && y.map.isVideoTexture === !0 && y.map.encoding === 3001,
      clearcoat: ve,
      clearcoatMap: ve && !!y.clearcoatMap,
      clearcoatRoughnessMap: ve && !!y.clearcoatRoughnessMap,
      clearcoatNormalMap: ve && !!y.clearcoatNormalMap,
      iridescence: xe,
      iridescenceMap: xe && !!y.iridescenceMap,
      iridescenceThicknessMap: xe && !!y.iridescenceThicknessMap,
      displacementMap: !!y.displacementMap,
      roughnessMap: !!y.roughnessMap,
      metalnessMap: !!y.metalnessMap,
      specularMap: !!y.specularMap,
      specularIntensityMap: !!y.specularIntensityMap,
      specularColorMap: !!y.specularColorMap,
      opaque: y.transparent === !1 && y.blending === 1,
      alphaMap: !!y.alphaMap,
      alphaTest: De,
      gradientMap: !!y.gradientMap,
      sheen: y.sheen > 0,
      sheenColorMap: !!y.sheenColorMap,
      sheenRoughnessMap: !!y.sheenRoughnessMap,
      transmission: y.transmission > 0,
      transmissionMap: !!y.transmissionMap,
      thicknessMap: !!y.thicknessMap,
      combine: y.combine,
      vertexTangents: !!y.normalMap && !!L.attributes.tangent,
      vertexColors: y.vertexColors,
      vertexAlphas: y.vertexColors === !0 && !!L.attributes.color && L.attributes.color.itemSize === 4,
      vertexUvs: !!y.map || !!y.bumpMap || !!y.normalMap || !!y.specularMap || !!y.alphaMap || !!y.emissiveMap || !!y.roughnessMap || !!y.metalnessMap || !!y.clearcoatMap || !!y.clearcoatRoughnessMap || !!y.clearcoatNormalMap || !!y.iridescenceMap || !!y.iridescenceThicknessMap || !!y.displacementMap || !!y.transmissionMap || !!y.thicknessMap || !!y.specularIntensityMap || !!y.specularColorMap || !!y.sheenColorMap || !!y.sheenRoughnessMap,
      uvsVertexOnly: !(!!y.map || !!y.bumpMap || !!y.normalMap || !!y.specularMap || !!y.alphaMap || !!y.emissiveMap || !!y.roughnessMap || !!y.metalnessMap || !!y.clearcoatNormalMap || !!y.iridescenceMap || !!y.iridescenceThicknessMap || y.transmission > 0 || !!y.transmissionMap || !!y.thicknessMap || !!y.specularIntensityMap || !!y.specularColorMap || y.sheen > 0 || !!y.sheenColorMap || !!y.sheenRoughnessMap) && !!y.displacementMap,
      fog: !!z,
      useFog: y.fog === !0,
      fogExp2: z && z.isFogExp2,
      flatShading: !!y.flatShading,
      sizeAttenuation: y.sizeAttenuation,
      logarithmicDepthBuffer: d,
      skinning: G.isSkinnedMesh === !0,
      morphTargets: L.morphAttributes.position !== void 0,
      morphNormals: L.morphAttributes.normal !== void 0,
      morphColors: L.morphAttributes.color !== void 0,
      morphTargetsCount: H,
      morphTextureStride: J,
      numDirLights: A.directional.length,
      numPointLights: A.point.length,
      numSpotLights: A.spot.length,
      numRectAreaLights: A.rectArea.length,
      numHemiLights: A.hemi.length,
      numDirLightShadows: A.directionalShadowMap.length,
      numPointLightShadows: A.pointShadowMap.length,
      numSpotLightShadows: A.spotShadowMap.length,
      numClippingPlanes: o.numPlanes,
      numClipIntersection: o.numIntersection,
      dithering: y.dithering,
      shadowMapEnabled: h.shadowMap.enabled && F.length > 0,
      shadowMapType: h.shadowMap.type,
      toneMapping: y.toneMapped ? h.toneMapping : 0,
      physicallyCorrectLights: h.physicallyCorrectLights,
      premultipliedAlpha: y.premultipliedAlpha,
      doubleSided: y.side === 2,
      flipSided: y.side === 1,
      useDepthPacking: !!y.depthPacking,
      depthPacking: y.depthPacking || 0,
      index0AttributeName: y.index0AttributeName,
      extensionDerivatives: y.extensions && y.extensions.derivatives,
      extensionFragDepth: y.extensions && y.extensions.fragDepth,
      extensionDrawBuffers: y.extensions && y.extensions.drawBuffers,
      extensionShaderTextureLOD: y.extensions && y.extensions.shaderTextureLOD,
      rendererExtensionFragDepth: c || n.has("EXT_frag_depth"),
      rendererExtensionDrawBuffers: c || n.has("WEBGL_draw_buffers"),
      rendererExtensionShaderTextureLod: c || n.has("EXT_shader_texture_lod"),
      customProgramCacheKey: y.customProgramCacheKey()
    };
  }
  function f(y) {
    const A = [];
    if (y.shaderID ? A.push(y.shaderID) : (A.push(y.customVertexShaderID), A.push(y.customFragmentShaderID)), y.defines !== void 0)
      for (const F in y.defines)
        A.push(F), A.push(y.defines[F]);
    return y.isRawShaderMaterial === !1 && (v(A, y), _(A, y), A.push(h.outputEncoding)), A.push(y.customProgramCacheKey), A.join();
  }
  function v(y, A) {
    y.push(A.precision), y.push(A.outputEncoding), y.push(A.envMapMode), y.push(A.envMapCubeUVHeight), y.push(A.combine), y.push(A.vertexUvs), y.push(A.fogExp2), y.push(A.sizeAttenuation), y.push(A.morphTargetsCount), y.push(A.morphAttributeCount), y.push(A.numDirLights), y.push(A.numPointLights), y.push(A.numSpotLights), y.push(A.numHemiLights), y.push(A.numRectAreaLights), y.push(A.numDirLightShadows), y.push(A.numPointLightShadows), y.push(A.numSpotLightShadows), y.push(A.shadowMapType), y.push(A.toneMapping), y.push(A.numClippingPlanes), y.push(A.numClipIntersection), y.push(A.depthPacking);
  }
  function _(y, A) {
    r.disableAll(), A.isWebGL2 && r.enable(0), A.supportsVertexTextures && r.enable(1), A.instancing && r.enable(2), A.instancingColor && r.enable(3), A.map && r.enable(4), A.matcap && r.enable(5), A.envMap && r.enable(6), A.lightMap && r.enable(7), A.aoMap && r.enable(8), A.emissiveMap && r.enable(9), A.bumpMap && r.enable(10), A.normalMap && r.enable(11), A.objectSpaceNormalMap && r.enable(12), A.tangentSpaceNormalMap && r.enable(13), A.clearcoat && r.enable(14), A.clearcoatMap && r.enable(15), A.clearcoatRoughnessMap && r.enable(16), A.clearcoatNormalMap && r.enable(17), A.iridescence && r.enable(18), A.iridescenceMap && r.enable(19), A.iridescenceThicknessMap && r.enable(20), A.displacementMap && r.enable(21), A.specularMap && r.enable(22), A.roughnessMap && r.enable(23), A.metalnessMap && r.enable(24), A.gradientMap && r.enable(25), A.alphaMap && r.enable(26), A.alphaTest && r.enable(27), A.vertexColors && r.enable(28), A.vertexAlphas && r.enable(29), A.vertexUvs && r.enable(30), A.vertexTangents && r.enable(31), A.uvsVertexOnly && r.enable(32), A.fog && r.enable(33), y.push(r.mask), r.disableAll(), A.useFog && r.enable(0), A.flatShading && r.enable(1), A.logarithmicDepthBuffer && r.enable(2), A.skinning && r.enable(3), A.morphTargets && r.enable(4), A.morphNormals && r.enable(5), A.morphColors && r.enable(6), A.premultipliedAlpha && r.enable(7), A.shadowMapEnabled && r.enable(8), A.physicallyCorrectLights && r.enable(9), A.doubleSided && r.enable(10), A.flipSided && r.enable(11), A.useDepthPacking && r.enable(12), A.dithering && r.enable(13), A.specularIntensityMap && r.enable(14), A.specularColorMap && r.enable(15), A.transmission && r.enable(16), A.transmissionMap && r.enable(17), A.thicknessMap && r.enable(18), A.sheen && r.enable(19), A.sheenColorMap && r.enable(20), A.sheenRoughnessMap && r.enable(21), A.decodeVideoTexture && r.enable(22), A.opaque && r.enable(23), y.push(r.mask);
  }
  function w(y) {
    const A = g[y.type];
    let F;
    if (A) {
      const P = Bt[A];
      F = Jo.clone(P.uniforms);
    } else
      F = y.uniforms;
    return F;
  }
  function x(y, A) {
    let F;
    for (let P = 0, G = a.length; P < G; P++) {
      const z = a[P];
      if (z.cacheKey === A) {
        F = z, ++F.usedTimes;
        break;
      }
    }
    return F === void 0 && (F = new au(h, A, y, s), a.push(F)), F;
  }
  function M(y) {
    if (--y.usedTimes === 0) {
      const A = a.indexOf(y);
      a[A] = a[a.length - 1], a.pop(), y.destroy();
    }
  }
  function E(y) {
    l.remove(y);
  }
  function R() {
    l.dispose();
  }
  return {
    getParameters: p,
    getProgramCacheKey: f,
    getUniforms: w,
    acquireProgram: x,
    releaseProgram: M,
    releaseShaderCache: E,
    programs: a,
    dispose: R
  };
}
function du() {
  let h = /* @__PURE__ */ new WeakMap();
  function e(s) {
    let o = h.get(s);
    return o === void 0 && (o = {}, h.set(s, o)), o;
  }
  function t(s) {
    h.delete(s);
  }
  function n(s, o, r) {
    h.get(s)[o] = r;
  }
  function i() {
    h = /* @__PURE__ */ new WeakMap();
  }
  return {
    get: e,
    remove: t,
    update: n,
    dispose: i
  };
}
function fu(h, e) {
  return h.groupOrder !== e.groupOrder ? h.groupOrder - e.groupOrder : h.renderOrder !== e.renderOrder ? h.renderOrder - e.renderOrder : h.material.id !== e.material.id ? h.material.id - e.material.id : h.z !== e.z ? h.z - e.z : h.id - e.id;
}
function Ar(h, e) {
  return h.groupOrder !== e.groupOrder ? h.groupOrder - e.groupOrder : h.renderOrder !== e.renderOrder ? h.renderOrder - e.renderOrder : h.z !== e.z ? e.z - h.z : h.id - e.id;
}
function Cr() {
  const h = [];
  let e = 0;
  const t = [], n = [], i = [];
  function s() {
    e = 0, t.length = 0, n.length = 0, i.length = 0;
  }
  function o(d, u, m, g, p, f) {
    let v = h[e];
    return v === void 0 ? (v = {
      id: d.id,
      object: d,
      geometry: u,
      material: m,
      groupOrder: g,
      renderOrder: d.renderOrder,
      z: p,
      group: f
    }, h[e] = v) : (v.id = d.id, v.object = d, v.geometry = u, v.material = m, v.groupOrder = g, v.renderOrder = d.renderOrder, v.z = p, v.group = f), e++, v;
  }
  function r(d, u, m, g, p, f) {
    const v = o(d, u, m, g, p, f);
    m.transmission > 0 ? n.push(v) : m.transparent === !0 ? i.push(v) : t.push(v);
  }
  function l(d, u, m, g, p, f) {
    const v = o(d, u, m, g, p, f);
    m.transmission > 0 ? n.unshift(v) : m.transparent === !0 ? i.unshift(v) : t.unshift(v);
  }
  function a(d, u) {
    t.length > 1 && t.sort(d || fu), n.length > 1 && n.sort(u || Ar), i.length > 1 && i.sort(u || Ar);
  }
  function c() {
    for (let d = e, u = h.length; d < u; d++) {
      const m = h[d];
      if (m.id === null)
        break;
      m.id = null, m.object = null, m.geometry = null, m.material = null, m.group = null;
    }
  }
  return {
    opaque: t,
    transmissive: n,
    transparent: i,
    init: s,
    push: r,
    unshift: l,
    finish: c,
    sort: a
  };
}
function pu() {
  let h = /* @__PURE__ */ new WeakMap();
  function e(n, i) {
    let s;
    return h.has(n) === !1 ? (s = new Cr(), h.set(n, [s])) : i >= h.get(n).length ? (s = new Cr(), h.get(n).push(s)) : s = h.get(n)[i], s;
  }
  function t() {
    h = /* @__PURE__ */ new WeakMap();
  }
  return {
    get: e,
    dispose: t
  };
}
function mu() {
  const h = {};
  return {
    get: function(e) {
      if (h[e.id] !== void 0)
        return h[e.id];
      let t;
      switch (e.type) {
        case "DirectionalLight":
          t = {
            direction: new O(),
            color: new Ae()
          };
          break;
        case "SpotLight":
          t = {
            position: new O(),
            direction: new O(),
            color: new Ae(),
            distance: 0,
            coneCos: 0,
            penumbraCos: 0,
            decay: 0
          };
          break;
        case "PointLight":
          t = {
            position: new O(),
            color: new Ae(),
            distance: 0,
            decay: 0
          };
          break;
        case "HemisphereLight":
          t = {
            direction: new O(),
            skyColor: new Ae(),
            groundColor: new Ae()
          };
          break;
        case "RectAreaLight":
          t = {
            color: new Ae(),
            position: new O(),
            halfWidth: new O(),
            halfHeight: new O()
          };
          break;
      }
      return h[e.id] = t, t;
    }
  };
}
function gu() {
  const h = {};
  return {
    get: function(e) {
      if (h[e.id] !== void 0)
        return h[e.id];
      let t;
      switch (e.type) {
        case "DirectionalLight":
          t = {
            shadowBias: 0,
            shadowNormalBias: 0,
            shadowRadius: 1,
            shadowMapSize: new Ce()
          };
          break;
        case "SpotLight":
          t = {
            shadowBias: 0,
            shadowNormalBias: 0,
            shadowRadius: 1,
            shadowMapSize: new Ce()
          };
          break;
        case "PointLight":
          t = {
            shadowBias: 0,
            shadowNormalBias: 0,
            shadowRadius: 1,
            shadowMapSize: new Ce(),
            shadowCameraNear: 1,
            shadowCameraFar: 1e3
          };
          break;
      }
      return h[e.id] = t, t;
    }
  };
}
let _u = 0;
function vu(h, e) {
  return (e.castShadow ? 1 : 0) - (h.castShadow ? 1 : 0);
}
function xu(h, e) {
  const t = new mu(), n = gu(), i = {
    version: 0,
    hash: {
      directionalLength: -1,
      pointLength: -1,
      spotLength: -1,
      rectAreaLength: -1,
      hemiLength: -1,
      numDirectionalShadows: -1,
      numPointShadows: -1,
      numSpotShadows: -1
    },
    ambient: [0, 0, 0],
    probe: [],
    directional: [],
    directionalShadow: [],
    directionalShadowMap: [],
    directionalShadowMatrix: [],
    spot: [],
    spotShadow: [],
    spotShadowMap: [],
    spotShadowMatrix: [],
    rectArea: [],
    rectAreaLTC1: null,
    rectAreaLTC2: null,
    point: [],
    pointShadow: [],
    pointShadowMap: [],
    pointShadowMatrix: [],
    hemi: []
  };
  for (let c = 0; c < 9; c++)
    i.probe.push(new O());
  const s = new O(), o = new Ke(), r = new Ke();
  function l(c, d) {
    let u = 0, m = 0, g = 0;
    for (let A = 0; A < 9; A++)
      i.probe[A].set(0, 0, 0);
    let p = 0, f = 0, v = 0, _ = 0, w = 0, x = 0, M = 0, E = 0;
    c.sort(vu);
    const R = d !== !0 ? Math.PI : 1;
    for (let A = 0, F = c.length; A < F; A++) {
      const P = c[A], G = P.color, z = P.intensity, L = P.distance, I = P.shadow && P.shadow.map ? P.shadow.map.texture : null;
      if (P.isAmbientLight)
        u += G.r * z * R, m += G.g * z * R, g += G.b * z * R;
      else if (P.isLightProbe)
        for (let D = 0; D < 9; D++)
          i.probe[D].addScaledVector(P.sh.coefficients[D], z);
      else if (P.isDirectionalLight) {
        const D = t.get(P);
        if (D.color.copy(P.color).multiplyScalar(P.intensity * R), P.castShadow) {
          const q = P.shadow, k = n.get(P);
          k.shadowBias = q.bias, k.shadowNormalBias = q.normalBias, k.shadowRadius = q.radius, k.shadowMapSize = q.mapSize, i.directionalShadow[p] = k, i.directionalShadowMap[p] = I, i.directionalShadowMatrix[p] = P.shadow.matrix, x++;
        }
        i.directional[p] = D, p++;
      } else if (P.isSpotLight) {
        const D = t.get(P);
        if (D.position.setFromMatrixPosition(P.matrixWorld), D.color.copy(G).multiplyScalar(z * R), D.distance = L, D.coneCos = Math.cos(P.angle), D.penumbraCos = Math.cos(P.angle * (1 - P.penumbra)), D.decay = P.decay, P.castShadow) {
          const q = P.shadow, k = n.get(P);
          k.shadowBias = q.bias, k.shadowNormalBias = q.normalBias, k.shadowRadius = q.radius, k.shadowMapSize = q.mapSize, i.spotShadow[v] = k, i.spotShadowMap[v] = I, i.spotShadowMatrix[v] = P.shadow.matrix, E++;
        }
        i.spot[v] = D, v++;
      } else if (P.isRectAreaLight) {
        const D = t.get(P);
        D.color.copy(G).multiplyScalar(z), D.halfWidth.set(P.width * 0.5, 0, 0), D.halfHeight.set(0, P.height * 0.5, 0), i.rectArea[_] = D, _++;
      } else if (P.isPointLight) {
        const D = t.get(P);
        if (D.color.copy(P.color).multiplyScalar(P.intensity * R), D.distance = P.distance, D.decay = P.decay, P.castShadow) {
          const q = P.shadow, k = n.get(P);
          k.shadowBias = q.bias, k.shadowNormalBias = q.normalBias, k.shadowRadius = q.radius, k.shadowMapSize = q.mapSize, k.shadowCameraNear = q.camera.near, k.shadowCameraFar = q.camera.far, i.pointShadow[f] = k, i.pointShadowMap[f] = I, i.pointShadowMatrix[f] = P.shadow.matrix, M++;
        }
        i.point[f] = D, f++;
      } else if (P.isHemisphereLight) {
        const D = t.get(P);
        D.skyColor.copy(P.color).multiplyScalar(z * R), D.groundColor.copy(P.groundColor).multiplyScalar(z * R), i.hemi[w] = D, w++;
      }
    }
    _ > 0 && (e.isWebGL2 || h.has("OES_texture_float_linear") === !0 ? (i.rectAreaLTC1 = ne.LTC_FLOAT_1, i.rectAreaLTC2 = ne.LTC_FLOAT_2) : h.has("OES_texture_half_float_linear") === !0 ? (i.rectAreaLTC1 = ne.LTC_HALF_1, i.rectAreaLTC2 = ne.LTC_HALF_2) : console.error("THREE.WebGLRenderer: Unable to use RectAreaLight. Missing WebGL extensions.")), i.ambient[0] = u, i.ambient[1] = m, i.ambient[2] = g;
    const y = i.hash;
    (y.directionalLength !== p || y.pointLength !== f || y.spotLength !== v || y.rectAreaLength !== _ || y.hemiLength !== w || y.numDirectionalShadows !== x || y.numPointShadows !== M || y.numSpotShadows !== E) && (i.directional.length = p, i.spot.length = v, i.rectArea.length = _, i.point.length = f, i.hemi.length = w, i.directionalShadow.length = x, i.directionalShadowMap.length = x, i.pointShadow.length = M, i.pointShadowMap.length = M, i.spotShadow.length = E, i.spotShadowMap.length = E, i.directionalShadowMatrix.length = x, i.pointShadowMatrix.length = M, i.spotShadowMatrix.length = E, y.directionalLength = p, y.pointLength = f, y.spotLength = v, y.rectAreaLength = _, y.hemiLength = w, y.numDirectionalShadows = x, y.numPointShadows = M, y.numSpotShadows = E, i.version = _u++);
  }
  function a(c, d) {
    let u = 0, m = 0, g = 0, p = 0, f = 0;
    const v = d.matrixWorldInverse;
    for (let _ = 0, w = c.length; _ < w; _++) {
      const x = c[_];
      if (x.isDirectionalLight) {
        const M = i.directional[u];
        M.direction.setFromMatrixPosition(x.matrixWorld), s.setFromMatrixPosition(x.target.matrixWorld), M.direction.sub(s), M.direction.transformDirection(v), u++;
      } else if (x.isSpotLight) {
        const M = i.spot[g];
        M.position.setFromMatrixPosition(x.matrixWorld), M.position.applyMatrix4(v), M.direction.setFromMatrixPosition(x.matrixWorld), s.setFromMatrixPosition(x.target.matrixWorld), M.direction.sub(s), M.direction.transformDirection(v), g++;
      } else if (x.isRectAreaLight) {
        const M = i.rectArea[p];
        M.position.setFromMatrixPosition(x.matrixWorld), M.position.applyMatrix4(v), r.identity(), o.copy(x.matrixWorld), o.premultiply(v), r.extractRotation(o), M.halfWidth.set(x.width * 0.5, 0, 0), M.halfHeight.set(0, x.height * 0.5, 0), M.halfWidth.applyMatrix4(r), M.halfHeight.applyMatrix4(r), p++;
      } else if (x.isPointLight) {
        const M = i.point[m];
        M.position.setFromMatrixPosition(x.matrixWorld), M.position.applyMatrix4(v), m++;
      } else if (x.isHemisphereLight) {
        const M = i.hemi[f];
        M.direction.setFromMatrixPosition(x.matrixWorld), M.direction.transformDirection(v), f++;
      }
    }
  }
  return {
    setup: l,
    setupView: a,
    state: i
  };
}
function Lr(h, e) {
  const t = new xu(h, e), n = [], i = [];
  function s() {
    n.length = 0, i.length = 0;
  }
  function o(d) {
    n.push(d);
  }
  function r(d) {
    i.push(d);
  }
  function l(d) {
    t.setup(n, d);
  }
  function a(d) {
    t.setupView(n, d);
  }
  return {
    init: s,
    state: {
      lightsArray: n,
      shadowsArray: i,
      lights: t
    },
    setupLights: l,
    setupLightsView: a,
    pushLight: o,
    pushShadow: r
  };
}
function yu(h, e) {
  let t = /* @__PURE__ */ new WeakMap();
  function n(s, o = 0) {
    let r;
    return t.has(s) === !1 ? (r = new Lr(h, e), t.set(s, [r])) : o >= t.get(s).length ? (r = new Lr(h, e), t.get(s).push(r)) : r = t.get(s)[o], r;
  }
  function i() {
    t = /* @__PURE__ */ new WeakMap();
  }
  return {
    get: n,
    dispose: i
  };
}
class bu extends An {
  constructor(e) {
    super(), this.isMeshDepthMaterial = !0, this.type = "MeshDepthMaterial", this.depthPacking = 3200, this.map = null, this.alphaMap = null, this.displacementMap = null, this.displacementScale = 1, this.displacementBias = 0, this.wireframe = !1, this.wireframeLinewidth = 1, this.setValues(e);
  }
  copy(e) {
    return super.copy(e), this.depthPacking = e.depthPacking, this.map = e.map, this.alphaMap = e.alphaMap, this.displacementMap = e.displacementMap, this.displacementScale = e.displacementScale, this.displacementBias = e.displacementBias, this.wireframe = e.wireframe, this.wireframeLinewidth = e.wireframeLinewidth, this;
  }
}
class wu extends An {
  constructor(e) {
    super(), this.isMeshDistanceMaterial = !0, this.type = "MeshDistanceMaterial", this.referencePosition = new O(), this.nearDistance = 1, this.farDistance = 1e3, this.map = null, this.alphaMap = null, this.displacementMap = null, this.displacementScale = 1, this.displacementBias = 0, this.setValues(e);
  }
  copy(e) {
    return super.copy(e), this.referencePosition.copy(e.referencePosition), this.nearDistance = e.nearDistance, this.farDistance = e.farDistance, this.map = e.map, this.alphaMap = e.alphaMap, this.displacementMap = e.displacementMap, this.displacementScale = e.displacementScale, this.displacementBias = e.displacementBias, this;
  }
}
const Mu = `void main() {
	gl_Position = vec4( position, 1.0 );
}`, Su = `uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
#include <packing>
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = unpackRGBATo2Half( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ) );
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = unpackRGBAToDepth( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ) );
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( squared_mean - mean * mean );
	gl_FragColor = pack2HalfToRGBA( vec2( mean, std_dev ) );
}`;
function Eu(h, e, t) {
  let n = new Us();
  const i = new Ce(), s = new Ce(), o = new $e(), r = new bu({ depthPacking: 3201 }), l = new wu(), a = {}, c = t.maxTextureSize, d = { 0: 1, 1: 0, 2: 2 }, u = new Tn({
    defines: {
      VSM_SAMPLES: 8
    },
    uniforms: {
      shadow_pass: { value: null },
      resolution: { value: new Ce() },
      radius: { value: 4 }
    },
    vertexShader: Mu,
    fragmentShader: Su
  }), m = u.clone();
  m.defines.HORIZONTAL_PASS = 1;
  const g = new Ut();
  g.setAttribute(
    "position",
    new Ot(
      new Float32Array([-1, -1, 0.5, 3, -1, 0.5, -1, 3, 0.5]),
      3
    )
  );
  const p = new Nt(g, u), f = this;
  this.enabled = !1, this.autoUpdate = !0, this.needsUpdate = !1, this.type = 1, this.render = function(x, M, E) {
    if (f.enabled === !1 || f.autoUpdate === !1 && f.needsUpdate === !1 || x.length === 0)
      return;
    const R = h.getRenderTarget(), y = h.getActiveCubeFace(), A = h.getActiveMipmapLevel(), F = h.state;
    F.setBlending(0), F.buffers.color.setClear(1, 1, 1, 1), F.buffers.depth.setTest(!0), F.setScissorTest(!1);
    for (let P = 0, G = x.length; P < G; P++) {
      const z = x[P], L = z.shadow;
      if (L === void 0) {
        console.warn("THREE.WebGLShadowMap:", z, "has no shadow.");
        continue;
      }
      if (L.autoUpdate === !1 && L.needsUpdate === !1)
        continue;
      i.copy(L.mapSize);
      const I = L.getFrameExtents();
      if (i.multiply(I), s.copy(L.mapSize), (i.x > c || i.y > c) && (i.x > c && (s.x = Math.floor(c / I.x), i.x = s.x * I.x, L.mapSize.x = s.x), i.y > c && (s.y = Math.floor(c / I.y), i.y = s.y * I.y, L.mapSize.y = s.y)), L.map === null) {
        const q = this.type !== 3 ? { minFilter: 1003, magFilter: 1003 } : {};
        L.map = new En(i.x, i.y, q), L.map.texture.name = z.name + ".shadowMap", L.camera.updateProjectionMatrix();
      }
      h.setRenderTarget(L.map), h.clear();
      const D = L.getViewportCount();
      for (let q = 0; q < D; q++) {
        const k = L.getViewport(q);
        o.set(
          s.x * k.x,
          s.y * k.y,
          s.x * k.z,
          s.y * k.w
        ), F.viewport(o), L.updateMatrices(z, q), n = L.getFrustum(), w(M, E, L.camera, z, this.type);
      }
      L.isPointLightShadow !== !0 && this.type === 3 && v(L, E), L.needsUpdate = !1;
    }
    f.needsUpdate = !1, h.setRenderTarget(R, y, A);
  };
  function v(x, M) {
    const E = e.update(p);
    u.defines.VSM_SAMPLES !== x.blurSamples && (u.defines.VSM_SAMPLES = x.blurSamples, m.defines.VSM_SAMPLES = x.blurSamples, u.needsUpdate = !0, m.needsUpdate = !0), x.mapPass === null && (x.mapPass = new En(i.x, i.y)), u.uniforms.shadow_pass.value = x.map.texture, u.uniforms.resolution.value = x.mapSize, u.uniforms.radius.value = x.radius, h.setRenderTarget(x.mapPass), h.clear(), h.renderBufferDirect(M, null, E, u, p, null), m.uniforms.shadow_pass.value = x.mapPass.texture, m.uniforms.resolution.value = x.mapSize, m.uniforms.radius.value = x.radius, h.setRenderTarget(x.map), h.clear(), h.renderBufferDirect(M, null, E, m, p, null);
  }
  function _(x, M, E, R, y, A) {
    let F = null;
    const P = E.isPointLight === !0 ? x.customDistanceMaterial : x.customDepthMaterial;
    if (P !== void 0 ? F = P : F = E.isPointLight === !0 ? l : r, h.localClippingEnabled && M.clipShadows === !0 && Array.isArray(M.clippingPlanes) && M.clippingPlanes.length !== 0 || M.displacementMap && M.displacementScale !== 0 || M.alphaMap && M.alphaTest > 0) {
      const G = F.uuid, z = M.uuid;
      let L = a[G];
      L === void 0 && (L = {}, a[G] = L);
      let I = L[z];
      I === void 0 && (I = F.clone(), L[z] = I), F = I;
    }
    return F.visible = M.visible, F.wireframe = M.wireframe, A === 3 ? F.side = M.shadowSide !== null ? M.shadowSide : M.side : F.side = M.shadowSide !== null ? M.shadowSide : d[M.side], F.alphaMap = M.alphaMap, F.alphaTest = M.alphaTest, F.clipShadows = M.clipShadows, F.clippingPlanes = M.clippingPlanes, F.clipIntersection = M.clipIntersection, F.displacementMap = M.displacementMap, F.displacementScale = M.displacementScale, F.displacementBias = M.displacementBias, F.wireframeLinewidth = M.wireframeLinewidth, F.linewidth = M.linewidth, E.isPointLight === !0 && F.isMeshDistanceMaterial === !0 && (F.referencePosition.setFromMatrixPosition(E.matrixWorld), F.nearDistance = R, F.farDistance = y), F;
  }
  function w(x, M, E, R, y) {
    if (x.visible === !1)
      return;
    if (x.layers.test(M.layers) && (x.isMesh || x.isLine || x.isPoints) && (x.castShadow || x.receiveShadow && y === 3) && (!x.frustumCulled || n.intersectsObject(x))) {
      x.modelViewMatrix.multiplyMatrices(E.matrixWorldInverse, x.matrixWorld);
      const P = e.update(x), G = x.material;
      if (Array.isArray(G)) {
        const z = P.groups;
        for (let L = 0, I = z.length; L < I; L++) {
          const D = z[L], q = G[D.materialIndex];
          if (q && q.visible) {
            const k = _(x, q, R, E.near, E.far, y);
            h.renderBufferDirect(E, null, P, k, x, D);
          }
        }
      } else if (G.visible) {
        const z = _(x, G, R, E.near, E.far, y);
        h.renderBufferDirect(E, null, P, z, x, null);
      }
    }
    const F = x.children;
    for (let P = 0, G = F.length; P < G; P++)
      w(F[P], M, E, R, y);
  }
}
function Tu(h, e, t) {
  const n = t.isWebGL2;
  function i() {
    let B = !1;
    const ae = new $e();
    let Y = null;
    const oe = new $e(0, 0, 0, 0);
    return {
      setMask: function(se) {
        Y !== se && !B && (h.colorMask(se, se, se, se), Y = se);
      },
      setLocked: function(se) {
        B = se;
      },
      setClear: function(se, Re, Je, Ve, en) {
        en === !0 && (se *= Ve, Re *= Ve, Je *= Ve), ae.set(se, Re, Je, Ve), oe.equals(ae) === !1 && (h.clearColor(se, Re, Je, Ve), oe.copy(ae));
      },
      reset: function() {
        B = !1, Y = null, oe.set(-1, 0, 0, 0);
      }
    };
  }
  function s() {
    let B = !1, ae = null, Y = null, oe = null;
    return {
      setTest: function(se) {
        se ? De(2929) : ve(2929);
      },
      setMask: function(se) {
        ae !== se && !B && (h.depthMask(se), ae = se);
      },
      setFunc: function(se) {
        if (Y !== se) {
          if (se)
            switch (se) {
              case 0:
                h.depthFunc(512);
                break;
              case 1:
                h.depthFunc(519);
                break;
              case 2:
                h.depthFunc(513);
                break;
              case 3:
                h.depthFunc(515);
                break;
              case 4:
                h.depthFunc(514);
                break;
              case 5:
                h.depthFunc(518);
                break;
              case 6:
                h.depthFunc(516);
                break;
              case 7:
                h.depthFunc(517);
                break;
              default:
                h.depthFunc(515);
            }
          else
            h.depthFunc(515);
          Y = se;
        }
      },
      setLocked: function(se) {
        B = se;
      },
      setClear: function(se) {
        oe !== se && (h.clearDepth(se), oe = se);
      },
      reset: function() {
        B = !1, ae = null, Y = null, oe = null;
      }
    };
  }
  function o() {
    let B = !1, ae = null, Y = null, oe = null, se = null, Re = null, Je = null, Ve = null, en = null;
    return {
      setTest: function(Ge) {
        B || (Ge ? De(2960) : ve(2960));
      },
      setMask: function(Ge) {
        ae !== Ge && !B && (h.stencilMask(Ge), ae = Ge);
      },
      setFunc: function(Ge, kt, xt) {
        (Y !== Ge || oe !== kt || se !== xt) && (h.stencilFunc(Ge, kt, xt), Y = Ge, oe = kt, se = xt);
      },
      setOp: function(Ge, kt, xt) {
        (Re !== Ge || Je !== kt || Ve !== xt) && (h.stencilOp(Ge, kt, xt), Re = Ge, Je = kt, Ve = xt);
      },
      setLocked: function(Ge) {
        B = Ge;
      },
      setClear: function(Ge) {
        en !== Ge && (h.clearStencil(Ge), en = Ge);
      },
      reset: function() {
        B = !1, ae = null, Y = null, oe = null, se = null, Re = null, Je = null, Ve = null, en = null;
      }
    };
  }
  const r = new i(), l = new s(), a = new o(), c = /* @__PURE__ */ new WeakMap(), d = /* @__PURE__ */ new WeakMap();
  let u = {}, m = {}, g = /* @__PURE__ */ new WeakMap(), p = [], f = null, v = !1, _ = null, w = null, x = null, M = null, E = null, R = null, y = null, A = !1, F = null, P = null, G = null, z = null, L = null;
  const I = h.getParameter(35661);
  let D = !1, q = 0;
  const k = h.getParameter(7938);
  k.indexOf("WebGL") !== -1 ? (q = parseFloat(/^WebGL (\d)/.exec(k)[1]), D = q >= 1) : k.indexOf("OpenGL ES") !== -1 && (q = parseFloat(/^OpenGL ES (\d)/.exec(k)[1]), D = q >= 2);
  let N = null, H = {};
  const J = h.getParameter(3088), V = h.getParameter(2978), ee = new $e().fromArray(J), ce = new $e().fromArray(V);
  function ge(B, ae, Y) {
    const oe = new Uint8Array(4), se = h.createTexture();
    h.bindTexture(B, se), h.texParameteri(B, 10241, 9728), h.texParameteri(B, 10240, 9728);
    for (let Re = 0; Re < Y; Re++)
      h.texImage2D(ae + Re, 0, 6408, 1, 1, 0, 6408, 5121, oe);
    return se;
  }
  const $ = {};
  $[3553] = ge(3553, 3553, 1), $[34067] = ge(34067, 34069, 6), r.setClear(0, 0, 0, 1), l.setClear(1), a.setClear(0), De(2929), l.setFunc(3), rt(!1), Rt(1), De(2884), et(0);
  function De(B) {
    u[B] !== !0 && (h.enable(B), u[B] = !0);
  }
  function ve(B) {
    u[B] !== !1 && (h.disable(B), u[B] = !1);
  }
  function xe(B, ae) {
    return m[B] !== ae ? (h.bindFramebuffer(B, ae), m[B] = ae, n && (B === 36009 && (m[36160] = ae), B === 36160 && (m[36009] = ae)), !0) : !1;
  }
  function ue(B, ae) {
    let Y = p, oe = !1;
    if (B)
      if (Y = g.get(ae), Y === void 0 && (Y = [], g.set(ae, Y)), B.isWebGLMultipleRenderTargets) {
        const se = B.texture;
        if (Y.length !== se.length || Y[0] !== 36064) {
          for (let Re = 0, Je = se.length; Re < Je; Re++)
            Y[Re] = 36064 + Re;
          Y.length = se.length, oe = !0;
        }
      } else
        Y[0] !== 36064 && (Y[0] = 36064, oe = !0);
    else
      Y[0] !== 1029 && (Y[0] = 1029, oe = !0);
    oe && (t.isWebGL2 ? h.drawBuffers(Y) : e.get("WEBGL_draw_buffers").drawBuffersWEBGL(Y));
  }
  function Oe(B) {
    return f !== B ? (h.useProgram(B), f = B, !0) : !1;
  }
  const Ee = {
    [100]: 32774,
    [101]: 32778,
    [102]: 32779
  };
  if (n)
    Ee[103] = 32775, Ee[104] = 32776;
  else {
    const B = e.get("EXT_blend_minmax");
    B !== null && (Ee[103] = B.MIN_EXT, Ee[104] = B.MAX_EXT);
  }
  const me = {
    [200]: 0,
    [201]: 1,
    [202]: 768,
    [204]: 770,
    [210]: 776,
    [208]: 774,
    [206]: 772,
    [203]: 769,
    [205]: 771,
    [209]: 775,
    [207]: 773
  };
  function et(B, ae, Y, oe, se, Re, Je, Ve) {
    if (B === 0) {
      v === !0 && (ve(3042), v = !1);
      return;
    }
    if (v === !1 && (De(3042), v = !0), B !== 5) {
      if (B !== _ || Ve !== A) {
        if ((w !== 100 || E !== 100) && (h.blendEquation(32774), w = 100, E = 100), Ve)
          switch (B) {
            case 1:
              h.blendFuncSeparate(1, 771, 1, 771);
              break;
            case 2:
              h.blendFunc(1, 1);
              break;
            case 3:
              h.blendFuncSeparate(0, 769, 0, 1);
              break;
            case 4:
              h.blendFuncSeparate(0, 768, 0, 770);
              break;
            default:
              console.error("THREE.WebGLState: Invalid blending: ", B);
              break;
          }
        else
          switch (B) {
            case 1:
              h.blendFuncSeparate(770, 771, 1, 771);
              break;
            case 2:
              h.blendFunc(770, 1);
              break;
            case 3:
              h.blendFuncSeparate(0, 769, 0, 1);
              break;
            case 4:
              h.blendFunc(0, 768);
              break;
            default:
              console.error("THREE.WebGLState: Invalid blending: ", B);
              break;
          }
        x = null, M = null, R = null, y = null, _ = B, A = Ve;
      }
      return;
    }
    se = se || ae, Re = Re || Y, Je = Je || oe, (ae !== w || se !== E) && (h.blendEquationSeparate(Ee[ae], Ee[se]), w = ae, E = se), (Y !== x || oe !== M || Re !== R || Je !== y) && (h.blendFuncSeparate(me[Y], me[oe], me[Re], me[Je]), x = Y, M = oe, R = Re, y = Je), _ = B, A = null;
  }
  function ut(B, ae) {
    B.side === 2 ? ve(2884) : De(2884);
    let Y = B.side === 1;
    ae && (Y = !Y), rt(Y), B.blending === 1 && B.transparent === !1 ? et(0) : et(B.blending, B.blendEquation, B.blendSrc, B.blendDst, B.blendEquationAlpha, B.blendSrcAlpha, B.blendDstAlpha, B.premultipliedAlpha), l.setFunc(B.depthFunc), l.setTest(B.depthTest), l.setMask(B.depthWrite), r.setMask(B.colorWrite);
    const oe = B.stencilWrite;
    a.setTest(oe), oe && (a.setMask(B.stencilWriteMask), a.setFunc(B.stencilFunc, B.stencilRef, B.stencilFuncMask), a.setOp(B.stencilFail, B.stencilZFail, B.stencilZPass)), Ne(B.polygonOffset, B.polygonOffsetFactor, B.polygonOffsetUnits), B.alphaToCoverage === !0 ? De(32926) : ve(32926);
  }
  function rt(B) {
    F !== B && (B ? h.frontFace(2304) : h.frontFace(2305), F = B);
  }
  function Rt(B) {
    B !== 0 ? (De(2884), B !== P && (B === 1 ? h.cullFace(1029) : B === 2 ? h.cullFace(1028) : h.cullFace(1032))) : ve(2884), P = B;
  }
  function tt(B) {
    B !== G && (D && h.lineWidth(B), G = B);
  }
  function Ne(B, ae, Y) {
    B ? (De(32823), (z !== ae || L !== Y) && (h.polygonOffset(ae, Y), z = ae, L = Y)) : ve(32823);
  }
  function Gt(B) {
    B ? De(3089) : ve(3089);
  }
  function Ft(B) {
    B === void 0 && (B = 33984 + I - 1), N !== B && (h.activeTexture(B), N = B);
  }
  function C(B, ae) {
    N === null && Ft();
    let Y = H[N];
    Y === void 0 && (Y = { type: void 0, texture: void 0 }, H[N] = Y), (Y.type !== B || Y.texture !== ae) && (h.bindTexture(B, ae || $[B]), Y.type = B, Y.texture = ae);
  }
  function S() {
    const B = H[N];
    B !== void 0 && B.type !== void 0 && (h.bindTexture(B.type, null), B.type = void 0, B.texture = void 0);
  }
  function Z() {
    try {
      h.compressedTexImage2D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function Q() {
    try {
      h.texSubImage2D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function te() {
    try {
      h.texSubImage3D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function re() {
    try {
      h.compressedTexSubImage2D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function ye() {
    try {
      h.texStorage2D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function j() {
    try {
      h.texStorage3D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function pe() {
    try {
      h.texImage2D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function he() {
    try {
      h.texImage3D.apply(h, arguments);
    } catch (B) {
      console.error("THREE.WebGLState:", B);
    }
  }
  function fe(B) {
    ee.equals(B) === !1 && (h.scissor(B.x, B.y, B.z, B.w), ee.copy(B));
  }
  function de(B) {
    ce.equals(B) === !1 && (h.viewport(B.x, B.y, B.z, B.w), ce.copy(B));
  }
  function we(B, ae) {
    let Y = d.get(ae);
    Y === void 0 && (Y = /* @__PURE__ */ new WeakMap(), d.set(ae, Y));
    let oe = Y.get(B);
    oe === void 0 && (oe = h.getUniformBlockIndex(ae, B.name), Y.set(B, oe));
  }
  function Ie(B, ae) {
    const oe = d.get(ae).get(B);
    c.get(B) !== oe && (h.uniformBlockBinding(ae, oe, B.__bindingPointIndex), c.set(B, oe));
  }
  function We() {
    h.disable(3042), h.disable(2884), h.disable(2929), h.disable(32823), h.disable(3089), h.disable(2960), h.disable(32926), h.blendEquation(32774), h.blendFunc(1, 0), h.blendFuncSeparate(1, 0, 1, 0), h.colorMask(!0, !0, !0, !0), h.clearColor(0, 0, 0, 0), h.depthMask(!0), h.depthFunc(513), h.clearDepth(1), h.stencilMask(4294967295), h.stencilFunc(519, 0, 4294967295), h.stencilOp(7680, 7680, 7680), h.clearStencil(0), h.cullFace(1029), h.frontFace(2305), h.polygonOffset(0, 0), h.activeTexture(33984), h.bindFramebuffer(36160, null), n === !0 && (h.bindFramebuffer(36009, null), h.bindFramebuffer(36008, null)), h.useProgram(null), h.lineWidth(1), h.scissor(0, 0, h.canvas.width, h.canvas.height), h.viewport(0, 0, h.canvas.width, h.canvas.height), u = {}, N = null, H = {}, m = {}, g = /* @__PURE__ */ new WeakMap(), p = [], f = null, v = !1, _ = null, w = null, x = null, M = null, E = null, R = null, y = null, A = !1, F = null, P = null, G = null, z = null, L = null, ee.set(0, 0, h.canvas.width, h.canvas.height), ce.set(0, 0, h.canvas.width, h.canvas.height), r.reset(), l.reset(), a.reset();
  }
  return {
    buffers: {
      color: r,
      depth: l,
      stencil: a
    },
    enable: De,
    disable: ve,
    bindFramebuffer: xe,
    drawBuffers: ue,
    useProgram: Oe,
    setBlending: et,
    setMaterial: ut,
    setFlipSided: rt,
    setCullFace: Rt,
    setLineWidth: tt,
    setPolygonOffset: Ne,
    setScissorTest: Gt,
    activeTexture: Ft,
    bindTexture: C,
    unbindTexture: S,
    compressedTexImage2D: Z,
    texImage2D: pe,
    texImage3D: he,
    updateUBOMapping: we,
    uniformBlockBinding: Ie,
    texStorage2D: ye,
    texStorage3D: j,
    texSubImage2D: Q,
    texSubImage3D: te,
    compressedTexSubImage2D: re,
    scissor: fe,
    viewport: de,
    reset: We
  };
}
function Au(h, e, t, n, i, s, o) {
  const r = i.isWebGL2, l = i.maxTextures, a = i.maxCubemapSize, c = i.maxTextureSize, d = i.maxSamples, u = e.has("WEBGL_multisampled_render_to_texture") ? e.get("WEBGL_multisampled_render_to_texture") : null, m = /OculusBrowser/g.test(navigator.userAgent), g = /* @__PURE__ */ new WeakMap();
  let p;
  const f = /* @__PURE__ */ new WeakMap();
  let v = !1;
  try {
    v = typeof OffscreenCanvas < "u" && new OffscreenCanvas(1, 1).getContext("2d") !== null;
  } catch {
  }
  function _(C, S) {
    return v ? new OffscreenCanvas(C, S) : qi("canvas");
  }
  function w(C, S, Z, Q) {
    let te = 1;
    if ((C.width > Q || C.height > Q) && (te = Q / Math.max(C.width, C.height)), te < 1 || S === !0)
      if (typeof HTMLImageElement < "u" && C instanceof HTMLImageElement || typeof HTMLCanvasElement < "u" && C instanceof HTMLCanvasElement || typeof ImageBitmap < "u" && C instanceof ImageBitmap) {
        const re = S ? Bs : Math.floor, ye = re(te * C.width), j = re(te * C.height);
        p === void 0 && (p = _(ye, j));
        const pe = Z ? _(ye, j) : p;
        return pe.width = ye, pe.height = j, pe.getContext("2d").drawImage(C, 0, 0, ye, j), console.warn("THREE.WebGLRenderer: Texture has been resized from (" + C.width + "x" + C.height + ") to (" + ye + "x" + j + ")."), pe;
      } else
        return "data" in C && console.warn("THREE.WebGLRenderer: Image in DataTexture is too big (" + C.width + "x" + C.height + ")."), C;
    return C;
  }
  function x(C) {
    return $s(C.width) && $s(C.height);
  }
  function M(C) {
    return r ? !1 : C.wrapS !== 1001 || C.wrapT !== 1001 || C.minFilter !== 1003 && C.minFilter !== 1006;
  }
  function E(C, S) {
    return C.generateMipmaps && S && C.minFilter !== 1003 && C.minFilter !== 1006;
  }
  function R(C) {
    h.generateMipmap(C);
  }
  function y(C, S, Z, Q, te = !1) {
    if (r === !1)
      return S;
    if (C !== null) {
      if (h[C] !== void 0)
        return h[C];
      console.warn("THREE.WebGLRenderer: Attempt to use non-existing WebGL internal format '" + C + "'");
    }
    let re = S;
    return S === 6403 && (Z === 5126 && (re = 33326), Z === 5131 && (re = 33325), Z === 5121 && (re = 33321)), S === 33319 && (Z === 5126 && (re = 33328), Z === 5131 && (re = 33327), Z === 5121 && (re = 33323)), S === 6408 && (Z === 5126 && (re = 34836), Z === 5131 && (re = 34842), Z === 5121 && (re = Q === 3001 && te === !1 ? 35907 : 32856), Z === 32819 && (re = 32854), Z === 32820 && (re = 32855)), (re === 33325 || re === 33326 || re === 33327 || re === 33328 || re === 34842 || re === 34836) && e.get("EXT_color_buffer_float"), re;
  }
  function A(C, S, Z) {
    return E(C, Z) === !0 || C.isFramebufferTexture && C.minFilter !== 1003 && C.minFilter !== 1006 ? Math.log2(Math.max(S.width, S.height)) + 1 : C.mipmaps !== void 0 && C.mipmaps.length > 0 ? C.mipmaps.length : C.isCompressedTexture && Array.isArray(C.image) ? S.mipmaps.length : 1;
  }
  function F(C) {
    return C === 1003 || C === 1004 || C === 1005 ? 9728 : 9729;
  }
  function P(C) {
    const S = C.target;
    S.removeEventListener("dispose", P), z(S), S.isVideoTexture && g.delete(S);
  }
  function G(C) {
    const S = C.target;
    S.removeEventListener("dispose", G), I(S);
  }
  function z(C) {
    const S = n.get(C);
    if (S.__webglInit === void 0)
      return;
    const Z = C.source, Q = f.get(Z);
    if (Q) {
      const te = Q[S.__cacheKey];
      te.usedTimes--, te.usedTimes === 0 && L(C), Object.keys(Q).length === 0 && f.delete(Z);
    }
    n.remove(C);
  }
  function L(C) {
    const S = n.get(C);
    h.deleteTexture(S.__webglTexture);
    const Z = C.source, Q = f.get(Z);
    delete Q[S.__cacheKey], o.memory.textures--;
  }
  function I(C) {
    const S = C.texture, Z = n.get(C), Q = n.get(S);
    if (Q.__webglTexture !== void 0 && (h.deleteTexture(Q.__webglTexture), o.memory.textures--), C.depthTexture && C.depthTexture.dispose(), C.isWebGLCubeRenderTarget)
      for (let te = 0; te < 6; te++)
        h.deleteFramebuffer(Z.__webglFramebuffer[te]), Z.__webglDepthbuffer && h.deleteRenderbuffer(Z.__webglDepthbuffer[te]);
    else {
      if (h.deleteFramebuffer(Z.__webglFramebuffer), Z.__webglDepthbuffer && h.deleteRenderbuffer(Z.__webglDepthbuffer), Z.__webglMultisampledFramebuffer && h.deleteFramebuffer(Z.__webglMultisampledFramebuffer), Z.__webglColorRenderbuffer)
        for (let te = 0; te < Z.__webglColorRenderbuffer.length; te++)
          Z.__webglColorRenderbuffer[te] && h.deleteRenderbuffer(Z.__webglColorRenderbuffer[te]);
      Z.__webglDepthRenderbuffer && h.deleteRenderbuffer(Z.__webglDepthRenderbuffer);
    }
    if (C.isWebGLMultipleRenderTargets)
      for (let te = 0, re = S.length; te < re; te++) {
        const ye = n.get(S[te]);
        ye.__webglTexture && (h.deleteTexture(ye.__webglTexture), o.memory.textures--), n.remove(S[te]);
      }
    n.remove(S), n.remove(C);
  }
  let D = 0;
  function q() {
    D = 0;
  }
  function k() {
    const C = D;
    return C >= l && console.warn("THREE.WebGLTextures: Trying to use " + C + " texture units while this GPU supports only " + l), D += 1, C;
  }
  function N(C) {
    const S = [];
    return S.push(C.wrapS), S.push(C.wrapT), S.push(C.magFilter), S.push(C.minFilter), S.push(C.anisotropy), S.push(C.internalFormat), S.push(C.format), S.push(C.type), S.push(C.generateMipmaps), S.push(C.premultiplyAlpha), S.push(C.flipY), S.push(C.unpackAlignment), S.push(C.encoding), S.join();
  }
  function H(C, S) {
    const Z = n.get(C);
    if (C.isVideoTexture && Gt(C), C.isRenderTargetTexture === !1 && C.version > 0 && Z.__version !== C.version) {
      const Q = C.image;
      if (Q === null)
        console.warn("THREE.WebGLRenderer: Texture marked for update but no image data found.");
      else if (Q.complete === !1)
        console.warn("THREE.WebGLRenderer: Texture marked for update but image is incomplete");
      else {
        ve(Z, C, S);
        return;
      }
    }
    t.activeTexture(33984 + S), t.bindTexture(3553, Z.__webglTexture);
  }
  function J(C, S) {
    const Z = n.get(C);
    if (C.version > 0 && Z.__version !== C.version) {
      ve(Z, C, S);
      return;
    }
    t.activeTexture(33984 + S), t.bindTexture(35866, Z.__webglTexture);
  }
  function V(C, S) {
    const Z = n.get(C);
    if (C.version > 0 && Z.__version !== C.version) {
      ve(Z, C, S);
      return;
    }
    t.activeTexture(33984 + S), t.bindTexture(32879, Z.__webglTexture);
  }
  function ee(C, S) {
    const Z = n.get(C);
    if (C.version > 0 && Z.__version !== C.version) {
      xe(Z, C, S);
      return;
    }
    t.activeTexture(33984 + S), t.bindTexture(34067, Z.__webglTexture);
  }
  const ce = {
    [1e3]: 10497,
    [1001]: 33071,
    [1002]: 33648
  }, ge = {
    [1003]: 9728,
    [1004]: 9984,
    [1005]: 9986,
    [1006]: 9729,
    [1007]: 9985,
    [1008]: 9987
  };
  function $(C, S, Z) {
    if (Z ? (h.texParameteri(C, 10242, ce[S.wrapS]), h.texParameteri(C, 10243, ce[S.wrapT]), (C === 32879 || C === 35866) && h.texParameteri(C, 32882, ce[S.wrapR]), h.texParameteri(C, 10240, ge[S.magFilter]), h.texParameteri(C, 10241, ge[S.minFilter])) : (h.texParameteri(C, 10242, 33071), h.texParameteri(C, 10243, 33071), (C === 32879 || C === 35866) && h.texParameteri(C, 32882, 33071), (S.wrapS !== 1001 || S.wrapT !== 1001) && console.warn("THREE.WebGLRenderer: Texture is not power of two. Texture.wrapS and Texture.wrapT should be set to THREE.ClampToEdgeWrapping."), h.texParameteri(C, 10240, F(S.magFilter)), h.texParameteri(C, 10241, F(S.minFilter)), S.minFilter !== 1003 && S.minFilter !== 1006 && console.warn("THREE.WebGLRenderer: Texture is not power of two. Texture.minFilter should be set to THREE.NearestFilter or THREE.LinearFilter.")), e.has("EXT_texture_filter_anisotropic") === !0) {
      const Q = e.get("EXT_texture_filter_anisotropic");
      if (S.type === 1015 && e.has("OES_texture_float_linear") === !1 || r === !1 && S.type === 1016 && e.has("OES_texture_half_float_linear") === !1)
        return;
      (S.anisotropy > 1 || n.get(S).__currentAnisotropy) && (h.texParameterf(C, Q.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(S.anisotropy, i.getMaxAnisotropy())), n.get(S).__currentAnisotropy = S.anisotropy);
    }
  }
  function De(C, S) {
    let Z = !1;
    C.__webglInit === void 0 && (C.__webglInit = !0, S.addEventListener("dispose", P));
    const Q = S.source;
    let te = f.get(Q);
    te === void 0 && (te = {}, f.set(Q, te));
    const re = N(S);
    if (re !== C.__cacheKey) {
      te[re] === void 0 && (te[re] = {
        texture: h.createTexture(),
        usedTimes: 0
      }, o.memory.textures++, Z = !0), te[re].usedTimes++;
      const ye = te[C.__cacheKey];
      ye !== void 0 && (te[C.__cacheKey].usedTimes--, ye.usedTimes === 0 && L(S)), C.__cacheKey = re, C.__webglTexture = te[re].texture;
    }
    return Z;
  }
  function ve(C, S, Z) {
    let Q = 3553;
    S.isDataArrayTexture && (Q = 35866), S.isData3DTexture && (Q = 32879);
    const te = De(C, S), re = S.source;
    if (t.activeTexture(33984 + Z), t.bindTexture(Q, C.__webglTexture), re.version !== re.__currentVersion || te === !0) {
      h.pixelStorei(37440, S.flipY), h.pixelStorei(37441, S.premultiplyAlpha), h.pixelStorei(3317, S.unpackAlignment), h.pixelStorei(37443, 0);
      const ye = M(S) && x(S.image) === !1;
      let j = w(S.image, ye, !1, c);
      j = Ft(S, j);
      const pe = x(j) || r, he = s.convert(S.format, S.encoding);
      let fe = s.convert(S.type), de = y(S.internalFormat, he, fe, S.encoding, S.isVideoTexture);
      $(Q, S, pe);
      let we;
      const Ie = S.mipmaps, We = r && S.isVideoTexture !== !0, B = re.__currentVersion === void 0 || te === !0, ae = A(S, j, pe);
      if (S.isDepthTexture)
        de = 6402, r ? S.type === 1015 ? de = 36012 : S.type === 1014 ? de = 33190 : S.type === 1020 ? de = 35056 : de = 33189 : S.type === 1015 && console.error("WebGLRenderer: Floating point depth texture requires WebGL2."), S.format === 1026 && de === 6402 && S.type !== 1012 && S.type !== 1014 && (console.warn("THREE.WebGLRenderer: Use UnsignedShortType or UnsignedIntType for DepthFormat DepthTexture."), S.type = 1014, fe = s.convert(S.type)), S.format === 1027 && de === 6402 && (de = 34041, S.type !== 1020 && (console.warn("THREE.WebGLRenderer: Use UnsignedInt248Type for DepthStencilFormat DepthTexture."), S.type = 1020, fe = s.convert(S.type))), B && (We ? t.texStorage2D(3553, 1, de, j.width, j.height) : t.texImage2D(3553, 0, de, j.width, j.height, 0, he, fe, null));
      else if (S.isDataTexture)
        if (Ie.length > 0 && pe) {
          We && B && t.texStorage2D(3553, ae, de, Ie[0].width, Ie[0].height);
          for (let Y = 0, oe = Ie.length; Y < oe; Y++)
            we = Ie[Y], We ? t.texSubImage2D(3553, Y, 0, 0, we.width, we.height, he, fe, we.data) : t.texImage2D(3553, Y, de, we.width, we.height, 0, he, fe, we.data);
          S.generateMipmaps = !1;
        } else
          We ? (B && t.texStorage2D(3553, ae, de, j.width, j.height), t.texSubImage2D(3553, 0, 0, 0, j.width, j.height, he, fe, j.data)) : t.texImage2D(3553, 0, de, j.width, j.height, 0, he, fe, j.data);
      else if (S.isCompressedTexture) {
        We && B && t.texStorage2D(3553, ae, de, Ie[0].width, Ie[0].height);
        for (let Y = 0, oe = Ie.length; Y < oe; Y++)
          we = Ie[Y], S.format !== 1023 ? he !== null ? We ? t.compressedTexSubImage2D(3553, Y, 0, 0, we.width, we.height, he, we.data) : t.compressedTexImage2D(3553, Y, de, we.width, we.height, 0, we.data) : console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()") : We ? t.texSubImage2D(3553, Y, 0, 0, we.width, we.height, he, fe, we.data) : t.texImage2D(3553, Y, de, we.width, we.height, 0, he, fe, we.data);
      } else if (S.isDataArrayTexture)
        We ? (B && t.texStorage3D(35866, ae, de, j.width, j.height, j.depth), t.texSubImage3D(35866, 0, 0, 0, 0, j.width, j.height, j.depth, he, fe, j.data)) : t.texImage3D(35866, 0, de, j.width, j.height, j.depth, 0, he, fe, j.data);
      else if (S.isData3DTexture)
        We ? (B && t.texStorage3D(32879, ae, de, j.width, j.height, j.depth), t.texSubImage3D(32879, 0, 0, 0, 0, j.width, j.height, j.depth, he, fe, j.data)) : t.texImage3D(32879, 0, de, j.width, j.height, j.depth, 0, he, fe, j.data);
      else if (S.isFramebufferTexture) {
        if (B)
          if (We)
            t.texStorage2D(3553, ae, de, j.width, j.height);
          else {
            let Y = j.width, oe = j.height;
            for (let se = 0; se < ae; se++)
              t.texImage2D(3553, se, de, Y, oe, 0, he, fe, null), Y >>= 1, oe >>= 1;
          }
      } else if (Ie.length > 0 && pe) {
        We && B && t.texStorage2D(3553, ae, de, Ie[0].width, Ie[0].height);
        for (let Y = 0, oe = Ie.length; Y < oe; Y++)
          we = Ie[Y], We ? t.texSubImage2D(3553, Y, 0, 0, he, fe, we) : t.texImage2D(3553, Y, de, he, fe, we);
        S.generateMipmaps = !1;
      } else
        We ? (B && t.texStorage2D(3553, ae, de, j.width, j.height), t.texSubImage2D(3553, 0, 0, 0, he, fe, j)) : t.texImage2D(3553, 0, de, he, fe, j);
      E(S, pe) && R(Q), re.__currentVersion = re.version, S.onUpdate && S.onUpdate(S);
    }
    C.__version = S.version;
  }
  function xe(C, S, Z) {
    if (S.image.length !== 6)
      return;
    const Q = De(C, S), te = S.source;
    if (t.activeTexture(33984 + Z), t.bindTexture(34067, C.__webglTexture), te.version !== te.__currentVersion || Q === !0) {
      h.pixelStorei(37440, S.flipY), h.pixelStorei(37441, S.premultiplyAlpha), h.pixelStorei(3317, S.unpackAlignment), h.pixelStorei(37443, 0);
      const re = S.isCompressedTexture || S.image[0].isCompressedTexture, ye = S.image[0] && S.image[0].isDataTexture, j = [];
      for (let Y = 0; Y < 6; Y++)
        !re && !ye ? j[Y] = w(S.image[Y], !1, !0, a) : j[Y] = ye ? S.image[Y].image : S.image[Y], j[Y] = Ft(S, j[Y]);
      const pe = j[0], he = x(pe) || r, fe = s.convert(S.format, S.encoding), de = s.convert(S.type), we = y(S.internalFormat, fe, de, S.encoding), Ie = r && S.isVideoTexture !== !0, We = te.__currentVersion === void 0 || Q === !0;
      let B = A(S, pe, he);
      $(34067, S, he);
      let ae;
      if (re) {
        Ie && We && t.texStorage2D(34067, B, we, pe.width, pe.height);
        for (let Y = 0; Y < 6; Y++) {
          ae = j[Y].mipmaps;
          for (let oe = 0; oe < ae.length; oe++) {
            const se = ae[oe];
            S.format !== 1023 ? fe !== null ? Ie ? t.compressedTexSubImage2D(34069 + Y, oe, 0, 0, se.width, se.height, fe, se.data) : t.compressedTexImage2D(34069 + Y, oe, we, se.width, se.height, 0, se.data) : console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()") : Ie ? t.texSubImage2D(34069 + Y, oe, 0, 0, se.width, se.height, fe, de, se.data) : t.texImage2D(34069 + Y, oe, we, se.width, se.height, 0, fe, de, se.data);
          }
        }
      } else {
        ae = S.mipmaps, Ie && We && (ae.length > 0 && B++, t.texStorage2D(34067, B, we, j[0].width, j[0].height));
        for (let Y = 0; Y < 6; Y++)
          if (ye) {
            Ie ? t.texSubImage2D(34069 + Y, 0, 0, 0, j[Y].width, j[Y].height, fe, de, j[Y].data) : t.texImage2D(34069 + Y, 0, we, j[Y].width, j[Y].height, 0, fe, de, j[Y].data);
            for (let oe = 0; oe < ae.length; oe++) {
              const Re = ae[oe].image[Y].image;
              Ie ? t.texSubImage2D(34069 + Y, oe + 1, 0, 0, Re.width, Re.height, fe, de, Re.data) : t.texImage2D(34069 + Y, oe + 1, we, Re.width, Re.height, 0, fe, de, Re.data);
            }
          } else {
            Ie ? t.texSubImage2D(34069 + Y, 0, 0, 0, fe, de, j[Y]) : t.texImage2D(34069 + Y, 0, we, fe, de, j[Y]);
            for (let oe = 0; oe < ae.length; oe++) {
              const se = ae[oe];
              Ie ? t.texSubImage2D(34069 + Y, oe + 1, 0, 0, fe, de, se.image[Y]) : t.texImage2D(34069 + Y, oe + 1, we, fe, de, se.image[Y]);
            }
          }
      }
      E(S, he) && R(34067), te.__currentVersion = te.version, S.onUpdate && S.onUpdate(S);
    }
    C.__version = S.version;
  }
  function ue(C, S, Z, Q, te) {
    const re = s.convert(Z.format, Z.encoding), ye = s.convert(Z.type), j = y(Z.internalFormat, re, ye, Z.encoding);
    n.get(S).__hasExternalTextures || (te === 32879 || te === 35866 ? t.texImage3D(te, 0, j, S.width, S.height, S.depth, 0, re, ye, null) : t.texImage2D(te, 0, j, S.width, S.height, 0, re, ye, null)), t.bindFramebuffer(36160, C), Ne(S) ? u.framebufferTexture2DMultisampleEXT(36160, Q, te, n.get(Z).__webglTexture, 0, tt(S)) : h.framebufferTexture2D(36160, Q, te, n.get(Z).__webglTexture, 0), t.bindFramebuffer(36160, null);
  }
  function Oe(C, S, Z) {
    if (h.bindRenderbuffer(36161, C), S.depthBuffer && !S.stencilBuffer) {
      let Q = 33189;
      if (Z || Ne(S)) {
        const te = S.depthTexture;
        te && te.isDepthTexture && (te.type === 1015 ? Q = 36012 : te.type === 1014 && (Q = 33190));
        const re = tt(S);
        Ne(S) ? u.renderbufferStorageMultisampleEXT(36161, re, Q, S.width, S.height) : h.renderbufferStorageMultisample(36161, re, Q, S.width, S.height);
      } else
        h.renderbufferStorage(36161, Q, S.width, S.height);
      h.framebufferRenderbuffer(36160, 36096, 36161, C);
    } else if (S.depthBuffer && S.stencilBuffer) {
      const Q = tt(S);
      Z && Ne(S) === !1 ? h.renderbufferStorageMultisample(36161, Q, 35056, S.width, S.height) : Ne(S) ? u.renderbufferStorageMultisampleEXT(36161, Q, 35056, S.width, S.height) : h.renderbufferStorage(36161, 34041, S.width, S.height), h.framebufferRenderbuffer(36160, 33306, 36161, C);
    } else {
      const Q = S.isWebGLMultipleRenderTargets === !0 ? S.texture : [S.texture];
      for (let te = 0; te < Q.length; te++) {
        const re = Q[te], ye = s.convert(re.format, re.encoding), j = s.convert(re.type), pe = y(re.internalFormat, ye, j, re.encoding), he = tt(S);
        Z && Ne(S) === !1 ? h.renderbufferStorageMultisample(36161, he, pe, S.width, S.height) : Ne(S) ? u.renderbufferStorageMultisampleEXT(36161, he, pe, S.width, S.height) : h.renderbufferStorage(36161, pe, S.width, S.height);
      }
    }
    h.bindRenderbuffer(36161, null);
  }
  function Ee(C, S) {
    if (S && S.isWebGLCubeRenderTarget)
      throw new Error("Depth Texture with cube render targets is not supported");
    if (t.bindFramebuffer(36160, C), !(S.depthTexture && S.depthTexture.isDepthTexture))
      throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");
    (!n.get(S.depthTexture).__webglTexture || S.depthTexture.image.width !== S.width || S.depthTexture.image.height !== S.height) && (S.depthTexture.image.width = S.width, S.depthTexture.image.height = S.height, S.depthTexture.needsUpdate = !0), H(S.depthTexture, 0);
    const Q = n.get(S.depthTexture).__webglTexture, te = tt(S);
    if (S.depthTexture.format === 1026)
      Ne(S) ? u.framebufferTexture2DMultisampleEXT(36160, 36096, 3553, Q, 0, te) : h.framebufferTexture2D(36160, 36096, 3553, Q, 0);
    else if (S.depthTexture.format === 1027)
      Ne(S) ? u.framebufferTexture2DMultisampleEXT(36160, 33306, 3553, Q, 0, te) : h.framebufferTexture2D(36160, 33306, 3553, Q, 0);
    else
      throw new Error("Unknown depthTexture format");
  }
  function me(C) {
    const S = n.get(C), Z = C.isWebGLCubeRenderTarget === !0;
    if (C.depthTexture && !S.__autoAllocateDepthBuffer) {
      if (Z)
        throw new Error("target.depthTexture not supported in Cube render targets");
      Ee(S.__webglFramebuffer, C);
    } else if (Z) {
      S.__webglDepthbuffer = [];
      for (let Q = 0; Q < 6; Q++)
        t.bindFramebuffer(36160, S.__webglFramebuffer[Q]), S.__webglDepthbuffer[Q] = h.createRenderbuffer(), Oe(S.__webglDepthbuffer[Q], C, !1);
    } else
      t.bindFramebuffer(36160, S.__webglFramebuffer), S.__webglDepthbuffer = h.createRenderbuffer(), Oe(S.__webglDepthbuffer, C, !1);
    t.bindFramebuffer(36160, null);
  }
  function et(C, S, Z) {
    const Q = n.get(C);
    S !== void 0 && ue(Q.__webglFramebuffer, C, C.texture, 36064, 3553), Z !== void 0 && me(C);
  }
  function ut(C) {
    const S = C.texture, Z = n.get(C), Q = n.get(S);
    C.addEventListener("dispose", G), C.isWebGLMultipleRenderTargets !== !0 && (Q.__webglTexture === void 0 && (Q.__webglTexture = h.createTexture()), Q.__version = S.version, o.memory.textures++);
    const te = C.isWebGLCubeRenderTarget === !0, re = C.isWebGLMultipleRenderTargets === !0, ye = x(C) || r;
    if (te) {
      Z.__webglFramebuffer = [];
      for (let j = 0; j < 6; j++)
        Z.__webglFramebuffer[j] = h.createFramebuffer();
    } else {
      if (Z.__webglFramebuffer = h.createFramebuffer(), re)
        if (i.drawBuffers) {
          const j = C.texture;
          for (let pe = 0, he = j.length; pe < he; pe++) {
            const fe = n.get(j[pe]);
            fe.__webglTexture === void 0 && (fe.__webglTexture = h.createTexture(), o.memory.textures++);
          }
        } else
          console.warn("THREE.WebGLRenderer: WebGLMultipleRenderTargets can only be used with WebGL2 or WEBGL_draw_buffers extension.");
      if (r && C.samples > 0 && Ne(C) === !1) {
        const j = re ? S : [S];
        Z.__webglMultisampledFramebuffer = h.createFramebuffer(), Z.__webglColorRenderbuffer = [], t.bindFramebuffer(36160, Z.__webglMultisampledFramebuffer);
        for (let pe = 0; pe < j.length; pe++) {
          const he = j[pe];
          Z.__webglColorRenderbuffer[pe] = h.createRenderbuffer(), h.bindRenderbuffer(36161, Z.__webglColorRenderbuffer[pe]);
          const fe = s.convert(he.format, he.encoding), de = s.convert(he.type), we = y(he.internalFormat, fe, de, he.encoding), Ie = tt(C);
          h.renderbufferStorageMultisample(36161, Ie, we, C.width, C.height), h.framebufferRenderbuffer(36160, 36064 + pe, 36161, Z.__webglColorRenderbuffer[pe]);
        }
        h.bindRenderbuffer(36161, null), C.depthBuffer && (Z.__webglDepthRenderbuffer = h.createRenderbuffer(), Oe(Z.__webglDepthRenderbuffer, C, !0)), t.bindFramebuffer(36160, null);
      }
    }
    if (te) {
      t.bindTexture(34067, Q.__webglTexture), $(34067, S, ye);
      for (let j = 0; j < 6; j++)
        ue(Z.__webglFramebuffer[j], C, S, 36064, 34069 + j);
      E(S, ye) && R(34067), t.unbindTexture();
    } else if (re) {
      const j = C.texture;
      for (let pe = 0, he = j.length; pe < he; pe++) {
        const fe = j[pe], de = n.get(fe);
        t.bindTexture(3553, de.__webglTexture), $(3553, fe, ye), ue(Z.__webglFramebuffer, C, fe, 36064 + pe, 3553), E(fe, ye) && R(3553);
      }
      t.unbindTexture();
    } else {
      let j = 3553;
      (C.isWebGL3DRenderTarget || C.isWebGLArrayRenderTarget) && (r ? j = C.isWebGL3DRenderTarget ? 32879 : 35866 : console.error("THREE.WebGLTextures: THREE.Data3DTexture and THREE.DataArrayTexture only supported with WebGL2.")), t.bindTexture(j, Q.__webglTexture), $(j, S, ye), ue(Z.__webglFramebuffer, C, S, 36064, j), E(S, ye) && R(j), t.unbindTexture();
    }
    C.depthBuffer && me(C);
  }
  function rt(C) {
    const S = x(C) || r, Z = C.isWebGLMultipleRenderTargets === !0 ? C.texture : [C.texture];
    for (let Q = 0, te = Z.length; Q < te; Q++) {
      const re = Z[Q];
      if (E(re, S)) {
        const ye = C.isWebGLCubeRenderTarget ? 34067 : 3553, j = n.get(re).__webglTexture;
        t.bindTexture(ye, j), R(ye), t.unbindTexture();
      }
    }
  }
  function Rt(C) {
    if (r && C.samples > 0 && Ne(C) === !1) {
      const S = C.isWebGLMultipleRenderTargets ? C.texture : [C.texture], Z = C.width, Q = C.height;
      let te = 16384;
      const re = [], ye = C.stencilBuffer ? 33306 : 36096, j = n.get(C), pe = C.isWebGLMultipleRenderTargets === !0;
      if (pe)
        for (let he = 0; he < S.length; he++)
          t.bindFramebuffer(36160, j.__webglMultisampledFramebuffer), h.framebufferRenderbuffer(36160, 36064 + he, 36161, null), t.bindFramebuffer(36160, j.__webglFramebuffer), h.framebufferTexture2D(36009, 36064 + he, 3553, null, 0);
      t.bindFramebuffer(36008, j.__webglMultisampledFramebuffer), t.bindFramebuffer(36009, j.__webglFramebuffer);
      for (let he = 0; he < S.length; he++) {
        re.push(36064 + he), C.depthBuffer && re.push(ye);
        const fe = j.__ignoreDepthValues !== void 0 ? j.__ignoreDepthValues : !1;
        if (fe === !1 && (C.depthBuffer && (te |= 256), C.stencilBuffer && (te |= 1024)), pe && h.framebufferRenderbuffer(36008, 36064, 36161, j.__webglColorRenderbuffer[he]), fe === !0 && (h.invalidateFramebuffer(36008, [ye]), h.invalidateFramebuffer(36009, [ye])), pe) {
          const de = n.get(S[he]).__webglTexture;
          h.framebufferTexture2D(36009, 36064, 3553, de, 0);
        }
        h.blitFramebuffer(0, 0, Z, Q, 0, 0, Z, Q, te, 9728), m && h.invalidateFramebuffer(36008, re);
      }
      if (t.bindFramebuffer(36008, null), t.bindFramebuffer(36009, null), pe)
        for (let he = 0; he < S.length; he++) {
          t.bindFramebuffer(36160, j.__webglMultisampledFramebuffer), h.framebufferRenderbuffer(36160, 36064 + he, 36161, j.__webglColorRenderbuffer[he]);
          const fe = n.get(S[he]).__webglTexture;
          t.bindFramebuffer(36160, j.__webglFramebuffer), h.framebufferTexture2D(36009, 36064 + he, 3553, fe, 0);
        }
      t.bindFramebuffer(36009, j.__webglMultisampledFramebuffer);
    }
  }
  function tt(C) {
    return Math.min(d, C.samples);
  }
  function Ne(C) {
    const S = n.get(C);
    return r && C.samples > 0 && e.has("WEBGL_multisampled_render_to_texture") === !0 && S.__useRenderToTexture !== !1;
  }
  function Gt(C) {
    const S = o.render.frame;
    g.get(C) !== S && (g.set(C, S), C.update());
  }
  function Ft(C, S) {
    const Z = C.encoding, Q = C.format, te = C.type;
    return C.isCompressedTexture === !0 || C.isVideoTexture === !0 || C.format === 1035 || Z !== 3e3 && (Z === 3001 ? r === !1 ? e.has("EXT_sRGB") === !0 && Q === 1023 ? (C.format = 1035, C.minFilter = 1006, C.generateMipmaps = !1) : S = io.sRGBToLinear(S) : (Q !== 1023 || te !== 1009) && console.warn("THREE.WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType.") : console.error("THREE.WebGLTextures: Unsupported texture encoding:", Z)), S;
  }
  this.allocateTextureUnit = k, this.resetTextureUnits = q, this.setTexture2D = H, this.setTexture2DArray = J, this.setTexture3D = V, this.setTextureCube = ee, this.rebindTextures = et, this.setupRenderTarget = ut, this.updateRenderTargetMipmap = rt, this.updateMultisampleRenderTarget = Rt, this.setupDepthRenderbuffer = me, this.setupFrameBufferTexture = ue, this.useMultisampledRTT = Ne;
}
function Cu(h, e, t) {
  const n = t.isWebGL2;
  function i(s, o = null) {
    let r;
    if (s === 1009)
      return 5121;
    if (s === 1017)
      return 32819;
    if (s === 1018)
      return 32820;
    if (s === 1010)
      return 5120;
    if (s === 1011)
      return 5122;
    if (s === 1012)
      return 5123;
    if (s === 1013)
      return 5124;
    if (s === 1014)
      return 5125;
    if (s === 1015)
      return 5126;
    if (s === 1016)
      return n ? 5131 : (r = e.get("OES_texture_half_float"), r !== null ? r.HALF_FLOAT_OES : null);
    if (s === 1021)
      return 6406;
    if (s === 1023)
      return 6408;
    if (s === 1024)
      return 6409;
    if (s === 1025)
      return 6410;
    if (s === 1026)
      return 6402;
    if (s === 1027)
      return 34041;
    if (s === 1028)
      return 6403;
    if (s === 1022)
      return console.warn("THREE.WebGLRenderer: THREE.RGBFormat has been removed. Use THREE.RGBAFormat instead. https://github.com/mrdoob/three.js/pull/23228"), 6408;
    if (s === 1035)
      return r = e.get("EXT_sRGB"), r !== null ? r.SRGB_ALPHA_EXT : null;
    if (s === 1029)
      return 36244;
    if (s === 1030)
      return 33319;
    if (s === 1031)
      return 33320;
    if (s === 1033)
      return 36249;
    if (s === 33776 || s === 33777 || s === 33778 || s === 33779)
      if (o === 3001)
        if (r = e.get("WEBGL_compressed_texture_s3tc_srgb"), r !== null) {
          if (s === 33776)
            return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;
          if (s === 33777)
            return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;
          if (s === 33778)
            return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;
          if (s === 33779)
            return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT;
        } else
          return null;
      else if (r = e.get("WEBGL_compressed_texture_s3tc"), r !== null) {
        if (s === 33776)
          return r.COMPRESSED_RGB_S3TC_DXT1_EXT;
        if (s === 33777)
          return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;
        if (s === 33778)
          return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;
        if (s === 33779)
          return r.COMPRESSED_RGBA_S3TC_DXT5_EXT;
      } else
        return null;
    if (s === 35840 || s === 35841 || s === 35842 || s === 35843)
      if (r = e.get("WEBGL_compressed_texture_pvrtc"), r !== null) {
        if (s === 35840)
          return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;
        if (s === 35841)
          return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;
        if (s === 35842)
          return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;
        if (s === 35843)
          return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG;
      } else
        return null;
    if (s === 36196)
      return r = e.get("WEBGL_compressed_texture_etc1"), r !== null ? r.COMPRESSED_RGB_ETC1_WEBGL : null;
    if (s === 37492 || s === 37496)
      if (r = e.get("WEBGL_compressed_texture_etc"), r !== null) {
        if (s === 37492)
          return o === 3001 ? r.COMPRESSED_SRGB8_ETC2 : r.COMPRESSED_RGB8_ETC2;
        if (s === 37496)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC : r.COMPRESSED_RGBA8_ETC2_EAC;
      } else
        return null;
    if (s === 37808 || s === 37809 || s === 37810 || s === 37811 || s === 37812 || s === 37813 || s === 37814 || s === 37815 || s === 37816 || s === 37817 || s === 37818 || s === 37819 || s === 37820 || s === 37821)
      if (r = e.get("WEBGL_compressed_texture_astc"), r !== null) {
        if (s === 37808)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR : r.COMPRESSED_RGBA_ASTC_4x4_KHR;
        if (s === 37809)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR : r.COMPRESSED_RGBA_ASTC_5x4_KHR;
        if (s === 37810)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR : r.COMPRESSED_RGBA_ASTC_5x5_KHR;
        if (s === 37811)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR : r.COMPRESSED_RGBA_ASTC_6x5_KHR;
        if (s === 37812)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR : r.COMPRESSED_RGBA_ASTC_6x6_KHR;
        if (s === 37813)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR : r.COMPRESSED_RGBA_ASTC_8x5_KHR;
        if (s === 37814)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR : r.COMPRESSED_RGBA_ASTC_8x6_KHR;
        if (s === 37815)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR : r.COMPRESSED_RGBA_ASTC_8x8_KHR;
        if (s === 37816)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR : r.COMPRESSED_RGBA_ASTC_10x5_KHR;
        if (s === 37817)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR : r.COMPRESSED_RGBA_ASTC_10x6_KHR;
        if (s === 37818)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR : r.COMPRESSED_RGBA_ASTC_10x8_KHR;
        if (s === 37819)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR : r.COMPRESSED_RGBA_ASTC_10x10_KHR;
        if (s === 37820)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR : r.COMPRESSED_RGBA_ASTC_12x10_KHR;
        if (s === 37821)
          return o === 3001 ? r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR : r.COMPRESSED_RGBA_ASTC_12x12_KHR;
      } else
        return null;
    if (s === 36492)
      if (r = e.get("EXT_texture_compression_bptc"), r !== null) {
        if (s === 36492)
          return o === 3001 ? r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT : r.COMPRESSED_RGBA_BPTC_UNORM_EXT;
      } else
        return null;
    return s === 1020 ? n ? 34042 : (r = e.get("WEBGL_depth_texture"), r !== null ? r.UNSIGNED_INT_24_8_WEBGL : null) : h[s] !== void 0 ? h[s] : null;
  }
  return { convert: i };
}
class Lu extends gt {
  constructor(e = []) {
    super(), this.isArrayCamera = !0, this.cameras = e;
  }
}
class Bi extends at {
  constructor() {
    super(), this.isGroup = !0, this.type = "Group";
  }
}
const Ru = { type: "move" };
class Ts {
  constructor() {
    this._targetRay = null, this._grip = null, this._hand = null;
  }
  getHandSpace() {
    return this._hand === null && (this._hand = new Bi(), this._hand.matrixAutoUpdate = !1, this._hand.visible = !1, this._hand.joints = {}, this._hand.inputState = { pinching: !1 }), this._hand;
  }
  getTargetRaySpace() {
    return this._targetRay === null && (this._targetRay = new Bi(), this._targetRay.matrixAutoUpdate = !1, this._targetRay.visible = !1, this._targetRay.hasLinearVelocity = !1, this._targetRay.linearVelocity = new O(), this._targetRay.hasAngularVelocity = !1, this._targetRay.angularVelocity = new O()), this._targetRay;
  }
  getGripSpace() {
    return this._grip === null && (this._grip = new Bi(), this._grip.matrixAutoUpdate = !1, this._grip.visible = !1, this._grip.hasLinearVelocity = !1, this._grip.linearVelocity = new O(), this._grip.hasAngularVelocity = !1, this._grip.angularVelocity = new O()), this._grip;
  }
  dispatchEvent(e) {
    return this._targetRay !== null && this._targetRay.dispatchEvent(e), this._grip !== null && this._grip.dispatchEvent(e), this._hand !== null && this._hand.dispatchEvent(e), this;
  }
  disconnect(e) {
    return this.dispatchEvent({ type: "disconnected", data: e }), this._targetRay !== null && (this._targetRay.visible = !1), this._grip !== null && (this._grip.visible = !1), this._hand !== null && (this._hand.visible = !1), this;
  }
  update(e, t, n) {
    let i = null, s = null, o = null;
    const r = this._targetRay, l = this._grip, a = this._hand;
    if (e && t.session.visibilityState !== "visible-blurred") {
      if (a && e.hand) {
        o = !0;
        for (const p of e.hand.values()) {
          const f = t.getJointPose(p, n);
          if (a.joints[p.jointName] === void 0) {
            const _ = new Bi();
            _.matrixAutoUpdate = !1, _.visible = !1, a.joints[p.jointName] = _, a.add(_);
          }
          const v = a.joints[p.jointName];
          f !== null && (v.matrix.fromArray(f.transform.matrix), v.matrix.decompose(v.position, v.rotation, v.scale), v.jointRadius = f.radius), v.visible = f !== null;
        }
        const c = a.joints["index-finger-tip"], d = a.joints["thumb-tip"], u = c.position.distanceTo(d.position), m = 0.02, g = 5e-3;
        a.inputState.pinching && u > m + g ? (a.inputState.pinching = !1, this.dispatchEvent({
          type: "pinchend",
          handedness: e.handedness,
          target: this
        })) : !a.inputState.pinching && u <= m - g && (a.inputState.pinching = !0, this.dispatchEvent({
          type: "pinchstart",
          handedness: e.handedness,
          target: this
        }));
      } else
        l !== null && e.gripSpace && (s = t.getPose(e.gripSpace, n), s !== null && (l.matrix.fromArray(s.transform.matrix), l.matrix.decompose(l.position, l.rotation, l.scale), s.linearVelocity ? (l.hasLinearVelocity = !0, l.linearVelocity.copy(s.linearVelocity)) : l.hasLinearVelocity = !1, s.angularVelocity ? (l.hasAngularVelocity = !0, l.angularVelocity.copy(s.angularVelocity)) : l.hasAngularVelocity = !1));
      r !== null && (i = t.getPose(e.targetRaySpace, n), i === null && s !== null && (i = s), i !== null && (r.matrix.fromArray(i.transform.matrix), r.matrix.decompose(r.position, r.rotation, r.scale), i.linearVelocity ? (r.hasLinearVelocity = !0, r.linearVelocity.copy(i.linearVelocity)) : r.hasLinearVelocity = !1, i.angularVelocity ? (r.hasAngularVelocity = !0, r.angularVelocity.copy(i.angularVelocity)) : r.hasAngularVelocity = !1, this.dispatchEvent(Ru)));
    }
    return r !== null && (r.visible = i !== null), l !== null && (l.visible = s !== null), a !== null && (a.visible = o !== null), this;
  }
}
class Fu extends _t {
  constructor(e, t, n, i, s, o, r, l, a, c) {
    if (c = c !== void 0 ? c : 1026, c !== 1026 && c !== 1027)
      throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");
    n === void 0 && c === 1026 && (n = 1014), n === void 0 && c === 1027 && (n = 1020), super(null, i, s, o, r, l, c, n, a), this.isDepthTexture = !0, this.image = { width: e, height: t }, this.magFilter = r !== void 0 ? r : 1003, this.minFilter = l !== void 0 ? l : 1003, this.flipY = !1, this.generateMipmaps = !1;
  }
}
class Du extends $n {
  constructor(e, t) {
    super();
    const n = this;
    let i = null, s = 1, o = null, r = "local-floor", l = null, a = null, c = null, d = null, u = null, m = null;
    const g = t.getContextAttributes();
    let p = null, f = null;
    const v = [], _ = [], w = new gt();
    w.layers.enable(1), w.viewport = new $e();
    const x = new gt();
    x.layers.enable(2), x.viewport = new $e();
    const M = [w, x], E = new Lu();
    E.layers.enable(1), E.layers.enable(2);
    let R = null, y = null;
    this.cameraAutoUpdate = !0, this.enabled = !1, this.isPresenting = !1, this.getController = function(N) {
      let H = v[N];
      return H === void 0 && (H = new Ts(), v[N] = H), H.getTargetRaySpace();
    }, this.getControllerGrip = function(N) {
      let H = v[N];
      return H === void 0 && (H = new Ts(), v[N] = H), H.getGripSpace();
    }, this.getHand = function(N) {
      let H = v[N];
      return H === void 0 && (H = new Ts(), v[N] = H), H.getHandSpace();
    };
    function A(N) {
      const H = _.indexOf(N.inputSource);
      if (H === -1)
        return;
      const J = v[H];
      J !== void 0 && J.dispatchEvent({ type: N.type, data: N.inputSource });
    }
    function F() {
      i.removeEventListener("select", A), i.removeEventListener("selectstart", A), i.removeEventListener("selectend", A), i.removeEventListener("squeeze", A), i.removeEventListener("squeezestart", A), i.removeEventListener("squeezeend", A), i.removeEventListener("end", F), i.removeEventListener("inputsourceschange", P);
      for (let N = 0; N < v.length; N++) {
        const H = _[N];
        H !== null && (_[N] = null, v[N].disconnect(H));
      }
      R = null, y = null, e.setRenderTarget(p), u = null, d = null, c = null, i = null, f = null, k.stop(), n.isPresenting = !1, n.dispatchEvent({ type: "sessionend" });
    }
    this.setFramebufferScaleFactor = function(N) {
      s = N, n.isPresenting === !0 && console.warn("THREE.WebXRManager: Cannot change framebuffer scale while presenting.");
    }, this.setReferenceSpaceType = function(N) {
      r = N, n.isPresenting === !0 && console.warn("THREE.WebXRManager: Cannot change reference space type while presenting.");
    }, this.getReferenceSpace = function() {
      return l || o;
    }, this.setReferenceSpace = function(N) {
      l = N;
    }, this.getBaseLayer = function() {
      return d !== null ? d : u;
    }, this.getBinding = function() {
      return c;
    }, this.getFrame = function() {
      return m;
    }, this.getSession = function() {
      return i;
    }, this.setSession = async function(N) {
      if (i = N, i !== null) {
        if (p = e.getRenderTarget(), i.addEventListener("select", A), i.addEventListener("selectstart", A), i.addEventListener("selectend", A), i.addEventListener("squeeze", A), i.addEventListener("squeezestart", A), i.addEventListener("squeezeend", A), i.addEventListener("end", F), i.addEventListener("inputsourceschange", P), g.xrCompatible !== !0 && await t.makeXRCompatible(), i.renderState.layers === void 0 || e.capabilities.isWebGL2 === !1) {
          const H = {
            antialias: i.renderState.layers === void 0 ? g.antialias : !0,
            alpha: g.alpha,
            depth: g.depth,
            stencil: g.stencil,
            framebufferScaleFactor: s
          };
          u = new XRWebGLLayer(i, t, H), i.updateRenderState({ baseLayer: u }), f = new En(
            u.framebufferWidth,
            u.framebufferHeight,
            {
              format: 1023,
              type: 1009,
              encoding: e.outputEncoding
            }
          );
        } else {
          let H = null, J = null, V = null;
          g.depth && (V = g.stencil ? 35056 : 33190, H = g.stencil ? 1027 : 1026, J = g.stencil ? 1020 : 1014);
          const ee = {
            colorFormat: 32856,
            depthFormat: V,
            scaleFactor: s
          };
          c = new XRWebGLBinding(i, t), d = c.createProjectionLayer(ee), i.updateRenderState({ layers: [d] }), f = new En(
            d.textureWidth,
            d.textureHeight,
            {
              format: 1023,
              type: 1009,
              depthTexture: new Fu(d.textureWidth, d.textureHeight, J, void 0, void 0, void 0, void 0, void 0, void 0, H),
              stencilBuffer: g.stencil,
              encoding: e.outputEncoding,
              samples: g.antialias ? 4 : 0
            }
          );
          const ce = e.properties.get(f);
          ce.__ignoreDepthValues = d.ignoreDepthValues;
        }
        f.isXRRenderTarget = !0, this.setFoveation(1), l = null, o = await i.requestReferenceSpace(r), k.setContext(i), k.start(), n.isPresenting = !0, n.dispatchEvent({ type: "sessionstart" });
      }
    };
    function P(N) {
      for (let H = 0; H < N.removed.length; H++) {
        const J = N.removed[H], V = _.indexOf(J);
        V >= 0 && (_[V] = null, v[V].dispatchEvent({ type: "disconnected", data: J }));
      }
      for (let H = 0; H < N.added.length; H++) {
        const J = N.added[H];
        let V = _.indexOf(J);
        if (V === -1) {
          for (let ce = 0; ce < v.length; ce++)
            if (ce >= _.length) {
              _.push(J), V = ce;
              break;
            } else if (_[ce] === null) {
              _[ce] = J, V = ce;
              break;
            }
          if (V === -1)
            break;
        }
        const ee = v[V];
        ee && ee.dispatchEvent({ type: "connected", data: J });
      }
    }
    const G = new O(), z = new O();
    function L(N, H, J) {
      G.setFromMatrixPosition(H.matrixWorld), z.setFromMatrixPosition(J.matrixWorld);
      const V = G.distanceTo(z), ee = H.projectionMatrix.elements, ce = J.projectionMatrix.elements, ge = ee[14] / (ee[10] - 1), $ = ee[14] / (ee[10] + 1), De = (ee[9] + 1) / ee[5], ve = (ee[9] - 1) / ee[5], xe = (ee[8] - 1) / ee[0], ue = (ce[8] + 1) / ce[0], Oe = ge * xe, Ee = ge * ue, me = V / (-xe + ue), et = me * -xe;
      H.matrixWorld.decompose(N.position, N.quaternion, N.scale), N.translateX(et), N.translateZ(me), N.matrixWorld.compose(N.position, N.quaternion, N.scale), N.matrixWorldInverse.copy(N.matrixWorld).invert();
      const ut = ge + me, rt = $ + me, Rt = Oe - et, tt = Ee + (V - et), Ne = De * $ / rt * ut, Gt = ve * $ / rt * ut;
      N.projectionMatrix.makePerspective(Rt, tt, Ne, Gt, ut, rt);
    }
    function I(N, H) {
      H === null ? N.matrixWorld.copy(N.matrix) : N.matrixWorld.multiplyMatrices(H.matrixWorld, N.matrix), N.matrixWorldInverse.copy(N.matrixWorld).invert();
    }
    this.updateCamera = function(N) {
      if (i === null)
        return;
      E.near = x.near = w.near = N.near, E.far = x.far = w.far = N.far, (R !== E.near || y !== E.far) && (i.updateRenderState({
        depthNear: E.near,
        depthFar: E.far
      }), R = E.near, y = E.far);
      const H = N.parent, J = E.cameras;
      I(E, H);
      for (let ee = 0; ee < J.length; ee++)
        I(J[ee], H);
      E.matrixWorld.decompose(E.position, E.quaternion, E.scale), N.position.copy(E.position), N.quaternion.copy(E.quaternion), N.scale.copy(E.scale), N.matrix.copy(E.matrix), N.matrixWorld.copy(E.matrixWorld);
      const V = N.children;
      for (let ee = 0, ce = V.length; ee < ce; ee++)
        V[ee].updateMatrixWorld(!0);
      J.length === 2 ? L(E, w, x) : E.projectionMatrix.copy(w.projectionMatrix);
    }, this.getCamera = function() {
      return E;
    }, this.getFoveation = function() {
      if (d !== null)
        return d.fixedFoveation;
      if (u !== null)
        return u.fixedFoveation;
    }, this.setFoveation = function(N) {
      d !== null && (d.fixedFoveation = N), u !== null && u.fixedFoveation !== void 0 && (u.fixedFoveation = N);
    };
    let D = null;
    function q(N, H) {
      if (a = H.getViewerPose(l || o), m = H, a !== null) {
        const J = a.views;
        u !== null && (e.setRenderTargetFramebuffer(f, u.framebuffer), e.setRenderTarget(f));
        let V = !1;
        J.length !== E.cameras.length && (E.cameras.length = 0, V = !0);
        for (let ee = 0; ee < J.length; ee++) {
          const ce = J[ee];
          let ge = null;
          if (u !== null)
            ge = u.getViewport(ce);
          else {
            const De = c.getViewSubImage(d, ce);
            ge = De.viewport, ee === 0 && (e.setRenderTargetTextures(
              f,
              De.colorTexture,
              d.ignoreDepthValues ? void 0 : De.depthStencilTexture
            ), e.setRenderTarget(f));
          }
          let $ = M[ee];
          $ === void 0 && ($ = new gt(), $.layers.enable(ee), $.viewport = new $e(), M[ee] = $), $.matrix.fromArray(ce.transform.matrix), $.projectionMatrix.fromArray(ce.projectionMatrix), $.viewport.set(ge.x, ge.y, ge.width, ge.height), ee === 0 && E.matrix.copy($.matrix), V === !0 && E.cameras.push($);
        }
      }
      for (let J = 0; J < v.length; J++) {
        const V = _[J], ee = v[J];
        V !== null && ee !== void 0 && ee.update(V, H, l || o);
      }
      D && D(N, H), m = null;
    }
    const k = new fo();
    k.setAnimationLoop(q), this.setAnimationLoop = function(N) {
      D = N;
    }, this.dispose = function() {
    };
  }
}
function Pu(h, e) {
  function t(p, f) {
    p.fogColor.value.copy(f.color), f.isFog ? (p.fogNear.value = f.near, p.fogFar.value = f.far) : f.isFogExp2 && (p.fogDensity.value = f.density);
  }
  function n(p, f, v, _, w) {
    f.isMeshBasicMaterial || f.isMeshLambertMaterial ? i(p, f) : f.isMeshToonMaterial ? (i(p, f), c(p, f)) : f.isMeshPhongMaterial ? (i(p, f), a(p, f)) : f.isMeshStandardMaterial ? (i(p, f), d(p, f), f.isMeshPhysicalMaterial && u(p, f, w)) : f.isMeshMatcapMaterial ? (i(p, f), m(p, f)) : f.isMeshDepthMaterial ? i(p, f) : f.isMeshDistanceMaterial ? (i(p, f), g(p, f)) : f.isMeshNormalMaterial ? i(p, f) : f.isLineBasicMaterial ? (s(p, f), f.isLineDashedMaterial && o(p, f)) : f.isPointsMaterial ? r(p, f, v, _) : f.isSpriteMaterial ? l(p, f) : f.isShadowMaterial ? (p.color.value.copy(f.color), p.opacity.value = f.opacity) : f.isShaderMaterial && (f.uniformsNeedUpdate = !1);
  }
  function i(p, f) {
    p.opacity.value = f.opacity, f.color && p.diffuse.value.copy(f.color), f.emissive && p.emissive.value.copy(f.emissive).multiplyScalar(f.emissiveIntensity), f.map && (p.map.value = f.map), f.alphaMap && (p.alphaMap.value = f.alphaMap), f.bumpMap && (p.bumpMap.value = f.bumpMap, p.bumpScale.value = f.bumpScale, f.side === 1 && (p.bumpScale.value *= -1)), f.displacementMap && (p.displacementMap.value = f.displacementMap, p.displacementScale.value = f.displacementScale, p.displacementBias.value = f.displacementBias), f.emissiveMap && (p.emissiveMap.value = f.emissiveMap), f.normalMap && (p.normalMap.value = f.normalMap, p.normalScale.value.copy(f.normalScale), f.side === 1 && p.normalScale.value.negate()), f.specularMap && (p.specularMap.value = f.specularMap), f.alphaTest > 0 && (p.alphaTest.value = f.alphaTest);
    const v = e.get(f).envMap;
    if (v && (p.envMap.value = v, p.flipEnvMap.value = v.isCubeTexture && v.isRenderTargetTexture === !1 ? -1 : 1, p.reflectivity.value = f.reflectivity, p.ior.value = f.ior, p.refractionRatio.value = f.refractionRatio), f.lightMap) {
      p.lightMap.value = f.lightMap;
      const x = h.physicallyCorrectLights !== !0 ? Math.PI : 1;
      p.lightMapIntensity.value = f.lightMapIntensity * x;
    }
    f.aoMap && (p.aoMap.value = f.aoMap, p.aoMapIntensity.value = f.aoMapIntensity);
    let _;
    f.map ? _ = f.map : f.specularMap ? _ = f.specularMap : f.displacementMap ? _ = f.displacementMap : f.normalMap ? _ = f.normalMap : f.bumpMap ? _ = f.bumpMap : f.roughnessMap ? _ = f.roughnessMap : f.metalnessMap ? _ = f.metalnessMap : f.alphaMap ? _ = f.alphaMap : f.emissiveMap ? _ = f.emissiveMap : f.clearcoatMap ? _ = f.clearcoatMap : f.clearcoatNormalMap ? _ = f.clearcoatNormalMap : f.clearcoatRoughnessMap ? _ = f.clearcoatRoughnessMap : f.iridescenceMap ? _ = f.iridescenceMap : f.iridescenceThicknessMap ? _ = f.iridescenceThicknessMap : f.specularIntensityMap ? _ = f.specularIntensityMap : f.specularColorMap ? _ = f.specularColorMap : f.transmissionMap ? _ = f.transmissionMap : f.thicknessMap ? _ = f.thicknessMap : f.sheenColorMap ? _ = f.sheenColorMap : f.sheenRoughnessMap && (_ = f.sheenRoughnessMap), _ !== void 0 && (_.isWebGLRenderTarget && (_ = _.texture), _.matrixAutoUpdate === !0 && _.updateMatrix(), p.uvTransform.value.copy(_.matrix));
    let w;
    f.aoMap ? w = f.aoMap : f.lightMap && (w = f.lightMap), w !== void 0 && (w.isWebGLRenderTarget && (w = w.texture), w.matrixAutoUpdate === !0 && w.updateMatrix(), p.uv2Transform.value.copy(w.matrix));
  }
  function s(p, f) {
    p.diffuse.value.copy(f.color), p.opacity.value = f.opacity;
  }
  function o(p, f) {
    p.dashSize.value = f.dashSize, p.totalSize.value = f.dashSize + f.gapSize, p.scale.value = f.scale;
  }
  function r(p, f, v, _) {
    p.diffuse.value.copy(f.color), p.opacity.value = f.opacity, p.size.value = f.size * v, p.scale.value = _ * 0.5, f.map && (p.map.value = f.map), f.alphaMap && (p.alphaMap.value = f.alphaMap), f.alphaTest > 0 && (p.alphaTest.value = f.alphaTest);
    let w;
    f.map ? w = f.map : f.alphaMap && (w = f.alphaMap), w !== void 0 && (w.matrixAutoUpdate === !0 && w.updateMatrix(), p.uvTransform.value.copy(w.matrix));
  }
  function l(p, f) {
    p.diffuse.value.copy(f.color), p.opacity.value = f.opacity, p.rotation.value = f.rotation, f.map && (p.map.value = f.map), f.alphaMap && (p.alphaMap.value = f.alphaMap), f.alphaTest > 0 && (p.alphaTest.value = f.alphaTest);
    let v;
    f.map ? v = f.map : f.alphaMap && (v = f.alphaMap), v !== void 0 && (v.matrixAutoUpdate === !0 && v.updateMatrix(), p.uvTransform.value.copy(v.matrix));
  }
  function a(p, f) {
    p.specular.value.copy(f.specular), p.shininess.value = Math.max(f.shininess, 1e-4);
  }
  function c(p, f) {
    f.gradientMap && (p.gradientMap.value = f.gradientMap);
  }
  function d(p, f) {
    p.roughness.value = f.roughness, p.metalness.value = f.metalness, f.roughnessMap && (p.roughnessMap.value = f.roughnessMap), f.metalnessMap && (p.metalnessMap.value = f.metalnessMap), e.get(f).envMap && (p.envMapIntensity.value = f.envMapIntensity);
  }
  function u(p, f, v) {
    p.ior.value = f.ior, f.sheen > 0 && (p.sheenColor.value.copy(f.sheenColor).multiplyScalar(f.sheen), p.sheenRoughness.value = f.sheenRoughness, f.sheenColorMap && (p.sheenColorMap.value = f.sheenColorMap), f.sheenRoughnessMap && (p.sheenRoughnessMap.value = f.sheenRoughnessMap)), f.clearcoat > 0 && (p.clearcoat.value = f.clearcoat, p.clearcoatRoughness.value = f.clearcoatRoughness, f.clearcoatMap && (p.clearcoatMap.value = f.clearcoatMap), f.clearcoatRoughnessMap && (p.clearcoatRoughnessMap.value = f.clearcoatRoughnessMap), f.clearcoatNormalMap && (p.clearcoatNormalScale.value.copy(f.clearcoatNormalScale), p.clearcoatNormalMap.value = f.clearcoatNormalMap, f.side === 1 && p.clearcoatNormalScale.value.negate())), f.iridescence > 0 && (p.iridescence.value = f.iridescence, p.iridescenceIOR.value = f.iridescenceIOR, p.iridescenceThicknessMinimum.value = f.iridescenceThicknessRange[0], p.iridescenceThicknessMaximum.value = f.iridescenceThicknessRange[1], f.iridescenceMap && (p.iridescenceMap.value = f.iridescenceMap), f.iridescenceThicknessMap && (p.iridescenceThicknessMap.value = f.iridescenceThicknessMap)), f.transmission > 0 && (p.transmission.value = f.transmission, p.transmissionSamplerMap.value = v.texture, p.transmissionSamplerSize.value.set(v.width, v.height), f.transmissionMap && (p.transmissionMap.value = f.transmissionMap), p.thickness.value = f.thickness, f.thicknessMap && (p.thicknessMap.value = f.thicknessMap), p.attenuationDistance.value = f.attenuationDistance, p.attenuationColor.value.copy(f.attenuationColor)), p.specularIntensity.value = f.specularIntensity, p.specularColor.value.copy(f.specularColor), f.specularIntensityMap && (p.specularIntensityMap.value = f.specularIntensityMap), f.specularColorMap && (p.specularColorMap.value = f.specularColorMap);
  }
  function m(p, f) {
    f.matcap && (p.matcap.value = f.matcap);
  }
  function g(p, f) {
    p.referencePosition.value.copy(f.referencePosition), p.nearDistance.value = f.nearDistance, p.farDistance.value = f.farDistance;
  }
  return {
    refreshFogUniforms: t,
    refreshMaterialUniforms: n
  };
}
function Iu(h, e, t, n) {
  let i = {}, s = {}, o = [];
  const r = t.isWebGL2 ? h.getParameter(35375) : 0;
  function l(_, w) {
    const x = w.program;
    n.uniformBlockBinding(_, x);
  }
  function a(_, w) {
    let x = i[_.id];
    x === void 0 && (g(_), x = c(_), i[_.id] = x, _.addEventListener("dispose", f));
    const M = w.program;
    n.updateUBOMapping(_, M);
    const E = e.render.frame;
    s[_.id] !== E && (u(_), s[_.id] = E);
  }
  function c(_) {
    const w = d();
    _.__bindingPointIndex = w;
    const x = h.createBuffer(), M = _.__size, E = _.usage;
    return h.bindBuffer(35345, x), h.bufferData(35345, M, E), h.bindBuffer(35345, null), h.bindBufferBase(35345, w, x), x;
  }
  function d() {
    for (let _ = 0; _ < r; _++)
      if (o.indexOf(_) === -1)
        return o.push(_), _;
    return console.error("THREE.WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."), 0;
  }
  function u(_) {
    const w = i[_.id], x = _.uniforms, M = _.__cache;
    h.bindBuffer(35345, w);
    for (let E = 0, R = x.length; E < R; E++) {
      const y = x[E];
      if (m(y, E, M) === !0) {
        const A = y.value, F = y.__offset;
        typeof A == "number" ? (y.__data[0] = A, h.bufferSubData(35345, F, y.__data)) : (y.value.isMatrix3 ? (y.__data[0] = y.value.elements[0], y.__data[1] = y.value.elements[1], y.__data[2] = y.value.elements[2], y.__data[3] = y.value.elements[0], y.__data[4] = y.value.elements[3], y.__data[5] = y.value.elements[4], y.__data[6] = y.value.elements[5], y.__data[7] = y.value.elements[0], y.__data[8] = y.value.elements[6], y.__data[9] = y.value.elements[7], y.__data[10] = y.value.elements[8], y.__data[11] = y.value.elements[0]) : A.toArray(y.__data), h.bufferSubData(35345, F, y.__data));
      }
    }
    h.bindBuffer(35345, null);
  }
  function m(_, w, x) {
    const M = _.value;
    if (x[w] === void 0)
      return typeof M == "number" ? x[w] = M : x[w] = M.clone(), !0;
    if (typeof M == "number") {
      if (x[w] !== M)
        return x[w] = M, !0;
    } else {
      const E = x[w];
      if (E.equals(M) === !1)
        return E.copy(M), !0;
    }
    return !1;
  }
  function g(_) {
    const w = _.uniforms;
    let x = 0;
    const M = 16;
    let E = 0;
    for (let R = 0, y = w.length; R < y; R++) {
      const A = w[R], F = p(A);
      if (A.__data = new Float32Array(F.storage / Float32Array.BYTES_PER_ELEMENT), A.__offset = x, R > 0) {
        E = x % M;
        const P = M - E;
        E !== 0 && P - F.boundary < 0 && (x += M - E, A.__offset = x);
      }
      x += F.storage;
    }
    return E = x % M, E > 0 && (x += M - E), _.__size = x, _.__cache = {}, this;
  }
  function p(_) {
    const w = _.value, x = {
      boundary: 0,
      storage: 0
    };
    return typeof w == "number" ? (x.boundary = 4, x.storage = 4) : w.isVector2 ? (x.boundary = 8, x.storage = 8) : w.isVector3 || w.isColor ? (x.boundary = 16, x.storage = 12) : w.isVector4 ? (x.boundary = 16, x.storage = 16) : w.isMatrix3 ? (x.boundary = 48, x.storage = 48) : w.isMatrix4 ? (x.boundary = 64, x.storage = 64) : w.isTexture ? console.warn("THREE.WebGLRenderer: Texture samplers can not be part of an uniforms group.") : console.warn("THREE.WebGLRenderer: Unsupported uniform value type.", w), x;
  }
  function f(_) {
    const w = _.target;
    w.removeEventListener("dispose", f);
    const x = o.indexOf(w.__bindingPointIndex);
    o.splice(x, 1), h.deleteBuffer(i[w.id]), delete i[w.id], delete s[w.id];
  }
  function v() {
    for (const _ in i)
      h.deleteBuffer(i[_]);
    o = [], i = {}, s = {};
  }
  return {
    bind: l,
    update: a,
    dispose: v
  };
}
function zu() {
  const h = qi("canvas");
  return h.style.display = "block", h;
}
function xo(h = {}) {
  this.isWebGLRenderer = !0;
  const e = h.canvas !== void 0 ? h.canvas : zu(), t = h.context !== void 0 ? h.context : null, n = h.depth !== void 0 ? h.depth : !0, i = h.stencil !== void 0 ? h.stencil : !0, s = h.antialias !== void 0 ? h.antialias : !1, o = h.premultipliedAlpha !== void 0 ? h.premultipliedAlpha : !0, r = h.preserveDrawingBuffer !== void 0 ? h.preserveDrawingBuffer : !1, l = h.powerPreference !== void 0 ? h.powerPreference : "default", a = h.failIfMajorPerformanceCaveat !== void 0 ? h.failIfMajorPerformanceCaveat : !1;
  let c;
  t !== null ? c = t.getContextAttributes().alpha : c = h.alpha !== void 0 ? h.alpha : !1;
  let d = null, u = null;
  const m = [], g = [];
  this.domElement = e, this.debug = {
    checkShaderErrors: !0
  }, this.autoClear = !0, this.autoClearColor = !0, this.autoClearDepth = !0, this.autoClearStencil = !0, this.sortObjects = !0, this.clippingPlanes = [], this.localClippingEnabled = !1, this.outputEncoding = 3e3, this.physicallyCorrectLights = !1, this.toneMapping = 0, this.toneMappingExposure = 1, Object.defineProperties(this, {
    gammaFactor: {
      get: function() {
        return console.warn("THREE.WebGLRenderer: .gammaFactor has been removed."), 2;
      },
      set: function() {
        console.warn("THREE.WebGLRenderer: .gammaFactor has been removed.");
      }
    }
  });
  const p = this;
  let f = !1, v = 0, _ = 0, w = null, x = -1, M = null;
  const E = new $e(), R = new $e();
  let y = null, A = e.width, F = e.height, P = 1, G = null, z = null;
  const L = new $e(0, 0, A, F), I = new $e(0, 0, A, F);
  let D = !1;
  const q = new Us();
  let k = !1, N = !1, H = null;
  const J = new Ke(), V = new Ce(), ee = new O(), ce = { background: null, fog: null, environment: null, overrideMaterial: null, isScene: !0 };
  function ge() {
    return w === null ? P : 1;
  }
  let $ = t;
  function De(T, U) {
    for (let X = 0; X < T.length; X++) {
      const W = T[X], K = e.getContext(W, U);
      if (K !== null)
        return K;
    }
    return null;
  }
  try {
    const T = {
      alpha: !0,
      depth: n,
      stencil: i,
      antialias: s,
      premultipliedAlpha: o,
      preserveDrawingBuffer: r,
      powerPreference: l,
      failIfMajorPerformanceCaveat: a
    };
    if ("setAttribute" in e && e.setAttribute("data-engine", `three.js r${Os}`), e.addEventListener("webglcontextlost", we, !1), e.addEventListener("webglcontextrestored", Ie, !1), e.addEventListener("webglcontextcreationerror", We, !1), $ === null) {
      const U = ["webgl2", "webgl", "experimental-webgl"];
      if (p.isWebGL1Renderer === !0 && U.shift(), $ = De(U, T), $ === null)
        throw De(U) ? new Error("Error creating WebGL context with your selected attributes.") : new Error("Error creating WebGL context.");
    }
    $.getShaderPrecisionFormat === void 0 && ($.getShaderPrecisionFormat = function() {
      return { rangeMin: 1, rangeMax: 1, precision: 1 };
    });
  } catch (T) {
    throw console.error("THREE.WebGLRenderer: " + T.message), T;
  }
  let ve, xe, ue, Oe, Ee, me, et, ut, rt, Rt, tt, Ne, Gt, Ft, C, S, Z, Q, te, re, ye, j, pe, he;
  function fe() {
    ve = new qc($), xe = new Oc($, ve, h), ve.init(xe), j = new Cu($, ve, xe), ue = new Tu($, ve, xe), Oe = new Yc(), Ee = new du(), me = new Au($, ve, ue, Ee, xe, j, Oe), et = new Gc(p), ut = new Hc(p), rt = new ra($, xe), pe = new Bc($, ve, rt, xe), Rt = new Xc($, rt, Oe, pe), tt = new Jc($, Rt, rt, Oe), te = new Kc($, xe, me), S = new Uc(Ee), Ne = new uu(p, et, ut, ve, xe, pe, S), Gt = new Pu(p, Ee), Ft = new pu(), C = new yu(ve, xe), Q = new zc(p, et, ue, tt, c, o), Z = new Eu(p, tt, xe), he = new Iu($, Oe, xe, ue), re = new Nc($, ve, Oe, xe), ye = new jc($, ve, Oe, xe), Oe.programs = Ne.programs, p.capabilities = xe, p.extensions = ve, p.properties = Ee, p.renderLists = Ft, p.shadowMap = Z, p.state = ue, p.info = Oe;
  }
  fe();
  const de = new Du(p, $);
  this.xr = de, this.getContext = function() {
    return $;
  }, this.getContextAttributes = function() {
    return $.getContextAttributes();
  }, this.forceContextLoss = function() {
    const T = ve.get("WEBGL_lose_context");
    T && T.loseContext();
  }, this.forceContextRestore = function() {
    const T = ve.get("WEBGL_lose_context");
    T && T.restoreContext();
  }, this.getPixelRatio = function() {
    return P;
  }, this.setPixelRatio = function(T) {
    T !== void 0 && (P = T, this.setSize(A, F, !1));
  }, this.getSize = function(T) {
    return T.set(A, F);
  }, this.setSize = function(T, U, X) {
    if (de.isPresenting) {
      console.warn("THREE.WebGLRenderer: Can't change size while VR device is presenting.");
      return;
    }
    A = T, F = U, e.width = Math.floor(T * P), e.height = Math.floor(U * P), X !== !1 && (e.style.width = T + "px", e.style.height = U + "px"), this.setViewport(0, 0, T, U);
  }, this.getDrawingBufferSize = function(T) {
    return T.set(A * P, F * P).floor();
  }, this.setDrawingBufferSize = function(T, U, X) {
    A = T, F = U, P = X, e.width = Math.floor(T * X), e.height = Math.floor(U * X), this.setViewport(0, 0, T, U);
  }, this.getCurrentViewport = function(T) {
    return T.copy(E);
  }, this.getViewport = function(T) {
    return T.copy(L);
  }, this.setViewport = function(T, U, X, W) {
    T.isVector4 ? L.set(T.x, T.y, T.z, T.w) : L.set(T, U, X, W), ue.viewport(E.copy(L).multiplyScalar(P).floor());
  }, this.getScissor = function(T) {
    return T.copy(I);
  }, this.setScissor = function(T, U, X, W) {
    T.isVector4 ? I.set(T.x, T.y, T.z, T.w) : I.set(T, U, X, W), ue.scissor(R.copy(I).multiplyScalar(P).floor());
  }, this.getScissorTest = function() {
    return D;
  }, this.setScissorTest = function(T) {
    ue.setScissorTest(D = T);
  }, this.setOpaqueSort = function(T) {
    G = T;
  }, this.setTransparentSort = function(T) {
    z = T;
  }, this.getClearColor = function(T) {
    return T.copy(Q.getClearColor());
  }, this.setClearColor = function() {
    Q.setClearColor.apply(Q, arguments);
  }, this.getClearAlpha = function() {
    return Q.getClearAlpha();
  }, this.setClearAlpha = function() {
    Q.setClearAlpha.apply(Q, arguments);
  }, this.clear = function(T = !0, U = !0, X = !0) {
    let W = 0;
    T && (W |= 16384), U && (W |= 256), X && (W |= 1024), $.clear(W);
  }, this.clearColor = function() {
    this.clear(!0, !1, !1);
  }, this.clearDepth = function() {
    this.clear(!1, !0, !1);
  }, this.clearStencil = function() {
    this.clear(!1, !1, !0);
  }, this.dispose = function() {
    e.removeEventListener("webglcontextlost", we, !1), e.removeEventListener("webglcontextrestored", Ie, !1), e.removeEventListener("webglcontextcreationerror", We, !1), Ft.dispose(), C.dispose(), Ee.dispose(), et.dispose(), ut.dispose(), tt.dispose(), pe.dispose(), he.dispose(), Ne.dispose(), de.dispose(), de.removeEventListener("sessionstart", Re), de.removeEventListener("sessionend", Je), H && (H.dispose(), H = null), Ve.stop();
  };
  function we(T) {
    T.preventDefault(), console.log("THREE.WebGLRenderer: Context Lost."), f = !0;
  }
  function Ie() {
    console.log("THREE.WebGLRenderer: Context Restored."), f = !1;
    const T = Oe.autoReset, U = Z.enabled, X = Z.autoUpdate, W = Z.needsUpdate, K = Z.type;
    fe(), Oe.autoReset = T, Z.enabled = U, Z.autoUpdate = X, Z.needsUpdate = W, Z.type = K;
  }
  function We(T) {
    console.error("THREE.WebGLRenderer: A WebGL context could not be created. Reason: ", T.statusMessage);
  }
  function B(T) {
    const U = T.target;
    U.removeEventListener("dispose", B), ae(U);
  }
  function ae(T) {
    Y(T), Ee.remove(T);
  }
  function Y(T) {
    const U = Ee.get(T).programs;
    U !== void 0 && (U.forEach(function(X) {
      Ne.releaseProgram(X);
    }), T.isShaderMaterial && Ne.releaseShaderCache(T));
  }
  this.renderBufferDirect = function(T, U, X, W, K, _e) {
    U === null && (U = ce);
    const be = K.isMesh && K.matrixWorld.determinant() < 0, Se = Fo(T, U, X, W, K);
    ue.setMaterial(W, be);
    let Me = X.index;
    const Be = X.attributes.position;
    if (Me === null) {
      if (Be === void 0 || Be.count === 0)
        return;
    } else if (Me.count === 0)
      return;
    let Le = 1;
    W.wireframe === !0 && (Me = Rt.getWireframeAttribute(X), Le = 2), pe.setup(K, W, Se, X, Me);
    let Fe, ke = re;
    Me !== null && (Fe = rt.get(Me), ke = ye, ke.setIndex(Fe));
    const un = Me !== null ? Me.count : Be.count, Cn = X.drawRange.start * Le, Ln = X.drawRange.count * Le, Dt = _e !== null ? _e.start * Le : 0, ze = _e !== null ? _e.count * Le : 1 / 0, Rn = Math.max(Cn, Dt), He = Math.min(un, Cn + Ln, Dt + ze) - 1, yt = Math.max(0, He - Rn + 1);
    if (yt !== 0) {
      if (K.isMesh)
        W.wireframe === !0 ? (ue.setLineWidth(W.wireframeLinewidth * ge()), ke.setMode(1)) : ke.setMode(4);
      else if (K.isLine) {
        let tn = W.linewidth;
        tn === void 0 && (tn = 1), ue.setLineWidth(tn * ge()), K.isLineSegments ? ke.setMode(1) : K.isLineLoop ? ke.setMode(2) : ke.setMode(3);
      } else
        K.isPoints ? ke.setMode(0) : K.isSprite && ke.setMode(4);
      if (K.isInstancedMesh)
        ke.renderInstances(Rn, yt, K.count);
      else if (X.isInstancedBufferGeometry) {
        const tn = Math.min(X.instanceCount, X._maxInstanceCount);
        ke.renderInstances(Rn, yt, tn);
      } else
        ke.render(Rn, yt);
    }
  }, this.compile = function(T, U) {
    u = C.get(T), u.init(), g.push(u), T.traverseVisible(function(X) {
      X.isLight && X.layers.test(U.layers) && (u.pushLight(X), X.castShadow && u.pushShadow(X));
    }), u.setupLights(p.physicallyCorrectLights), T.traverse(function(X) {
      const W = X.material;
      if (W)
        if (Array.isArray(W))
          for (let K = 0; K < W.length; K++) {
            const _e = W[K];
            Zi(_e, T, X);
          }
        else
          Zi(W, T, X);
    }), g.pop(), u = null;
  };
  let oe = null;
  function se(T) {
    oe && oe(T);
  }
  function Re() {
    Ve.stop();
  }
  function Je() {
    Ve.start();
  }
  const Ve = new fo();
  Ve.setAnimationLoop(se), typeof self < "u" && Ve.setContext(self), this.setAnimationLoop = function(T) {
    oe = T, de.setAnimationLoop(T), T === null ? Ve.stop() : Ve.start();
  }, de.addEventListener("sessionstart", Re), de.addEventListener("sessionend", Je), this.render = function(T, U) {
    if (U !== void 0 && U.isCamera !== !0) {
      console.error("THREE.WebGLRenderer.render: camera is not an instance of THREE.Camera.");
      return;
    }
    if (f === !0)
      return;
    T.autoUpdate === !0 && T.updateMatrixWorld(), U.parent === null && U.updateMatrixWorld(), de.enabled === !0 && de.isPresenting === !0 && (de.cameraAutoUpdate === !0 && de.updateCamera(U), U = de.getCamera()), T.isScene === !0 && T.onBeforeRender(p, T, U, w), u = C.get(T, g.length), u.init(), g.push(u), J.multiplyMatrices(U.projectionMatrix, U.matrixWorldInverse), q.setFromProjectionMatrix(J), N = this.localClippingEnabled, k = S.init(this.clippingPlanes, N, U), d = Ft.get(T, m.length), d.init(), m.push(d), en(T, U, 0, p.sortObjects), d.finish(), p.sortObjects === !0 && d.sort(G, z), k === !0 && S.beginShadows();
    const X = u.state.shadowsArray;
    if (Z.render(X, T, U), k === !0 && S.endShadows(), this.info.autoReset === !0 && this.info.reset(), Q.render(d, T), u.setupLights(p.physicallyCorrectLights), U.isArrayCamera) {
      const W = U.cameras;
      for (let K = 0, _e = W.length; K < _e; K++) {
        const be = W[K];
        Ge(d, T, be, be.viewport);
      }
    } else
      Ge(d, T, U);
    w !== null && (me.updateMultisampleRenderTarget(w), me.updateRenderTargetMipmap(w)), T.isScene === !0 && T.onAfterRender(p, T, U), pe.resetDefaultState(), x = -1, M = null, g.pop(), g.length > 0 ? u = g[g.length - 1] : u = null, m.pop(), m.length > 0 ? d = m[m.length - 1] : d = null;
  };
  function en(T, U, X, W) {
    if (T.visible === !1)
      return;
    if (T.layers.test(U.layers)) {
      if (T.isGroup)
        X = T.renderOrder;
      else if (T.isLOD)
        T.autoUpdate === !0 && T.update(U);
      else if (T.isLight)
        u.pushLight(T), T.castShadow && u.pushShadow(T);
      else if (T.isSprite) {
        if (!T.frustumCulled || q.intersectsSprite(T)) {
          W && ee.setFromMatrixPosition(T.matrixWorld).applyMatrix4(J);
          const be = tt.update(T), Se = T.material;
          Se.visible && d.push(T, be, Se, X, ee.z, null);
        }
      } else if ((T.isMesh || T.isLine || T.isPoints) && (T.isSkinnedMesh && T.skeleton.frame !== Oe.render.frame && (T.skeleton.update(), T.skeleton.frame = Oe.render.frame), !T.frustumCulled || q.intersectsObject(T))) {
        W && ee.setFromMatrixPosition(T.matrixWorld).applyMatrix4(J);
        const be = tt.update(T), Se = T.material;
        if (Array.isArray(Se)) {
          const Me = be.groups;
          for (let Be = 0, Le = Me.length; Be < Le; Be++) {
            const Fe = Me[Be], ke = Se[Fe.materialIndex];
            ke && ke.visible && d.push(T, be, ke, X, ee.z, Fe);
          }
        } else
          Se.visible && d.push(T, be, Se, X, ee.z, null);
      }
    }
    const _e = T.children;
    for (let be = 0, Se = _e.length; be < Se; be++)
      en(_e[be], U, X, W);
  }
  function Ge(T, U, X, W) {
    const K = T.opaque, _e = T.transmissive, be = T.transparent;
    u.setupLightsView(X), _e.length > 0 && kt(K, U, X), W && ue.viewport(E.copy(W)), K.length > 0 && xt(K, U, X), _e.length > 0 && xt(_e, U, X), be.length > 0 && xt(be, U, X), ue.buffers.depth.setTest(!0), ue.buffers.depth.setMask(!0), ue.buffers.color.setMask(!0), ue.setPolygonOffset(!1);
  }
  function kt(T, U, X) {
    const W = xe.isWebGL2;
    H === null && (H = new En(1, 1, {
      generateMipmaps: !0,
      type: ve.has("EXT_color_buffer_half_float") ? 1016 : 1009,
      minFilter: 1008,
      samples: W && s === !0 ? 4 : 0
    })), p.getDrawingBufferSize(V), W ? H.setSize(V.x, V.y) : H.setSize(Bs(V.x), Bs(V.y));
    const K = p.getRenderTarget();
    p.setRenderTarget(H), p.clear();
    const _e = p.toneMapping;
    p.toneMapping = 0, xt(T, U, X), p.toneMapping = _e, me.updateMultisampleRenderTarget(H), me.updateRenderTargetMipmap(H), p.setRenderTarget(K);
  }
  function xt(T, U, X) {
    const W = U.isScene === !0 ? U.overrideMaterial : null;
    for (let K = 0, _e = T.length; K < _e; K++) {
      const be = T[K], Se = be.object, Me = be.geometry, Be = W === null ? be.material : W, Le = be.group;
      Se.layers.test(X.layers) && Ro(Se, U, X, Me, Be, Le);
    }
  }
  function Ro(T, U, X, W, K, _e) {
    T.onBeforeRender(p, U, X, W, K, _e), T.modelViewMatrix.multiplyMatrices(X.matrixWorldInverse, T.matrixWorld), T.normalMatrix.getNormalMatrix(T.modelViewMatrix), K.onBeforeRender(p, U, X, W, T, _e), K.transparent === !0 && K.side === 2 ? (K.side = 1, K.needsUpdate = !0, p.renderBufferDirect(X, U, W, K, T, _e), K.side = 0, K.needsUpdate = !0, p.renderBufferDirect(X, U, W, K, T, _e), K.side = 2) : p.renderBufferDirect(X, U, W, K, T, _e), T.onAfterRender(p, U, X, W, K, _e);
  }
  function Zi(T, U, X) {
    U.isScene !== !0 && (U = ce);
    const W = Ee.get(T), K = u.state.lights, _e = u.state.shadowsArray, be = K.state.version, Se = Ne.getParameters(T, K.state, _e, U, X), Me = Ne.getProgramCacheKey(Se);
    let Be = W.programs;
    W.environment = T.isMeshStandardMaterial ? U.environment : null, W.fog = U.fog, W.envMap = (T.isMeshStandardMaterial ? ut : et).get(T.envMap || W.environment), Be === void 0 && (T.addEventListener("dispose", B), Be = /* @__PURE__ */ new Map(), W.programs = Be);
    let Le = Be.get(Me);
    if (Le !== void 0) {
      if (W.currentProgram === Le && W.lightsStateVersion === be)
        return Xs(T, Se), Le;
    } else
      Se.uniforms = Ne.getUniforms(T), T.onBuild(X, Se, p), T.onBeforeCompile(Se, p), Le = Ne.acquireProgram(Se, Me), Be.set(Me, Le), W.uniforms = Se.uniforms;
    const Fe = W.uniforms;
    (!T.isShaderMaterial && !T.isRawShaderMaterial || T.clipping === !0) && (Fe.clippingPlanes = S.uniform), Xs(T, Se), W.needsLights = Po(T), W.lightsStateVersion = be, W.needsLights && (Fe.ambientLightColor.value = K.state.ambient, Fe.lightProbe.value = K.state.probe, Fe.directionalLights.value = K.state.directional, Fe.directionalLightShadows.value = K.state.directionalShadow, Fe.spotLights.value = K.state.spot, Fe.spotLightShadows.value = K.state.spotShadow, Fe.rectAreaLights.value = K.state.rectArea, Fe.ltc_1.value = K.state.rectAreaLTC1, Fe.ltc_2.value = K.state.rectAreaLTC2, Fe.pointLights.value = K.state.point, Fe.pointLightShadows.value = K.state.pointShadow, Fe.hemisphereLights.value = K.state.hemi, Fe.directionalShadowMap.value = K.state.directionalShadowMap, Fe.directionalShadowMatrix.value = K.state.directionalShadowMatrix, Fe.spotShadowMap.value = K.state.spotShadowMap, Fe.spotShadowMatrix.value = K.state.spotShadowMatrix, Fe.pointShadowMap.value = K.state.pointShadowMap, Fe.pointShadowMatrix.value = K.state.pointShadowMatrix);
    const ke = Le.getUniforms(), un = Vi.seqWithValue(ke.seq, Fe);
    return W.currentProgram = Le, W.uniformsList = un, Le;
  }
  function Xs(T, U) {
    const X = Ee.get(T);
    X.outputEncoding = U.outputEncoding, X.instancing = U.instancing, X.skinning = U.skinning, X.morphTargets = U.morphTargets, X.morphNormals = U.morphNormals, X.morphColors = U.morphColors, X.morphTargetsCount = U.morphTargetsCount, X.numClippingPlanes = U.numClippingPlanes, X.numIntersection = U.numClipIntersection, X.vertexAlphas = U.vertexAlphas, X.vertexTangents = U.vertexTangents, X.toneMapping = U.toneMapping;
  }
  function Fo(T, U, X, W, K) {
    U.isScene !== !0 && (U = ce), me.resetTextureUnits();
    const _e = U.fog, be = W.isMeshStandardMaterial ? U.environment : null, Se = w === null ? p.outputEncoding : w.isXRRenderTarget === !0 ? w.texture.encoding : 3e3, Me = (W.isMeshStandardMaterial ? ut : et).get(W.envMap || be), Be = W.vertexColors === !0 && !!X.attributes.color && X.attributes.color.itemSize === 4, Le = !!W.normalMap && !!X.attributes.tangent, Fe = !!X.morphAttributes.position, ke = !!X.morphAttributes.normal, un = !!X.morphAttributes.color, Cn = W.toneMapped ? p.toneMapping : 0, Ln = X.morphAttributes.position || X.morphAttributes.normal || X.morphAttributes.color, Dt = Ln !== void 0 ? Ln.length : 0, ze = Ee.get(W), Rn = u.state.lights;
    if (k === !0 && (N === !0 || T !== M)) {
      const dt = T === M && W.id === x;
      S.setState(W, T, dt);
    }
    let He = !1;
    W.version === ze.__version ? (ze.needsLights && ze.lightsStateVersion !== Rn.state.version || ze.outputEncoding !== Se || K.isInstancedMesh && ze.instancing === !1 || !K.isInstancedMesh && ze.instancing === !0 || K.isSkinnedMesh && ze.skinning === !1 || !K.isSkinnedMesh && ze.skinning === !0 || ze.envMap !== Me || W.fog === !0 && ze.fog !== _e || ze.numClippingPlanes !== void 0 && (ze.numClippingPlanes !== S.numPlanes || ze.numIntersection !== S.numIntersection) || ze.vertexAlphas !== Be || ze.vertexTangents !== Le || ze.morphTargets !== Fe || ze.morphNormals !== ke || ze.morphColors !== un || ze.toneMapping !== Cn || xe.isWebGL2 === !0 && ze.morphTargetsCount !== Dt) && (He = !0) : (He = !0, ze.__version = W.version);
    let yt = ze.currentProgram;
    He === !0 && (yt = Zi(W, U, K));
    let tn = !1, Jn = !1, $i = !1;
    const ot = yt.getUniforms(), Qn = ze.uniforms;
    if (ue.useProgram(yt.program) && (tn = !0, Jn = !0, $i = !0), W.id !== x && (x = W.id, Jn = !0), tn || M !== T) {
      if (ot.setValue($, "projectionMatrix", T.projectionMatrix), xe.logarithmicDepthBuffer && ot.setValue(
        $,
        "logDepthBufFC",
        2 / (Math.log(T.far + 1) / Math.LN2)
      ), M !== T && (M = T, Jn = !0, $i = !0), W.isShaderMaterial || W.isMeshPhongMaterial || W.isMeshToonMaterial || W.isMeshStandardMaterial || W.envMap) {
        const dt = ot.map.cameraPosition;
        dt !== void 0 && dt.setValue(
          $,
          ee.setFromMatrixPosition(T.matrixWorld)
        );
      }
      (W.isMeshPhongMaterial || W.isMeshToonMaterial || W.isMeshLambertMaterial || W.isMeshBasicMaterial || W.isMeshStandardMaterial || W.isShaderMaterial) && ot.setValue($, "isOrthographic", T.isOrthographicCamera === !0), (W.isMeshPhongMaterial || W.isMeshToonMaterial || W.isMeshLambertMaterial || W.isMeshBasicMaterial || W.isMeshStandardMaterial || W.isShaderMaterial || W.isShadowMaterial || K.isSkinnedMesh) && ot.setValue($, "viewMatrix", T.matrixWorldInverse);
    }
    if (K.isSkinnedMesh) {
      ot.setOptional($, K, "bindMatrix"), ot.setOptional($, K, "bindMatrixInverse");
      const dt = K.skeleton;
      dt && (xe.floatVertexTextures ? (dt.boneTexture === null && dt.computeBoneTexture(), ot.setValue($, "boneTexture", dt.boneTexture, me), ot.setValue($, "boneTextureSize", dt.boneTextureSize)) : console.warn("THREE.WebGLRenderer: SkinnedMesh can only be used with WebGL 2. With WebGL 1 OES_texture_float and vertex textures support is required."));
    }
    const Ki = X.morphAttributes;
    if ((Ki.position !== void 0 || Ki.normal !== void 0 || Ki.color !== void 0 && xe.isWebGL2 === !0) && te.update(K, X, W, yt), (Jn || ze.receiveShadow !== K.receiveShadow) && (ze.receiveShadow = K.receiveShadow, ot.setValue($, "receiveShadow", K.receiveShadow)), Jn && (ot.setValue($, "toneMappingExposure", p.toneMappingExposure), ze.needsLights && Do(Qn, $i), _e && W.fog === !0 && Gt.refreshFogUniforms(Qn, _e), Gt.refreshMaterialUniforms(Qn, W, P, F, H), Vi.upload($, ze.uniformsList, Qn, me)), W.isShaderMaterial && W.uniformsNeedUpdate === !0 && (Vi.upload($, ze.uniformsList, Qn, me), W.uniformsNeedUpdate = !1), W.isSpriteMaterial && ot.setValue($, "center", K.center), ot.setValue($, "modelViewMatrix", K.modelViewMatrix), ot.setValue($, "normalMatrix", K.normalMatrix), ot.setValue($, "modelMatrix", K.matrixWorld), W.isShaderMaterial || W.isRawShaderMaterial) {
      const dt = W.uniformsGroups;
      for (let Ji = 0, Io = dt.length; Ji < Io; Ji++)
        if (xe.isWebGL2) {
          const js = dt[Ji];
          he.update(js, yt), he.bind(js, yt);
        } else
          console.warn("THREE.WebGLRenderer: Uniform Buffer Objects can only be used with WebGL 2.");
    }
    return yt;
  }
  function Do(T, U) {
    T.ambientLightColor.needsUpdate = U, T.lightProbe.needsUpdate = U, T.directionalLights.needsUpdate = U, T.directionalLightShadows.needsUpdate = U, T.pointLights.needsUpdate = U, T.pointLightShadows.needsUpdate = U, T.spotLights.needsUpdate = U, T.spotLightShadows.needsUpdate = U, T.rectAreaLights.needsUpdate = U, T.hemisphereLights.needsUpdate = U;
  }
  function Po(T) {
    return T.isMeshLambertMaterial || T.isMeshToonMaterial || T.isMeshPhongMaterial || T.isMeshStandardMaterial || T.isShadowMaterial || T.isShaderMaterial && T.lights === !0;
  }
  this.getActiveCubeFace = function() {
    return v;
  }, this.getActiveMipmapLevel = function() {
    return _;
  }, this.getRenderTarget = function() {
    return w;
  }, this.setRenderTargetTextures = function(T, U, X) {
    Ee.get(T.texture).__webglTexture = U, Ee.get(T.depthTexture).__webglTexture = X;
    const W = Ee.get(T);
    W.__hasExternalTextures = !0, W.__hasExternalTextures && (W.__autoAllocateDepthBuffer = X === void 0, W.__autoAllocateDepthBuffer || ve.has("WEBGL_multisampled_render_to_texture") === !0 && (console.warn("THREE.WebGLRenderer: Render-to-texture extension was disabled because an external texture was provided"), W.__useRenderToTexture = !1));
  }, this.setRenderTargetFramebuffer = function(T, U) {
    const X = Ee.get(T);
    X.__webglFramebuffer = U, X.__useDefaultFramebuffer = U === void 0;
  }, this.setRenderTarget = function(T, U = 0, X = 0) {
    w = T, v = U, _ = X;
    let W = !0;
    if (T) {
      const Me = Ee.get(T);
      Me.__useDefaultFramebuffer !== void 0 ? (ue.bindFramebuffer(36160, null), W = !1) : Me.__webglFramebuffer === void 0 ? me.setupRenderTarget(T) : Me.__hasExternalTextures && me.rebindTextures(T, Ee.get(T.texture).__webglTexture, Ee.get(T.depthTexture).__webglTexture);
    }
    let K = null, _e = !1, be = !1;
    if (T) {
      const Me = T.texture;
      (Me.isData3DTexture || Me.isDataArrayTexture) && (be = !0);
      const Be = Ee.get(T).__webglFramebuffer;
      T.isWebGLCubeRenderTarget ? (K = Be[U], _e = !0) : xe.isWebGL2 && T.samples > 0 && me.useMultisampledRTT(T) === !1 ? K = Ee.get(T).__webglMultisampledFramebuffer : K = Be, E.copy(T.viewport), R.copy(T.scissor), y = T.scissorTest;
    } else
      E.copy(L).multiplyScalar(P).floor(), R.copy(I).multiplyScalar(P).floor(), y = D;
    if (ue.bindFramebuffer(36160, K) && xe.drawBuffers && W && ue.drawBuffers(T, K), ue.viewport(E), ue.scissor(R), ue.setScissorTest(y), _e) {
      const Me = Ee.get(T.texture);
      $.framebufferTexture2D(36160, 36064, 34069 + U, Me.__webglTexture, X);
    } else if (be) {
      const Me = Ee.get(T.texture), Be = U || 0;
      $.framebufferTextureLayer(36160, 36064, Me.__webglTexture, X || 0, Be);
    }
    x = -1;
  }, this.readRenderTargetPixels = function(T, U, X, W, K, _e, be) {
    if (!(T && T.isWebGLRenderTarget)) {
      console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");
      return;
    }
    let Se = Ee.get(T).__webglFramebuffer;
    if (T.isWebGLCubeRenderTarget && be !== void 0 && (Se = Se[be]), Se) {
      ue.bindFramebuffer(36160, Se);
      try {
        const Me = T.texture, Be = Me.format, Le = Me.type;
        if (Be !== 1023 && j.convert(Be) !== $.getParameter(35739)) {
          console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");
          return;
        }
        const Fe = Le === 1016 && (ve.has("EXT_color_buffer_half_float") || xe.isWebGL2 && ve.has("EXT_color_buffer_float"));
        if (Le !== 1009 && j.convert(Le) !== $.getParameter(35738) && !(Le === 1015 && (xe.isWebGL2 || ve.has("OES_texture_float") || ve.has("WEBGL_color_buffer_float"))) && !Fe) {
          console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");
          return;
        }
        U >= 0 && U <= T.width - W && X >= 0 && X <= T.height - K && $.readPixels(U, X, W, K, j.convert(Be), j.convert(Le), _e);
      } finally {
        const Me = w !== null ? Ee.get(w).__webglFramebuffer : null;
        ue.bindFramebuffer(36160, Me);
      }
    }
  }, this.copyFramebufferToTexture = function(T, U, X = 0) {
    const W = Math.pow(2, -X), K = Math.floor(U.image.width * W), _e = Math.floor(U.image.height * W);
    me.setTexture2D(U, 0), $.copyTexSubImage2D(3553, X, 0, 0, T.x, T.y, K, _e), ue.unbindTexture();
  }, this.copyTextureToTexture = function(T, U, X, W = 0) {
    const K = U.image.width, _e = U.image.height, be = j.convert(X.format), Se = j.convert(X.type);
    me.setTexture2D(X, 0), $.pixelStorei(37440, X.flipY), $.pixelStorei(37441, X.premultiplyAlpha), $.pixelStorei(3317, X.unpackAlignment), U.isDataTexture ? $.texSubImage2D(3553, W, T.x, T.y, K, _e, be, Se, U.image.data) : U.isCompressedTexture ? $.compressedTexSubImage2D(3553, W, T.x, T.y, U.mipmaps[0].width, U.mipmaps[0].height, be, U.mipmaps[0].data) : $.texSubImage2D(3553, W, T.x, T.y, be, Se, U.image), W === 0 && X.generateMipmaps && $.generateMipmap(3553), ue.unbindTexture();
  }, this.copyTextureToTexture3D = function(T, U, X, W, K = 0) {
    if (p.isWebGL1Renderer) {
      console.warn("THREE.WebGLRenderer.copyTextureToTexture3D: can only be used with WebGL2.");
      return;
    }
    const _e = T.max.x - T.min.x + 1, be = T.max.y - T.min.y + 1, Se = T.max.z - T.min.z + 1, Me = j.convert(W.format), Be = j.convert(W.type);
    let Le;
    if (W.isData3DTexture)
      me.setTexture3D(W, 0), Le = 32879;
    else if (W.isDataArrayTexture)
      me.setTexture2DArray(W, 0), Le = 35866;
    else {
      console.warn("THREE.WebGLRenderer.copyTextureToTexture3D: only supports THREE.DataTexture3D and THREE.DataTexture2DArray.");
      return;
    }
    $.pixelStorei(37440, W.flipY), $.pixelStorei(37441, W.premultiplyAlpha), $.pixelStorei(3317, W.unpackAlignment);
    const Fe = $.getParameter(3314), ke = $.getParameter(32878), un = $.getParameter(3316), Cn = $.getParameter(3315), Ln = $.getParameter(32877), Dt = X.isCompressedTexture ? X.mipmaps[0] : X.image;
    $.pixelStorei(3314, Dt.width), $.pixelStorei(32878, Dt.height), $.pixelStorei(3316, T.min.x), $.pixelStorei(3315, T.min.y), $.pixelStorei(32877, T.min.z), X.isDataTexture || X.isData3DTexture ? $.texSubImage3D(Le, K, U.x, U.y, U.z, _e, be, Se, Me, Be, Dt.data) : X.isCompressedTexture ? (console.warn("THREE.WebGLRenderer.copyTextureToTexture3D: untested support for compressed srcTexture."), $.compressedTexSubImage3D(Le, K, U.x, U.y, U.z, _e, be, Se, Me, Dt.data)) : $.texSubImage3D(Le, K, U.x, U.y, U.z, _e, be, Se, Me, Be, Dt), $.pixelStorei(3314, Fe), $.pixelStorei(32878, ke), $.pixelStorei(3316, un), $.pixelStorei(3315, Cn), $.pixelStorei(32877, Ln), K === 0 && W.generateMipmaps && $.generateMipmap(Le), ue.unbindTexture();
  }, this.initTexture = function(T) {
    T.isCubeTexture ? me.setTextureCube(T, 0) : T.isData3DTexture ? me.setTexture3D(T, 0) : T.isDataArrayTexture ? me.setTexture2DArray(T, 0) : me.setTexture2D(T, 0), ue.unbindTexture();
  }, this.resetState = function() {
    v = 0, _ = 0, w = null, ue.reset(), pe.reset();
  }, typeof __THREE_DEVTOOLS__ < "u" && __THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe", { detail: this }));
}
class Bu extends xo {
}
Bu.prototype.isWebGL1Renderer = !0;
class Nu extends at {
  constructor() {
    super(), this.isScene = !0, this.type = "Scene", this.background = null, this.environment = null, this.fog = null, this.overrideMaterial = null, this.autoUpdate = !0, typeof __THREE_DEVTOOLS__ < "u" && __THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe", { detail: this }));
  }
  copy(e, t) {
    return super.copy(e, t), e.background !== null && (this.background = e.background.clone()), e.environment !== null && (this.environment = e.environment.clone()), e.fog !== null && (this.fog = e.fog.clone()), e.overrideMaterial !== null && (this.overrideMaterial = e.overrideMaterial.clone()), this.autoUpdate = e.autoUpdate, this.matrixAutoUpdate = e.matrixAutoUpdate, this;
  }
  toJSON(e) {
    const t = super.toJSON(e);
    return this.fog !== null && (t.object.fog = this.fog.toJSON()), t;
  }
}
class Rr extends _t {
  constructor(e, t, n, i, s, o, r, l, a) {
    super(e, t, n, i, s, o, r, l, a), this.isCanvasTexture = !0, this.needsUpdate = !0;
  }
}
class ks extends Ut {
  constructor(e = 1, t = 1, n = 1, i = 8, s = 1, o = !1, r = 0, l = Math.PI * 2) {
    super(), this.type = "CylinderGeometry", this.parameters = {
      radiusTop: e,
      radiusBottom: t,
      height: n,
      radialSegments: i,
      heightSegments: s,
      openEnded: o,
      thetaStart: r,
      thetaLength: l
    };
    const a = this;
    i = Math.floor(i), s = Math.floor(s);
    const c = [], d = [], u = [], m = [];
    let g = 0;
    const p = [], f = n / 2;
    let v = 0;
    _(), o === !1 && (e > 0 && w(!0), t > 0 && w(!1)), this.setIndex(c), this.setAttribute("position", new st(d, 3)), this.setAttribute("normal", new st(u, 3)), this.setAttribute("uv", new st(m, 2));
    function _() {
      const x = new O(), M = new O();
      let E = 0;
      const R = (t - e) / n;
      for (let y = 0; y <= s; y++) {
        const A = [], F = y / s, P = F * (t - e) + e;
        for (let G = 0; G <= i; G++) {
          const z = G / i, L = z * l + r, I = Math.sin(L), D = Math.cos(L);
          M.x = P * I, M.y = -F * n + f, M.z = P * D, d.push(M.x, M.y, M.z), x.set(I, R, D).normalize(), u.push(x.x, x.y, x.z), m.push(z, 1 - F), A.push(g++);
        }
        p.push(A);
      }
      for (let y = 0; y < i; y++)
        for (let A = 0; A < s; A++) {
          const F = p[A][y], P = p[A + 1][y], G = p[A + 1][y + 1], z = p[A][y + 1];
          c.push(F, P, z), c.push(P, G, z), E += 6;
        }
      a.addGroup(v, E, 0), v += E;
    }
    function w(x) {
      const M = g, E = new Ce(), R = new O();
      let y = 0;
      const A = x === !0 ? e : t, F = x === !0 ? 1 : -1;
      for (let G = 1; G <= i; G++)
        d.push(0, f * F, 0), u.push(0, F, 0), m.push(0.5, 0.5), g++;
      const P = g;
      for (let G = 0; G <= i; G++) {
        const L = G / i * l + r, I = Math.cos(L), D = Math.sin(L);
        R.x = A * D, R.y = f * F, R.z = A * I, d.push(R.x, R.y, R.z), u.push(0, F, 0), E.x = I * 0.5 + 0.5, E.y = D * 0.5 * F + 0.5, m.push(E.x, E.y), g++;
      }
      for (let G = 0; G < i; G++) {
        const z = M + G, L = P + G;
        x === !0 ? c.push(L, L + 1, z) : c.push(L + 1, L, z), y += 3;
      }
      a.addGroup(v, y, x === !0 ? 1 : 2), v += y;
    }
  }
  static fromJSON(e) {
    return new ks(e.radiusTop, e.radiusBottom, e.height, e.radialSegments, e.heightSegments, e.openEnded, e.thetaStart, e.thetaLength);
  }
}
class Ou extends An {
  constructor(e) {
    super(), this.isShadowMaterial = !0, this.type = "ShadowMaterial", this.color = new Ae(0), this.transparent = !0, this.fog = !0, this.setValues(e);
  }
  copy(e) {
    return super.copy(e), this.color.copy(e.color), this.fog = e.fog, this;
  }
}
class Uu extends An {
  constructor(e) {
    super(), this.isMeshStandardMaterial = !0, this.defines = { STANDARD: "" }, this.type = "MeshStandardMaterial", this.color = new Ae(16777215), this.roughness = 1, this.metalness = 0, this.map = null, this.lightMap = null, this.lightMapIntensity = 1, this.aoMap = null, this.aoMapIntensity = 1, this.emissive = new Ae(0), this.emissiveIntensity = 1, this.emissiveMap = null, this.bumpMap = null, this.bumpScale = 1, this.normalMap = null, this.normalMapType = 0, this.normalScale = new Ce(1, 1), this.displacementMap = null, this.displacementScale = 1, this.displacementBias = 0, this.roughnessMap = null, this.metalnessMap = null, this.alphaMap = null, this.envMap = null, this.envMapIntensity = 1, this.wireframe = !1, this.wireframeLinewidth = 1, this.wireframeLinecap = "round", this.wireframeLinejoin = "round", this.flatShading = !1, this.fog = !0, this.setValues(e);
  }
  copy(e) {
    return super.copy(e), this.defines = { STANDARD: "" }, this.color.copy(e.color), this.roughness = e.roughness, this.metalness = e.metalness, this.map = e.map, this.lightMap = e.lightMap, this.lightMapIntensity = e.lightMapIntensity, this.aoMap = e.aoMap, this.aoMapIntensity = e.aoMapIntensity, this.emissive.copy(e.emissive), this.emissiveMap = e.emissiveMap, this.emissiveIntensity = e.emissiveIntensity, this.bumpMap = e.bumpMap, this.bumpScale = e.bumpScale, this.normalMap = e.normalMap, this.normalMapType = e.normalMapType, this.normalScale.copy(e.normalScale), this.displacementMap = e.displacementMap, this.displacementScale = e.displacementScale, this.displacementBias = e.displacementBias, this.roughnessMap = e.roughnessMap, this.metalnessMap = e.metalnessMap, this.alphaMap = e.alphaMap, this.envMap = e.envMap, this.envMapIntensity = e.envMapIntensity, this.wireframe = e.wireframe, this.wireframeLinewidth = e.wireframeLinewidth, this.wireframeLinecap = e.wireframeLinecap, this.wireframeLinejoin = e.wireframeLinejoin, this.flatShading = e.flatShading, this.fog = e.fog, this;
  }
}
class Gu extends An {
  constructor(e) {
    super(), this.isMeshPhongMaterial = !0, this.type = "MeshPhongMaterial", this.color = new Ae(16777215), this.specular = new Ae(1118481), this.shininess = 30, this.map = null, this.lightMap = null, this.lightMapIntensity = 1, this.aoMap = null, this.aoMapIntensity = 1, this.emissive = new Ae(0), this.emissiveIntensity = 1, this.emissiveMap = null, this.bumpMap = null, this.bumpScale = 1, this.normalMap = null, this.normalMapType = 0, this.normalScale = new Ce(1, 1), this.displacementMap = null, this.displacementScale = 1, this.displacementBias = 0, this.specularMap = null, this.alphaMap = null, this.envMap = null, this.combine = 0, this.reflectivity = 1, this.refractionRatio = 0.98, this.wireframe = !1, this.wireframeLinewidth = 1, this.wireframeLinecap = "round", this.wireframeLinejoin = "round", this.flatShading = !1, this.fog = !0, this.setValues(e);
  }
  copy(e) {
    return super.copy(e), this.color.copy(e.color), this.specular.copy(e.specular), this.shininess = e.shininess, this.map = e.map, this.lightMap = e.lightMap, this.lightMapIntensity = e.lightMapIntensity, this.aoMap = e.aoMap, this.aoMapIntensity = e.aoMapIntensity, this.emissive.copy(e.emissive), this.emissiveMap = e.emissiveMap, this.emissiveIntensity = e.emissiveIntensity, this.bumpMap = e.bumpMap, this.bumpScale = e.bumpScale, this.normalMap = e.normalMap, this.normalMapType = e.normalMapType, this.normalScale.copy(e.normalScale), this.displacementMap = e.displacementMap, this.displacementScale = e.displacementScale, this.displacementBias = e.displacementBias, this.specularMap = e.specularMap, this.alphaMap = e.alphaMap, this.envMap = e.envMap, this.combine = e.combine, this.reflectivity = e.reflectivity, this.refractionRatio = e.refractionRatio, this.wireframe = e.wireframe, this.wireframeLinewidth = e.wireframeLinewidth, this.wireframeLinecap = e.wireframeLinecap, this.wireframeLinejoin = e.wireframeLinejoin, this.flatShading = e.flatShading, this.fog = e.fog, this;
  }
}
class yo extends at {
  constructor(e, t = 1) {
    super(), this.isLight = !0, this.type = "Light", this.color = new Ae(e), this.intensity = t;
  }
  dispose() {
  }
  copy(e, t) {
    return super.copy(e, t), this.color.copy(e.color), this.intensity = e.intensity, this;
  }
  toJSON(e) {
    const t = super.toJSON(e);
    return t.object.color = this.color.getHex(), t.object.intensity = this.intensity, this.groundColor !== void 0 && (t.object.groundColor = this.groundColor.getHex()), this.distance !== void 0 && (t.object.distance = this.distance), this.angle !== void 0 && (t.object.angle = this.angle), this.decay !== void 0 && (t.object.decay = this.decay), this.penumbra !== void 0 && (t.object.penumbra = this.penumbra), this.shadow !== void 0 && (t.object.shadow = this.shadow.toJSON()), t;
  }
}
class ku extends yo {
  constructor(e, t, n) {
    super(e, n), this.isHemisphereLight = !0, this.type = "HemisphereLight", this.position.copy(at.DefaultUp), this.updateMatrix(), this.groundColor = new Ae(t);
  }
  copy(e, t) {
    return super.copy(e, t), this.groundColor.copy(e.groundColor), this;
  }
}
const Fr = /* @__PURE__ */ new Ke(), Dr = /* @__PURE__ */ new O(), Pr = /* @__PURE__ */ new O();
class Wu {
  constructor(e) {
    this.camera = e, this.bias = 0, this.normalBias = 0, this.radius = 1, this.blurSamples = 8, this.mapSize = new Ce(512, 512), this.map = null, this.mapPass = null, this.matrix = new Ke(), this.autoUpdate = !0, this.needsUpdate = !1, this._frustum = new Us(), this._frameExtents = new Ce(1, 1), this._viewportCount = 1, this._viewports = [
      new $e(0, 0, 1, 1)
    ];
  }
  getViewportCount() {
    return this._viewportCount;
  }
  getFrustum() {
    return this._frustum;
  }
  updateMatrices(e) {
    const t = this.camera, n = this.matrix;
    Dr.setFromMatrixPosition(e.matrixWorld), t.position.copy(Dr), Pr.setFromMatrixPosition(e.target.matrixWorld), t.lookAt(Pr), t.updateMatrixWorld(), Fr.multiplyMatrices(t.projectionMatrix, t.matrixWorldInverse), this._frustum.setFromProjectionMatrix(Fr), n.set(
      0.5,
      0,
      0,
      0.5,
      0,
      0.5,
      0,
      0.5,
      0,
      0,
      0.5,
      0.5,
      0,
      0,
      0,
      1
    ), n.multiply(t.projectionMatrix), n.multiply(t.matrixWorldInverse);
  }
  getViewport(e) {
    return this._viewports[e];
  }
  getFrameExtents() {
    return this._frameExtents;
  }
  dispose() {
    this.map && this.map.dispose(), this.mapPass && this.mapPass.dispose();
  }
  copy(e) {
    return this.camera = e.camera.clone(), this.bias = e.bias, this.radius = e.radius, this.mapSize.copy(e.mapSize), this;
  }
  clone() {
    return new this.constructor().copy(this);
  }
  toJSON() {
    const e = {};
    return this.bias !== 0 && (e.bias = this.bias), this.normalBias !== 0 && (e.normalBias = this.normalBias), this.radius !== 1 && (e.radius = this.radius), (this.mapSize.x !== 512 || this.mapSize.y !== 512) && (e.mapSize = this.mapSize.toArray()), e.camera = this.camera.toJSON(!1).object, delete e.camera.matrix, e;
  }
}
class Vu extends Wu {
  constructor() {
    super(new gt(50, 1, 0.5, 500)), this.isSpotLightShadow = !0, this.focus = 1;
  }
  updateMatrices(e) {
    const t = this.camera, n = zs * 2 * e.angle * this.focus, i = this.mapSize.width / this.mapSize.height, s = e.distance || t.far;
    (n !== t.fov || i !== t.aspect || s !== t.far) && (t.fov = n, t.aspect = i, t.far = s, t.updateProjectionMatrix()), super.updateMatrices(e);
  }
  copy(e) {
    return super.copy(e), this.focus = e.focus, this;
  }
}
class Hu extends yo {
  constructor(e, t, n = 0, i = Math.PI / 3, s = 0, o = 1) {
    super(e, t), this.isSpotLight = !0, this.type = "SpotLight", this.position.copy(at.DefaultUp), this.updateMatrix(), this.target = new at(), this.distance = n, this.angle = i, this.penumbra = s, this.decay = o, this.shadow = new Vu();
  }
  get power() {
    return this.intensity * Math.PI;
  }
  set power(e) {
    this.intensity = e / Math.PI;
  }
  dispose() {
    this.shadow.dispose();
  }
  copy(e, t) {
    return super.copy(e, t), this.distance = e.distance, this.angle = e.angle, this.penumbra = e.penumbra, this.decay = e.decay, this.target = e.target.clone(), this.shadow = e.shadow.clone(), this;
  }
}
typeof __THREE_DEVTOOLS__ < "u" && __THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register", { detail: {
  revision: Os
} }));
typeof window < "u" && (window.__THREE__ ? console.warn("WARNING: Multiple instances of Three.js being imported.") : window.__THREE__ = Os);
class Lt {
  constructor(e) {
    e === void 0 && (e = [0, 0, 0, 0, 0, 0, 0, 0, 0]), this.elements = e;
  }
  identity() {
    const e = this.elements;
    e[0] = 1, e[1] = 0, e[2] = 0, e[3] = 0, e[4] = 1, e[5] = 0, e[6] = 0, e[7] = 0, e[8] = 1;
  }
  setZero() {
    const e = this.elements;
    e[0] = 0, e[1] = 0, e[2] = 0, e[3] = 0, e[4] = 0, e[5] = 0, e[6] = 0, e[7] = 0, e[8] = 0;
  }
  setTrace(e) {
    const t = this.elements;
    t[0] = e.x, t[4] = e.y, t[8] = e.z;
  }
  getTrace(e) {
    e === void 0 && (e = new b());
    const t = this.elements;
    return e.x = t[0], e.y = t[4], e.z = t[8], e;
  }
  vmult(e, t) {
    t === void 0 && (t = new b());
    const n = this.elements, i = e.x, s = e.y, o = e.z;
    return t.x = n[0] * i + n[1] * s + n[2] * o, t.y = n[3] * i + n[4] * s + n[5] * o, t.z = n[6] * i + n[7] * s + n[8] * o, t;
  }
  smult(e) {
    for (let t = 0; t < this.elements.length; t++)
      this.elements[t] *= e;
  }
  mmult(e, t) {
    t === void 0 && (t = new Lt());
    const n = this.elements, i = e.elements, s = t.elements, o = n[0], r = n[1], l = n[2], a = n[3], c = n[4], d = n[5], u = n[6], m = n[7], g = n[8], p = i[0], f = i[1], v = i[2], _ = i[3], w = i[4], x = i[5], M = i[6], E = i[7], R = i[8];
    return s[0] = o * p + r * _ + l * M, s[1] = o * f + r * w + l * E, s[2] = o * v + r * x + l * R, s[3] = a * p + c * _ + d * M, s[4] = a * f + c * w + d * E, s[5] = a * v + c * x + d * R, s[6] = u * p + m * _ + g * M, s[7] = u * f + m * w + g * E, s[8] = u * v + m * x + g * R, t;
  }
  scale(e, t) {
    t === void 0 && (t = new Lt());
    const n = this.elements, i = t.elements;
    for (let s = 0; s !== 3; s++)
      i[3 * s + 0] = e.x * n[3 * s + 0], i[3 * s + 1] = e.y * n[3 * s + 1], i[3 * s + 2] = e.z * n[3 * s + 2];
    return t;
  }
  solve(e, t) {
    t === void 0 && (t = new b());
    const n = 3, i = 4, s = [];
    let o, r;
    for (o = 0; o < n * i; o++)
      s.push(0);
    for (o = 0; o < 3; o++)
      for (r = 0; r < 3; r++)
        s[o + i * r] = this.elements[o + 3 * r];
    s[3 + 4 * 0] = e.x, s[3 + 4 * 1] = e.y, s[3 + 4 * 2] = e.z;
    let l = 3;
    const a = l;
    let c;
    const d = 4;
    let u;
    do {
      if (o = a - l, s[o + i * o] === 0) {
        for (r = o + 1; r < a; r++)
          if (s[o + i * r] !== 0) {
            c = d;
            do
              u = d - c, s[u + i * o] += s[u + i * r];
            while (--c);
            break;
          }
      }
      if (s[o + i * o] !== 0)
        for (r = o + 1; r < a; r++) {
          const m = s[o + i * r] / s[o + i * o];
          c = d;
          do
            u = d - c, s[u + i * r] = u <= o ? 0 : s[u + i * r] - s[u + i * o] * m;
          while (--c);
        }
    } while (--l);
    if (t.z = s[2 * i + 3] / s[2 * i + 2], t.y = (s[1 * i + 3] - s[1 * i + 2] * t.z) / s[1 * i + 1], t.x = (s[0 * i + 3] - s[0 * i + 2] * t.z - s[0 * i + 1] * t.y) / s[0 * i + 0], isNaN(t.x) || isNaN(t.y) || isNaN(t.z) || t.x === 1 / 0 || t.y === 1 / 0 || t.z === 1 / 0)
      throw `Could not solve equation! Got x=[${t.toString()}], b=[${e.toString()}], A=[${this.toString()}]`;
    return t;
  }
  e(e, t, n) {
    if (n === void 0)
      return this.elements[t + 3 * e];
    this.elements[t + 3 * e] = n;
  }
  copy(e) {
    for (let t = 0; t < e.elements.length; t++)
      this.elements[t] = e.elements[t];
    return this;
  }
  toString() {
    let e = "";
    const t = ",";
    for (let n = 0; n < 9; n++)
      e += this.elements[n] + t;
    return e;
  }
  reverse(e) {
    e === void 0 && (e = new Lt());
    const t = 3, n = 6, i = qu;
    let s, o;
    for (s = 0; s < 3; s++)
      for (o = 0; o < 3; o++)
        i[s + n * o] = this.elements[s + 3 * o];
    i[3 + 6 * 0] = 1, i[3 + 6 * 1] = 0, i[3 + 6 * 2] = 0, i[4 + 6 * 0] = 0, i[4 + 6 * 1] = 1, i[4 + 6 * 2] = 0, i[5 + 6 * 0] = 0, i[5 + 6 * 1] = 0, i[5 + 6 * 2] = 1;
    let r = 3;
    const l = r;
    let a;
    const c = n;
    let d;
    do {
      if (s = l - r, i[s + n * s] === 0) {
        for (o = s + 1; o < l; o++)
          if (i[s + n * o] !== 0) {
            a = c;
            do
              d = c - a, i[d + n * s] += i[d + n * o];
            while (--a);
            break;
          }
      }
      if (i[s + n * s] !== 0)
        for (o = s + 1; o < l; o++) {
          const u = i[s + n * o] / i[s + n * s];
          a = c;
          do
            d = c - a, i[d + n * o] = d <= s ? 0 : i[d + n * o] - i[d + n * s] * u;
          while (--a);
        }
    } while (--r);
    s = 2;
    do {
      o = s - 1;
      do {
        const u = i[s + n * o] / i[s + n * s];
        a = n;
        do
          d = n - a, i[d + n * o] = i[d + n * o] - i[d + n * s] * u;
        while (--a);
      } while (o--);
    } while (--s);
    s = 2;
    do {
      const u = 1 / i[s + n * s];
      a = n;
      do
        d = n - a, i[d + n * s] = i[d + n * s] * u;
      while (--a);
    } while (s--);
    s = 2;
    do {
      o = 2;
      do {
        if (d = i[t + o + n * s], isNaN(d) || d === 1 / 0)
          throw `Could not reverse! A=[${this.toString()}]`;
        e.e(s, o, d);
      } while (o--);
    } while (s--);
    return e;
  }
  setRotationFromQuaternion(e) {
    const t = e.x, n = e.y, i = e.z, s = e.w, o = t + t, r = n + n, l = i + i, a = t * o, c = t * r, d = t * l, u = n * r, m = n * l, g = i * l, p = s * o, f = s * r, v = s * l, _ = this.elements;
    return _[3 * 0 + 0] = 1 - (u + g), _[3 * 0 + 1] = c - v, _[3 * 0 + 2] = d + f, _[3 * 1 + 0] = c + v, _[3 * 1 + 1] = 1 - (a + g), _[3 * 1 + 2] = m - p, _[3 * 2 + 0] = d - f, _[3 * 2 + 1] = m + p, _[3 * 2 + 2] = 1 - (a + u), this;
  }
  transpose(e) {
    e === void 0 && (e = new Lt());
    const t = this.elements, n = e.elements;
    let i;
    return n[0] = t[0], n[4] = t[4], n[8] = t[8], i = t[1], n[1] = t[3], n[3] = i, i = t[2], n[2] = t[6], n[6] = i, i = t[5], n[5] = t[7], n[7] = i, e;
  }
}
const qu = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
class b {
  constructor(e, t, n) {
    e === void 0 && (e = 0), t === void 0 && (t = 0), n === void 0 && (n = 0), this.x = e, this.y = t, this.z = n;
  }
  cross(e, t) {
    t === void 0 && (t = new b());
    const n = e.x, i = e.y, s = e.z, o = this.x, r = this.y, l = this.z;
    return t.x = r * s - l * i, t.y = l * n - o * s, t.z = o * i - r * n, t;
  }
  set(e, t, n) {
    return this.x = e, this.y = t, this.z = n, this;
  }
  setZero() {
    this.x = this.y = this.z = 0;
  }
  vadd(e, t) {
    if (t)
      t.x = e.x + this.x, t.y = e.y + this.y, t.z = e.z + this.z;
    else
      return new b(this.x + e.x, this.y + e.y, this.z + e.z);
  }
  vsub(e, t) {
    if (t)
      t.x = this.x - e.x, t.y = this.y - e.y, t.z = this.z - e.z;
    else
      return new b(this.x - e.x, this.y - e.y, this.z - e.z);
  }
  crossmat() {
    return new Lt([0, -this.z, this.y, this.z, 0, -this.x, -this.y, this.x, 0]);
  }
  normalize() {
    const e = this.x, t = this.y, n = this.z, i = Math.sqrt(e * e + t * t + n * n);
    if (i > 0) {
      const s = 1 / i;
      this.x *= s, this.y *= s, this.z *= s;
    } else
      this.x = 0, this.y = 0, this.z = 0;
    return i;
  }
  unit(e) {
    e === void 0 && (e = new b());
    const t = this.x, n = this.y, i = this.z;
    let s = Math.sqrt(t * t + n * n + i * i);
    return s > 0 ? (s = 1 / s, e.x = t * s, e.y = n * s, e.z = i * s) : (e.x = 1, e.y = 0, e.z = 0), e;
  }
  length() {
    const e = this.x, t = this.y, n = this.z;
    return Math.sqrt(e * e + t * t + n * n);
  }
  lengthSquared() {
    return this.dot(this);
  }
  distanceTo(e) {
    const t = this.x, n = this.y, i = this.z, s = e.x, o = e.y, r = e.z;
    return Math.sqrt((s - t) * (s - t) + (o - n) * (o - n) + (r - i) * (r - i));
  }
  distanceSquared(e) {
    const t = this.x, n = this.y, i = this.z, s = e.x, o = e.y, r = e.z;
    return (s - t) * (s - t) + (o - n) * (o - n) + (r - i) * (r - i);
  }
  scale(e, t) {
    t === void 0 && (t = new b());
    const n = this.x, i = this.y, s = this.z;
    return t.x = e * n, t.y = e * i, t.z = e * s, t;
  }
  vmul(e, t) {
    return t === void 0 && (t = new b()), t.x = e.x * this.x, t.y = e.y * this.y, t.z = e.z * this.z, t;
  }
  addScaledVector(e, t, n) {
    return n === void 0 && (n = new b()), n.x = this.x + e * t.x, n.y = this.y + e * t.y, n.z = this.z + e * t.z, n;
  }
  dot(e) {
    return this.x * e.x + this.y * e.y + this.z * e.z;
  }
  isZero() {
    return this.x === 0 && this.y === 0 && this.z === 0;
  }
  negate(e) {
    return e === void 0 && (e = new b()), e.x = -this.x, e.y = -this.y, e.z = -this.z, e;
  }
  tangents(e, t) {
    const n = this.length();
    if (n > 0) {
      const i = Xu, s = 1 / n;
      i.set(this.x * s, this.y * s, this.z * s);
      const o = ju;
      Math.abs(i.x) < 0.9 ? (o.set(1, 0, 0), i.cross(o, e)) : (o.set(0, 1, 0), i.cross(o, e)), i.cross(e, t);
    } else
      e.set(1, 0, 0), t.set(0, 1, 0);
  }
  toString() {
    return `${this.x},${this.y},${this.z}`;
  }
  toArray() {
    return [this.x, this.y, this.z];
  }
  copy(e) {
    return this.x = e.x, this.y = e.y, this.z = e.z, this;
  }
  lerp(e, t, n) {
    const i = this.x, s = this.y, o = this.z;
    n.x = i + (e.x - i) * t, n.y = s + (e.y - s) * t, n.z = o + (e.z - o) * t;
  }
  almostEquals(e, t) {
    return t === void 0 && (t = 1e-6), !(Math.abs(this.x - e.x) > t || Math.abs(this.y - e.y) > t || Math.abs(this.z - e.z) > t);
  }
  almostZero(e) {
    return e === void 0 && (e = 1e-6), !(Math.abs(this.x) > e || Math.abs(this.y) > e || Math.abs(this.z) > e);
  }
  isAntiparallelTo(e, t) {
    return this.negate(Ir), Ir.almostEquals(e, t);
  }
  clone() {
    return new b(this.x, this.y, this.z);
  }
}
b.ZERO = new b(0, 0, 0);
b.UNIT_X = new b(1, 0, 0);
b.UNIT_Y = new b(0, 1, 0);
b.UNIT_Z = new b(0, 0, 1);
const Xu = new b(), ju = new b(), Ir = new b();
class vt {
  constructor(e) {
    e === void 0 && (e = {}), this.lowerBound = new b(), this.upperBound = new b(), e.lowerBound && this.lowerBound.copy(e.lowerBound), e.upperBound && this.upperBound.copy(e.upperBound);
  }
  setFromPoints(e, t, n, i) {
    const s = this.lowerBound, o = this.upperBound, r = n;
    s.copy(e[0]), r && r.vmult(s, s), o.copy(s);
    for (let l = 1; l < e.length; l++) {
      let a = e[l];
      r && (r.vmult(a, zr), a = zr), a.x > o.x && (o.x = a.x), a.x < s.x && (s.x = a.x), a.y > o.y && (o.y = a.y), a.y < s.y && (s.y = a.y), a.z > o.z && (o.z = a.z), a.z < s.z && (s.z = a.z);
    }
    return t && (t.vadd(s, s), t.vadd(o, o)), i && (s.x -= i, s.y -= i, s.z -= i, o.x += i, o.y += i, o.z += i), this;
  }
  copy(e) {
    return this.lowerBound.copy(e.lowerBound), this.upperBound.copy(e.upperBound), this;
  }
  clone() {
    return new vt().copy(this);
  }
  extend(e) {
    this.lowerBound.x = Math.min(this.lowerBound.x, e.lowerBound.x), this.upperBound.x = Math.max(this.upperBound.x, e.upperBound.x), this.lowerBound.y = Math.min(this.lowerBound.y, e.lowerBound.y), this.upperBound.y = Math.max(this.upperBound.y, e.upperBound.y), this.lowerBound.z = Math.min(this.lowerBound.z, e.lowerBound.z), this.upperBound.z = Math.max(this.upperBound.z, e.upperBound.z);
  }
  overlaps(e) {
    const t = this.lowerBound, n = this.upperBound, i = e.lowerBound, s = e.upperBound, o = i.x <= n.x && n.x <= s.x || t.x <= s.x && s.x <= n.x, r = i.y <= n.y && n.y <= s.y || t.y <= s.y && s.y <= n.y, l = i.z <= n.z && n.z <= s.z || t.z <= s.z && s.z <= n.z;
    return o && r && l;
  }
  volume() {
    const e = this.lowerBound, t = this.upperBound;
    return (t.x - e.x) * (t.y - e.y) * (t.z - e.z);
  }
  contains(e) {
    const t = this.lowerBound, n = this.upperBound, i = e.lowerBound, s = e.upperBound;
    return t.x <= i.x && n.x >= s.x && t.y <= i.y && n.y >= s.y && t.z <= i.z && n.z >= s.z;
  }
  getCorners(e, t, n, i, s, o, r, l) {
    const a = this.lowerBound, c = this.upperBound;
    e.copy(a), t.set(c.x, a.y, a.z), n.set(c.x, c.y, a.z), i.set(a.x, c.y, c.z), s.set(c.x, a.y, c.z), o.set(a.x, c.y, a.z), r.set(a.x, a.y, c.z), l.copy(c);
  }
  toLocalFrame(e, t) {
    const n = Br, i = n[0], s = n[1], o = n[2], r = n[3], l = n[4], a = n[5], c = n[6], d = n[7];
    this.getCorners(i, s, o, r, l, a, c, d);
    for (let u = 0; u !== 8; u++) {
      const m = n[u];
      e.pointToLocal(m, m);
    }
    return t.setFromPoints(n);
  }
  toWorldFrame(e, t) {
    const n = Br, i = n[0], s = n[1], o = n[2], r = n[3], l = n[4], a = n[5], c = n[6], d = n[7];
    this.getCorners(i, s, o, r, l, a, c, d);
    for (let u = 0; u !== 8; u++) {
      const m = n[u];
      e.pointToWorld(m, m);
    }
    return t.setFromPoints(n);
  }
  overlapsRay(e) {
    const {
      direction: t,
      from: n
    } = e, i = 1 / t.x, s = 1 / t.y, o = 1 / t.z, r = (this.lowerBound.x - n.x) * i, l = (this.upperBound.x - n.x) * i, a = (this.lowerBound.y - n.y) * s, c = (this.upperBound.y - n.y) * s, d = (this.lowerBound.z - n.z) * o, u = (this.upperBound.z - n.z) * o, m = Math.max(Math.max(Math.min(r, l), Math.min(a, c)), Math.min(d, u)), g = Math.min(Math.min(Math.max(r, l), Math.max(a, c)), Math.max(d, u));
    return !(g < 0 || m > g);
  }
}
const zr = new b(), Br = [new b(), new b(), new b(), new b(), new b(), new b(), new b(), new b()];
class Nr {
  constructor() {
    this.matrix = [];
  }
  get(e, t) {
    let {
      index: n
    } = e, {
      index: i
    } = t;
    if (i > n) {
      const s = i;
      i = n, n = s;
    }
    return this.matrix[(n * (n + 1) >> 1) + i - 1];
  }
  set(e, t, n) {
    let {
      index: i
    } = e, {
      index: s
    } = t;
    if (s > i) {
      const o = s;
      s = i, i = o;
    }
    this.matrix[(i * (i + 1) >> 1) + s - 1] = n ? 1 : 0;
  }
  reset() {
    for (let e = 0, t = this.matrix.length; e !== t; e++)
      this.matrix[e] = 0;
  }
  setNumObjects(e) {
    this.matrix.length = e * (e - 1) >> 1;
  }
}
class bo {
  addEventListener(e, t) {
    this._listeners === void 0 && (this._listeners = {});
    const n = this._listeners;
    return n[e] === void 0 && (n[e] = []), n[e].includes(t) || n[e].push(t), this;
  }
  hasEventListener(e, t) {
    if (this._listeners === void 0)
      return !1;
    const n = this._listeners;
    return !!(n[e] !== void 0 && n[e].includes(t));
  }
  hasAnyEventListener(e) {
    return this._listeners === void 0 ? !1 : this._listeners[e] !== void 0;
  }
  removeEventListener(e, t) {
    if (this._listeners === void 0)
      return this;
    const n = this._listeners;
    if (n[e] === void 0)
      return this;
    const i = n[e].indexOf(t);
    return i !== -1 && n[e].splice(i, 1), this;
  }
  dispatchEvent(e) {
    if (this._listeners === void 0)
      return this;
    const n = this._listeners[e.type];
    if (n !== void 0) {
      e.target = this;
      for (let i = 0, s = n.length; i < s; i++)
        n[i].call(this, e);
    }
    return this;
  }
}
class je {
  constructor(e, t, n, i) {
    e === void 0 && (e = 0), t === void 0 && (t = 0), n === void 0 && (n = 0), i === void 0 && (i = 1), this.x = e, this.y = t, this.z = n, this.w = i;
  }
  set(e, t, n, i) {
    return this.x = e, this.y = t, this.z = n, this.w = i, this;
  }
  toString() {
    return `${this.x},${this.y},${this.z},${this.w}`;
  }
  toArray() {
    return [this.x, this.y, this.z, this.w];
  }
  setFromAxisAngle(e, t) {
    const n = Math.sin(t * 0.5);
    return this.x = e.x * n, this.y = e.y * n, this.z = e.z * n, this.w = Math.cos(t * 0.5), this;
  }
  toAxisAngle(e) {
    e === void 0 && (e = new b()), this.normalize();
    const t = 2 * Math.acos(this.w), n = Math.sqrt(1 - this.w * this.w);
    return n < 1e-3 ? (e.x = this.x, e.y = this.y, e.z = this.z) : (e.x = this.x / n, e.y = this.y / n, e.z = this.z / n), [e, t];
  }
  setFromVectors(e, t) {
    if (e.isAntiparallelTo(t)) {
      const n = Yu, i = Zu;
      e.tangents(n, i), this.setFromAxisAngle(n, Math.PI);
    } else {
      const n = e.cross(t);
      this.x = n.x, this.y = n.y, this.z = n.z, this.w = Math.sqrt(e.length() ** 2 * t.length() ** 2) + e.dot(t), this.normalize();
    }
    return this;
  }
  mult(e, t) {
    t === void 0 && (t = new je());
    const n = this.x, i = this.y, s = this.z, o = this.w, r = e.x, l = e.y, a = e.z, c = e.w;
    return t.x = n * c + o * r + i * a - s * l, t.y = i * c + o * l + s * r - n * a, t.z = s * c + o * a + n * l - i * r, t.w = o * c - n * r - i * l - s * a, t;
  }
  inverse(e) {
    e === void 0 && (e = new je());
    const t = this.x, n = this.y, i = this.z, s = this.w;
    this.conjugate(e);
    const o = 1 / (t * t + n * n + i * i + s * s);
    return e.x *= o, e.y *= o, e.z *= o, e.w *= o, e;
  }
  conjugate(e) {
    return e === void 0 && (e = new je()), e.x = -this.x, e.y = -this.y, e.z = -this.z, e.w = this.w, e;
  }
  normalize() {
    let e = Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z + this.w * this.w);
    return e === 0 ? (this.x = 0, this.y = 0, this.z = 0, this.w = 0) : (e = 1 / e, this.x *= e, this.y *= e, this.z *= e, this.w *= e), this;
  }
  normalizeFast() {
    const e = (3 - (this.x * this.x + this.y * this.y + this.z * this.z + this.w * this.w)) / 2;
    return e === 0 ? (this.x = 0, this.y = 0, this.z = 0, this.w = 0) : (this.x *= e, this.y *= e, this.z *= e, this.w *= e), this;
  }
  vmult(e, t) {
    t === void 0 && (t = new b());
    const n = e.x, i = e.y, s = e.z, o = this.x, r = this.y, l = this.z, a = this.w, c = a * n + r * s - l * i, d = a * i + l * n - o * s, u = a * s + o * i - r * n, m = -o * n - r * i - l * s;
    return t.x = c * a + m * -o + d * -l - u * -r, t.y = d * a + m * -r + u * -o - c * -l, t.z = u * a + m * -l + c * -r - d * -o, t;
  }
  copy(e) {
    return this.x = e.x, this.y = e.y, this.z = e.z, this.w = e.w, this;
  }
  toEuler(e, t) {
    t === void 0 && (t = "YZX");
    let n, i, s;
    const o = this.x, r = this.y, l = this.z, a = this.w;
    switch (t) {
      case "YZX":
        const c = o * r + l * a;
        if (c > 0.499 && (n = 2 * Math.atan2(o, a), i = Math.PI / 2, s = 0), c < -0.499 && (n = -2 * Math.atan2(o, a), i = -Math.PI / 2, s = 0), n === void 0) {
          const d = o * o, u = r * r, m = l * l;
          n = Math.atan2(2 * r * a - 2 * o * l, 1 - 2 * u - 2 * m), i = Math.asin(2 * c), s = Math.atan2(2 * o * a - 2 * r * l, 1 - 2 * d - 2 * m);
        }
        break;
      default:
        throw new Error(`Euler order ${t} not supported yet.`);
    }
    e.y = n, e.z = i, e.x = s;
  }
  setFromEuler(e, t, n, i) {
    i === void 0 && (i = "XYZ");
    const s = Math.cos(e / 2), o = Math.cos(t / 2), r = Math.cos(n / 2), l = Math.sin(e / 2), a = Math.sin(t / 2), c = Math.sin(n / 2);
    return i === "XYZ" ? (this.x = l * o * r + s * a * c, this.y = s * a * r - l * o * c, this.z = s * o * c + l * a * r, this.w = s * o * r - l * a * c) : i === "YXZ" ? (this.x = l * o * r + s * a * c, this.y = s * a * r - l * o * c, this.z = s * o * c - l * a * r, this.w = s * o * r + l * a * c) : i === "ZXY" ? (this.x = l * o * r - s * a * c, this.y = s * a * r + l * o * c, this.z = s * o * c + l * a * r, this.w = s * o * r - l * a * c) : i === "ZYX" ? (this.x = l * o * r - s * a * c, this.y = s * a * r + l * o * c, this.z = s * o * c - l * a * r, this.w = s * o * r + l * a * c) : i === "YZX" ? (this.x = l * o * r + s * a * c, this.y = s * a * r + l * o * c, this.z = s * o * c - l * a * r, this.w = s * o * r - l * a * c) : i === "XZY" && (this.x = l * o * r - s * a * c, this.y = s * a * r - l * o * c, this.z = s * o * c + l * a * r, this.w = s * o * r + l * a * c), this;
  }
  clone() {
    return new je(this.x, this.y, this.z, this.w);
  }
  slerp(e, t, n) {
    n === void 0 && (n = new je());
    const i = this.x, s = this.y, o = this.z, r = this.w;
    let l = e.x, a = e.y, c = e.z, d = e.w, u, m, g, p, f;
    return m = i * l + s * a + o * c + r * d, m < 0 && (m = -m, l = -l, a = -a, c = -c, d = -d), 1 - m > 1e-6 ? (u = Math.acos(m), g = Math.sin(u), p = Math.sin((1 - t) * u) / g, f = Math.sin(t * u) / g) : (p = 1 - t, f = t), n.x = p * i + f * l, n.y = p * s + f * a, n.z = p * o + f * c, n.w = p * r + f * d, n;
  }
  integrate(e, t, n, i) {
    i === void 0 && (i = new je());
    const s = e.x * n.x, o = e.y * n.y, r = e.z * n.z, l = this.x, a = this.y, c = this.z, d = this.w, u = t * 0.5;
    return i.x += u * (s * d + o * c - r * a), i.y += u * (o * d + r * l - s * c), i.z += u * (r * d + s * a - o * l), i.w += u * (-s * l - o * a - r * c), i;
  }
}
const Yu = new b(), Zu = new b(), $u = {
  SPHERE: 1,
  PLANE: 2,
  BOX: 4,
  COMPOUND: 8,
  CONVEXPOLYHEDRON: 16,
  HEIGHTFIELD: 32,
  PARTICLE: 64,
  CYLINDER: 128,
  TRIMESH: 256
};
class le {
  constructor(e) {
    e === void 0 && (e = {}), this.id = le.idCounter++, this.type = e.type || 0, this.boundingSphereRadius = 0, this.collisionResponse = e.collisionResponse ? e.collisionResponse : !0, this.collisionFilterGroup = e.collisionFilterGroup !== void 0 ? e.collisionFilterGroup : 1, this.collisionFilterMask = e.collisionFilterMask !== void 0 ? e.collisionFilterMask : -1, this.material = e.material ? e.material : null, this.body = null;
  }
  updateBoundingSphereRadius() {
    throw `computeBoundingSphereRadius() not implemented for shape type ${this.type}`;
  }
  volume() {
    throw `volume() not implemented for shape type ${this.type}`;
  }
  calculateLocalInertia(e, t) {
    throw `calculateLocalInertia() not implemented for shape type ${this.type}`;
  }
  calculateWorldAABB(e, t, n, i) {
    throw `calculateWorldAABB() not implemented for shape type ${this.type}`;
  }
}
le.idCounter = 0;
le.types = $u;
class Pe {
  constructor(e) {
    e === void 0 && (e = {}), this.position = new b(), this.quaternion = new je(), e.position && this.position.copy(e.position), e.quaternion && this.quaternion.copy(e.quaternion);
  }
  pointToLocal(e, t) {
    return Pe.pointToLocalFrame(this.position, this.quaternion, e, t);
  }
  pointToWorld(e, t) {
    return Pe.pointToWorldFrame(this.position, this.quaternion, e, t);
  }
  vectorToWorldFrame(e, t) {
    return t === void 0 && (t = new b()), this.quaternion.vmult(e, t), t;
  }
  static pointToLocalFrame(e, t, n, i) {
    return i === void 0 && (i = new b()), n.vsub(e, i), t.conjugate(Or), Or.vmult(i, i), i;
  }
  static pointToWorldFrame(e, t, n, i) {
    return i === void 0 && (i = new b()), t.vmult(n, i), i.vadd(e, i), i;
  }
  static vectorToWorldFrame(e, t, n) {
    return n === void 0 && (n = new b()), e.vmult(t, n), n;
  }
  static vectorToLocalFrame(e, t, n, i) {
    return i === void 0 && (i = new b()), t.w *= -1, t.vmult(n, i), t.w *= -1, i;
  }
}
const Or = new je();
class wn extends le {
  constructor(e) {
    e === void 0 && (e = {});
    const {
      vertices: t = [],
      faces: n = [],
      normals: i = [],
      axes: s,
      boundingSphereRadius: o
    } = e;
    super({
      type: le.types.CONVEXPOLYHEDRON
    }), this.vertices = t, this.faces = n, this.faceNormals = i, this.faceNormals.length === 0 && this.computeNormals(), o ? this.boundingSphereRadius = o : this.updateBoundingSphereRadius(), this.worldVertices = [], this.worldVerticesNeedsUpdate = !0, this.worldFaceNormals = [], this.worldFaceNormalsNeedsUpdate = !0, this.uniqueAxes = s ? s.slice() : null, this.uniqueEdges = [], this.computeEdges();
  }
  computeEdges() {
    const e = this.faces, t = this.vertices, n = this.uniqueEdges;
    n.length = 0;
    const i = new b();
    for (let s = 0; s !== e.length; s++) {
      const o = e[s], r = o.length;
      for (let l = 0; l !== r; l++) {
        const a = (l + 1) % r;
        t[o[l]].vsub(t[o[a]], i), i.normalize();
        let c = !1;
        for (let d = 0; d !== n.length; d++)
          if (n[d].almostEquals(i) || n[d].almostEquals(i)) {
            c = !0;
            break;
          }
        c || n.push(i.clone());
      }
    }
  }
  computeNormals() {
    this.faceNormals.length = this.faces.length;
    for (let e = 0; e < this.faces.length; e++) {
      for (let i = 0; i < this.faces[e].length; i++)
        if (!this.vertices[this.faces[e][i]])
          throw new Error(`Vertex ${this.faces[e][i]} not found!`);
      const t = this.faceNormals[e] || new b();
      this.getFaceNormal(e, t), t.negate(t), this.faceNormals[e] = t;
      const n = this.vertices[this.faces[e][0]];
      if (t.dot(n) < 0) {
        console.error(`.faceNormals[${e}] = Vec3(${t.toString()}) looks like it points into the shape? The vertices follow. Make sure they are ordered CCW around the normal, using the right hand rule.`);
        for (let i = 0; i < this.faces[e].length; i++)
          console.warn(`.vertices[${this.faces[e][i]}] = Vec3(${this.vertices[this.faces[e][i]].toString()})`);
      }
    }
  }
  getFaceNormal(e, t) {
    const n = this.faces[e], i = this.vertices[n[0]], s = this.vertices[n[1]], o = this.vertices[n[2]];
    wn.computeNormal(i, s, o, t);
  }
  static computeNormal(e, t, n, i) {
    const s = new b(), o = new b();
    t.vsub(e, o), n.vsub(t, s), s.cross(o, i), i.isZero() || i.normalize();
  }
  clipAgainstHull(e, t, n, i, s, o, r, l, a) {
    const c = new b();
    let d = -1, u = -Number.MAX_VALUE;
    for (let g = 0; g < n.faces.length; g++) {
      c.copy(n.faceNormals[g]), s.vmult(c, c);
      const p = c.dot(o);
      p > u && (u = p, d = g);
    }
    const m = [];
    for (let g = 0; g < n.faces[d].length; g++) {
      const p = n.vertices[n.faces[d][g]], f = new b();
      f.copy(p), s.vmult(f, f), i.vadd(f, f), m.push(f);
    }
    d >= 0 && this.clipFaceAgainstHull(o, e, t, m, r, l, a);
  }
  findSeparatingAxis(e, t, n, i, s, o, r, l) {
    const a = new b(), c = new b(), d = new b(), u = new b(), m = new b(), g = new b();
    let p = Number.MAX_VALUE;
    const f = this;
    if (f.uniqueAxes)
      for (let v = 0; v !== f.uniqueAxes.length; v++) {
        n.vmult(f.uniqueAxes[v], a);
        const _ = f.testSepAxis(a, e, t, n, i, s);
        if (_ === !1)
          return !1;
        _ < p && (p = _, o.copy(a));
      }
    else {
      const v = r ? r.length : f.faces.length;
      for (let _ = 0; _ < v; _++) {
        const w = r ? r[_] : _;
        a.copy(f.faceNormals[w]), n.vmult(a, a);
        const x = f.testSepAxis(a, e, t, n, i, s);
        if (x === !1)
          return !1;
        x < p && (p = x, o.copy(a));
      }
    }
    if (e.uniqueAxes)
      for (let v = 0; v !== e.uniqueAxes.length; v++) {
        s.vmult(e.uniqueAxes[v], c);
        const _ = f.testSepAxis(c, e, t, n, i, s);
        if (_ === !1)
          return !1;
        _ < p && (p = _, o.copy(c));
      }
    else {
      const v = l ? l.length : e.faces.length;
      for (let _ = 0; _ < v; _++) {
        const w = l ? l[_] : _;
        c.copy(e.faceNormals[w]), s.vmult(c, c);
        const x = f.testSepAxis(c, e, t, n, i, s);
        if (x === !1)
          return !1;
        x < p && (p = x, o.copy(c));
      }
    }
    for (let v = 0; v !== f.uniqueEdges.length; v++) {
      n.vmult(f.uniqueEdges[v], u);
      for (let _ = 0; _ !== e.uniqueEdges.length; _++)
        if (s.vmult(e.uniqueEdges[_], m), u.cross(m, g), !g.almostZero()) {
          g.normalize();
          const w = f.testSepAxis(g, e, t, n, i, s);
          if (w === !1)
            return !1;
          w < p && (p = w, o.copy(g));
        }
    }
    return i.vsub(t, d), d.dot(o) > 0 && o.negate(o), !0;
  }
  testSepAxis(e, t, n, i, s, o) {
    const r = this;
    wn.project(r, e, n, i, As), wn.project(t, e, s, o, Cs);
    const l = As[0], a = As[1], c = Cs[0], d = Cs[1];
    if (l < d || c < a)
      return !1;
    const u = l - d, m = c - a;
    return u < m ? u : m;
  }
  calculateLocalInertia(e, t) {
    const n = new b(), i = new b();
    this.computeLocalAABB(i, n);
    const s = n.x - i.x, o = n.y - i.y, r = n.z - i.z;
    t.x = 1 / 12 * e * (2 * o * 2 * o + 2 * r * 2 * r), t.y = 1 / 12 * e * (2 * s * 2 * s + 2 * r * 2 * r), t.z = 1 / 12 * e * (2 * o * 2 * o + 2 * s * 2 * s);
  }
  getPlaneConstantOfFace(e) {
    const t = this.faces[e], n = this.faceNormals[e], i = this.vertices[t[0]];
    return -n.dot(i);
  }
  clipFaceAgainstHull(e, t, n, i, s, o, r) {
    const l = new b(), a = new b(), c = new b(), d = new b(), u = new b(), m = new b(), g = new b(), p = new b(), f = this, v = [], _ = i, w = v;
    let x = -1, M = Number.MAX_VALUE;
    for (let F = 0; F < f.faces.length; F++) {
      l.copy(f.faceNormals[F]), n.vmult(l, l);
      const P = l.dot(e);
      P < M && (M = P, x = F);
    }
    if (x < 0)
      return;
    const E = f.faces[x];
    E.connectedFaces = [];
    for (let F = 0; F < f.faces.length; F++)
      for (let P = 0; P < f.faces[F].length; P++)
        E.indexOf(f.faces[F][P]) !== -1 && F !== x && E.connectedFaces.indexOf(F) === -1 && E.connectedFaces.push(F);
    const R = E.length;
    for (let F = 0; F < R; F++) {
      const P = f.vertices[E[F]], G = f.vertices[E[(F + 1) % R]];
      P.vsub(G, a), c.copy(a), n.vmult(c, c), t.vadd(c, c), d.copy(this.faceNormals[x]), n.vmult(d, d), t.vadd(d, d), c.cross(d, u), u.negate(u), m.copy(P), n.vmult(m, m), t.vadd(m, m);
      const z = E.connectedFaces[F];
      g.copy(this.faceNormals[z]);
      const L = this.getPlaneConstantOfFace(z);
      p.copy(g), n.vmult(p, p);
      const I = L - p.dot(t);
      for (this.clipFaceAgainstPlane(_, w, p, I); _.length; )
        _.shift();
      for (; w.length; )
        _.push(w.shift());
    }
    g.copy(this.faceNormals[x]);
    const y = this.getPlaneConstantOfFace(x);
    p.copy(g), n.vmult(p, p);
    const A = y - p.dot(t);
    for (let F = 0; F < _.length; F++) {
      let P = p.dot(_[F]) + A;
      if (P <= s && (P = s), P <= o) {
        const G = _[F];
        if (P <= 1e-6) {
          const z = {
            point: G,
            normal: p,
            depth: P
          };
          r.push(z);
        }
      }
    }
  }
  clipFaceAgainstPlane(e, t, n, i) {
    let s, o;
    const r = e.length;
    if (r < 2)
      return t;
    let l = e[e.length - 1], a = e[0];
    s = n.dot(l) + i;
    for (let c = 0; c < r; c++) {
      if (a = e[c], o = n.dot(a) + i, s < 0)
        if (o < 0) {
          const d = new b();
          d.copy(a), t.push(d);
        } else {
          const d = new b();
          l.lerp(a, s / (s - o), d), t.push(d);
        }
      else if (o < 0) {
        const d = new b();
        l.lerp(a, s / (s - o), d), t.push(d), t.push(a);
      }
      l = a, s = o;
    }
    return t;
  }
  computeWorldVertices(e, t) {
    for (; this.worldVertices.length < this.vertices.length; )
      this.worldVertices.push(new b());
    const n = this.vertices, i = this.worldVertices;
    for (let s = 0; s !== this.vertices.length; s++)
      t.vmult(n[s], i[s]), e.vadd(i[s], i[s]);
    this.worldVerticesNeedsUpdate = !1;
  }
  computeLocalAABB(e, t) {
    const n = this.vertices;
    e.set(Number.MAX_VALUE, Number.MAX_VALUE, Number.MAX_VALUE), t.set(-Number.MAX_VALUE, -Number.MAX_VALUE, -Number.MAX_VALUE);
    for (let i = 0; i < this.vertices.length; i++) {
      const s = n[i];
      s.x < e.x ? e.x = s.x : s.x > t.x && (t.x = s.x), s.y < e.y ? e.y = s.y : s.y > t.y && (t.y = s.y), s.z < e.z ? e.z = s.z : s.z > t.z && (t.z = s.z);
    }
  }
  computeWorldFaceNormals(e) {
    const t = this.faceNormals.length;
    for (; this.worldFaceNormals.length < t; )
      this.worldFaceNormals.push(new b());
    const n = this.faceNormals, i = this.worldFaceNormals;
    for (let s = 0; s !== t; s++)
      e.vmult(n[s], i[s]);
    this.worldFaceNormalsNeedsUpdate = !1;
  }
  updateBoundingSphereRadius() {
    let e = 0;
    const t = this.vertices;
    for (let n = 0; n !== t.length; n++) {
      const i = t[n].lengthSquared();
      i > e && (e = i);
    }
    this.boundingSphereRadius = Math.sqrt(e);
  }
  calculateWorldAABB(e, t, n, i) {
    const s = this.vertices;
    let o, r, l, a, c, d, u = new b();
    for (let m = 0; m < s.length; m++) {
      u.copy(s[m]), t.vmult(u, u), e.vadd(u, u);
      const g = u;
      (o === void 0 || g.x < o) && (o = g.x), (a === void 0 || g.x > a) && (a = g.x), (r === void 0 || g.y < r) && (r = g.y), (c === void 0 || g.y > c) && (c = g.y), (l === void 0 || g.z < l) && (l = g.z), (d === void 0 || g.z > d) && (d = g.z);
    }
    n.set(o, r, l), i.set(a, c, d);
  }
  volume() {
    return 4 * Math.PI * this.boundingSphereRadius / 3;
  }
  getAveragePointLocal(e) {
    e === void 0 && (e = new b());
    const t = this.vertices;
    for (let n = 0; n < t.length; n++)
      e.vadd(t[n], e);
    return e.scale(1 / t.length, e), e;
  }
  transformAllPoints(e, t) {
    const n = this.vertices.length, i = this.vertices;
    if (t) {
      for (let s = 0; s < n; s++) {
        const o = i[s];
        t.vmult(o, o);
      }
      for (let s = 0; s < this.faceNormals.length; s++) {
        const o = this.faceNormals[s];
        t.vmult(o, o);
      }
    }
    if (e)
      for (let s = 0; s < n; s++) {
        const o = i[s];
        o.vadd(e, o);
      }
  }
  pointIsInside(e) {
    const t = this.vertices, n = this.faces, i = this.faceNormals, s = null, o = new b();
    this.getAveragePointLocal(o);
    for (let r = 0; r < this.faces.length; r++) {
      let l = i[r];
      const a = t[n[r][0]], c = new b();
      e.vsub(a, c);
      const d = l.dot(c), u = new b();
      o.vsub(a, u);
      const m = l.dot(u);
      if (d < 0 && m > 0 || d > 0 && m < 0)
        return !1;
    }
    return s ? 1 : -1;
  }
  static project(e, t, n, i, s) {
    const o = e.vertices.length, r = Ku;
    let l = 0, a = 0;
    const c = Ju, d = e.vertices;
    c.setZero(), Pe.vectorToLocalFrame(n, i, t, r), Pe.pointToLocalFrame(n, i, c, c);
    const u = c.dot(r);
    a = l = d[0].dot(r);
    for (let m = 1; m < o; m++) {
      const g = d[m].dot(r);
      g > l && (l = g), g < a && (a = g);
    }
    if (a -= u, l -= u, a > l) {
      const m = a;
      a = l, l = m;
    }
    s[0] = l, s[1] = a;
  }
}
const As = [], Cs = [];
new b();
const Ku = new b(), Ju = new b();
class Ws extends le {
  constructor(e) {
    super({
      type: le.types.BOX
    }), this.halfExtents = e, this.convexPolyhedronRepresentation = null, this.updateConvexPolyhedronRepresentation(), this.updateBoundingSphereRadius();
  }
  updateConvexPolyhedronRepresentation() {
    const e = this.halfExtents.x, t = this.halfExtents.y, n = this.halfExtents.z, i = b, s = [new i(-e, -t, -n), new i(e, -t, -n), new i(e, t, -n), new i(-e, t, -n), new i(-e, -t, n), new i(e, -t, n), new i(e, t, n), new i(-e, t, n)], o = [
      [3, 2, 1, 0],
      [4, 5, 6, 7],
      [5, 4, 0, 1],
      [2, 3, 7, 6],
      [0, 4, 7, 3],
      [1, 2, 6, 5]
    ], r = [new i(0, 0, 1), new i(0, 1, 0), new i(1, 0, 0)], l = new wn({
      vertices: s,
      faces: o,
      axes: r
    });
    this.convexPolyhedronRepresentation = l, l.material = this.material;
  }
  calculateLocalInertia(e, t) {
    return t === void 0 && (t = new b()), Ws.calculateInertia(this.halfExtents, e, t), t;
  }
  static calculateInertia(e, t, n) {
    const i = e;
    n.x = 1 / 12 * t * (2 * i.y * 2 * i.y + 2 * i.z * 2 * i.z), n.y = 1 / 12 * t * (2 * i.x * 2 * i.x + 2 * i.z * 2 * i.z), n.z = 1 / 12 * t * (2 * i.y * 2 * i.y + 2 * i.x * 2 * i.x);
  }
  getSideNormals(e, t) {
    const n = e, i = this.halfExtents;
    if (n[0].set(i.x, 0, 0), n[1].set(0, i.y, 0), n[2].set(0, 0, i.z), n[3].set(-i.x, 0, 0), n[4].set(0, -i.y, 0), n[5].set(0, 0, -i.z), t !== void 0)
      for (let s = 0; s !== n.length; s++)
        t.vmult(n[s], n[s]);
    return n;
  }
  volume() {
    return 8 * this.halfExtents.x * this.halfExtents.y * this.halfExtents.z;
  }
  updateBoundingSphereRadius() {
    this.boundingSphereRadius = this.halfExtents.length();
  }
  forEachWorldCorner(e, t, n) {
    const i = this.halfExtents, s = [[i.x, i.y, i.z], [-i.x, i.y, i.z], [-i.x, -i.y, i.z], [-i.x, -i.y, -i.z], [i.x, -i.y, -i.z], [i.x, i.y, -i.z], [-i.x, i.y, -i.z], [i.x, -i.y, i.z]];
    for (let o = 0; o < s.length; o++)
      hn.set(s[o][0], s[o][1], s[o][2]), t.vmult(hn, hn), e.vadd(hn, hn), n(hn.x, hn.y, hn.z);
  }
  calculateWorldAABB(e, t, n, i) {
    const s = this.halfExtents;
    Pt[0].set(s.x, s.y, s.z), Pt[1].set(-s.x, s.y, s.z), Pt[2].set(-s.x, -s.y, s.z), Pt[3].set(-s.x, -s.y, -s.z), Pt[4].set(s.x, -s.y, -s.z), Pt[5].set(s.x, s.y, -s.z), Pt[6].set(-s.x, s.y, -s.z), Pt[7].set(s.x, -s.y, s.z);
    const o = Pt[0];
    t.vmult(o, o), e.vadd(o, o), i.copy(o), n.copy(o);
    for (let r = 1; r < 8; r++) {
      const l = Pt[r];
      t.vmult(l, l), e.vadd(l, l);
      const a = l.x, c = l.y, d = l.z;
      a > i.x && (i.x = a), c > i.y && (i.y = c), d > i.z && (i.z = d), a < n.x && (n.x = a), c < n.y && (n.y = c), d < n.z && (n.z = d);
    }
  }
}
const hn = new b(), Pt = [new b(), new b(), new b(), new b(), new b(), new b(), new b(), new b()], Vs = {
  DYNAMIC: 1,
  STATIC: 2,
  KINEMATIC: 4
}, Hs = {
  AWAKE: 0,
  SLEEPY: 1,
  SLEEPING: 2
};
class ie extends bo {
  constructor(e) {
    e === void 0 && (e = {}), super(), this.id = ie.idCounter++, this.index = -1, this.world = null, this.vlambda = new b(), this.collisionFilterGroup = typeof e.collisionFilterGroup == "number" ? e.collisionFilterGroup : 1, this.collisionFilterMask = typeof e.collisionFilterMask == "number" ? e.collisionFilterMask : -1, this.collisionResponse = typeof e.collisionResponse == "boolean" ? e.collisionResponse : !0, this.position = new b(), this.previousPosition = new b(), this.interpolatedPosition = new b(), this.initPosition = new b(), e.position && (this.position.copy(e.position), this.previousPosition.copy(e.position), this.interpolatedPosition.copy(e.position), this.initPosition.copy(e.position)), this.velocity = new b(), e.velocity && this.velocity.copy(e.velocity), this.initVelocity = new b(), this.force = new b();
    const t = typeof e.mass == "number" ? e.mass : 0;
    this.mass = t, this.invMass = t > 0 ? 1 / t : 0, this.material = e.material || null, this.linearDamping = typeof e.linearDamping == "number" ? e.linearDamping : 0.01, this.type = t <= 0 ? ie.STATIC : ie.DYNAMIC, typeof e.type == typeof ie.STATIC && (this.type = e.type), this.allowSleep = typeof e.allowSleep < "u" ? e.allowSleep : !0, this.sleepState = ie.AWAKE, this.sleepSpeedLimit = typeof e.sleepSpeedLimit < "u" ? e.sleepSpeedLimit : 0.1, this.sleepTimeLimit = typeof e.sleepTimeLimit < "u" ? e.sleepTimeLimit : 1, this.timeLastSleepy = 0, this.wakeUpAfterNarrowphase = !1, this.torque = new b(), this.quaternion = new je(), this.initQuaternion = new je(), this.previousQuaternion = new je(), this.interpolatedQuaternion = new je(), e.quaternion && (this.quaternion.copy(e.quaternion), this.initQuaternion.copy(e.quaternion), this.previousQuaternion.copy(e.quaternion), this.interpolatedQuaternion.copy(e.quaternion)), this.angularVelocity = new b(), e.angularVelocity && this.angularVelocity.copy(e.angularVelocity), this.initAngularVelocity = new b(), this.shapes = [], this.shapeOffsets = [], this.shapeOrientations = [], this.inertia = new b(), this.invInertia = new b(), this.invInertiaWorld = new Lt(), this.invMassSolve = 0, this.invInertiaSolve = new b(), this.invInertiaWorldSolve = new Lt(), this.fixedRotation = typeof e.fixedRotation < "u" ? e.fixedRotation : !1, this.angularDamping = typeof e.angularDamping < "u" ? e.angularDamping : 0.01, this.linearFactor = new b(1, 1, 1), e.linearFactor && this.linearFactor.copy(e.linearFactor), this.angularFactor = new b(1, 1, 1), e.angularFactor && this.angularFactor.copy(e.angularFactor), this.aabb = new vt(), this.aabbNeedsUpdate = !0, this.boundingRadius = 0, this.wlambda = new b(), this.isTrigger = Boolean(e.isTrigger), e.shape && this.addShape(e.shape), this.updateMassProperties();
  }
  wakeUp() {
    const e = this.sleepState;
    this.sleepState = ie.AWAKE, this.wakeUpAfterNarrowphase = !1, e === ie.SLEEPING && this.dispatchEvent(ie.wakeupEvent);
  }
  sleep() {
    this.sleepState = ie.SLEEPING, this.velocity.set(0, 0, 0), this.angularVelocity.set(0, 0, 0), this.wakeUpAfterNarrowphase = !1;
  }
  sleepTick(e) {
    if (this.allowSleep) {
      const t = this.sleepState, n = this.velocity.lengthSquared() + this.angularVelocity.lengthSquared(), i = this.sleepSpeedLimit ** 2;
      t === ie.AWAKE && n < i ? (this.sleepState = ie.SLEEPY, this.timeLastSleepy = e, this.dispatchEvent(ie.sleepyEvent)) : t === ie.SLEEPY && n > i ? this.wakeUp() : t === ie.SLEEPY && e - this.timeLastSleepy > this.sleepTimeLimit && (this.sleep(), this.dispatchEvent(ie.sleepEvent));
    }
  }
  updateSolveMassProperties() {
    this.sleepState === ie.SLEEPING || this.type === ie.KINEMATIC ? (this.invMassSolve = 0, this.invInertiaSolve.setZero(), this.invInertiaWorldSolve.setZero()) : (this.invMassSolve = this.invMass, this.invInertiaSolve.copy(this.invInertia), this.invInertiaWorldSolve.copy(this.invInertiaWorld));
  }
  pointToLocalFrame(e, t) {
    return t === void 0 && (t = new b()), e.vsub(this.position, t), this.quaternion.conjugate().vmult(t, t), t;
  }
  vectorToLocalFrame(e, t) {
    return t === void 0 && (t = new b()), this.quaternion.conjugate().vmult(e, t), t;
  }
  pointToWorldFrame(e, t) {
    return t === void 0 && (t = new b()), this.quaternion.vmult(e, t), t.vadd(this.position, t), t;
  }
  vectorToWorldFrame(e, t) {
    return t === void 0 && (t = new b()), this.quaternion.vmult(e, t), t;
  }
  addShape(e, t, n) {
    const i = new b(), s = new je();
    return t && i.copy(t), n && s.copy(n), this.shapes.push(e), this.shapeOffsets.push(i), this.shapeOrientations.push(s), this.updateMassProperties(), this.updateBoundingRadius(), this.aabbNeedsUpdate = !0, e.body = this, this;
  }
  removeShape(e) {
    const t = this.shapes.indexOf(e);
    return t === -1 ? (console.warn("Shape does not belong to the body"), this) : (this.shapes.splice(t, 1), this.shapeOffsets.splice(t, 1), this.shapeOrientations.splice(t, 1), this.updateMassProperties(), this.updateBoundingRadius(), this.aabbNeedsUpdate = !0, e.body = null, this);
  }
  updateBoundingRadius() {
    const e = this.shapes, t = this.shapeOffsets, n = e.length;
    let i = 0;
    for (let s = 0; s !== n; s++) {
      const o = e[s];
      o.updateBoundingSphereRadius();
      const r = t[s].length(), l = o.boundingSphereRadius;
      r + l > i && (i = r + l);
    }
    this.boundingRadius = i;
  }
  updateAABB() {
    const e = this.shapes, t = this.shapeOffsets, n = this.shapeOrientations, i = e.length, s = Qu, o = ed, r = this.quaternion, l = this.aabb, a = td;
    for (let c = 0; c !== i; c++) {
      const d = e[c];
      r.vmult(t[c], s), s.vadd(this.position, s), r.mult(n[c], o), d.calculateWorldAABB(s, o, a.lowerBound, a.upperBound), c === 0 ? l.copy(a) : l.extend(a);
    }
    this.aabbNeedsUpdate = !1;
  }
  updateInertiaWorld(e) {
    const t = this.invInertia;
    if (!(t.x === t.y && t.y === t.z && !e)) {
      const n = nd, i = id;
      n.setRotationFromQuaternion(this.quaternion), n.transpose(i), n.scale(t, n), n.mmult(i, this.invInertiaWorld);
    }
  }
  applyForce(e, t) {
    if (t === void 0 && (t = new b()), this.type !== ie.DYNAMIC)
      return;
    this.sleepState === ie.SLEEPING && this.wakeUp();
    const n = rd;
    t.cross(e, n), this.force.vadd(e, this.force), this.torque.vadd(n, this.torque);
  }
  applyLocalForce(e, t) {
    if (t === void 0 && (t = new b()), this.type !== ie.DYNAMIC)
      return;
    const n = od, i = ad;
    this.vectorToWorldFrame(e, n), this.vectorToWorldFrame(t, i), this.applyForce(n, i);
  }
  applyTorque(e) {
    this.type === ie.DYNAMIC && (this.sleepState === ie.SLEEPING && this.wakeUp(), this.torque.vadd(e, this.torque));
  }
  applyImpulse(e, t) {
    if (t === void 0 && (t = new b()), this.type !== ie.DYNAMIC)
      return;
    this.sleepState === ie.SLEEPING && this.wakeUp();
    const n = t, i = ld;
    i.copy(e), i.scale(this.invMass, i), this.velocity.vadd(i, this.velocity);
    const s = cd;
    n.cross(e, s), this.invInertiaWorld.vmult(s, s), this.angularVelocity.vadd(s, this.angularVelocity);
  }
  applyLocalImpulse(e, t) {
    if (t === void 0 && (t = new b()), this.type !== ie.DYNAMIC)
      return;
    const n = hd, i = ud;
    this.vectorToWorldFrame(e, n), this.vectorToWorldFrame(t, i), this.applyImpulse(n, i);
  }
  updateMassProperties() {
    const e = dd;
    this.invMass = this.mass > 0 ? 1 / this.mass : 0;
    const t = this.inertia, n = this.fixedRotation;
    this.updateAABB(), e.set((this.aabb.upperBound.x - this.aabb.lowerBound.x) / 2, (this.aabb.upperBound.y - this.aabb.lowerBound.y) / 2, (this.aabb.upperBound.z - this.aabb.lowerBound.z) / 2), Ws.calculateInertia(e, this.mass, t), this.invInertia.set(t.x > 0 && !n ? 1 / t.x : 0, t.y > 0 && !n ? 1 / t.y : 0, t.z > 0 && !n ? 1 / t.z : 0), this.updateInertiaWorld(!0);
  }
  getVelocityAtWorldPoint(e, t) {
    const n = new b();
    return e.vsub(this.position, n), this.angularVelocity.cross(n, t), this.velocity.vadd(t, t), t;
  }
  integrate(e, t, n) {
    if (this.previousPosition.copy(this.position), this.previousQuaternion.copy(this.quaternion), !(this.type === ie.DYNAMIC || this.type === ie.KINEMATIC) || this.sleepState === ie.SLEEPING)
      return;
    const i = this.velocity, s = this.angularVelocity, o = this.position, r = this.force, l = this.torque, a = this.quaternion, c = this.invMass, d = this.invInertiaWorld, u = this.linearFactor, m = c * e;
    i.x += r.x * m * u.x, i.y += r.y * m * u.y, i.z += r.z * m * u.z;
    const g = d.elements, p = this.angularFactor, f = l.x * p.x, v = l.y * p.y, _ = l.z * p.z;
    s.x += e * (g[0] * f + g[1] * v + g[2] * _), s.y += e * (g[3] * f + g[4] * v + g[5] * _), s.z += e * (g[6] * f + g[7] * v + g[8] * _), o.x += i.x * e, o.y += i.y * e, o.z += i.z * e, a.integrate(this.angularVelocity, e, this.angularFactor, a), t && (n ? a.normalizeFast() : a.normalize()), this.aabbNeedsUpdate = !0, this.updateInertiaWorld();
  }
}
ie.idCounter = 0;
ie.COLLIDE_EVENT_NAME = "collide";
ie.DYNAMIC = Vs.DYNAMIC;
ie.STATIC = Vs.STATIC;
ie.KINEMATIC = Vs.KINEMATIC;
ie.AWAKE = Hs.AWAKE;
ie.SLEEPY = Hs.SLEEPY;
ie.SLEEPING = Hs.SLEEPING;
ie.wakeupEvent = {
  type: "wakeup"
};
ie.sleepyEvent = {
  type: "sleepy"
};
ie.sleepEvent = {
  type: "sleep"
};
const Qu = new b(), ed = new je(), td = new vt(), nd = new Lt(), id = new Lt(), sd = new Lt(), rd = new b(), od = new b(), ad = new b(), ld = new b(), cd = new b(), hd = new b(), ud = new b(), dd = new b();
class fd {
  constructor() {
    this.world = null, this.useBoundingBoxes = !1, this.dirty = !0;
  }
  collisionPairs(e, t, n) {
    throw new Error("collisionPairs not implemented for this BroadPhase class!");
  }
  needBroadphaseCollision(e, t) {
    return !((e.collisionFilterGroup & t.collisionFilterMask) === 0 || (t.collisionFilterGroup & e.collisionFilterMask) === 0 || ((e.type & ie.STATIC) !== 0 || e.sleepState === ie.SLEEPING) && ((t.type & ie.STATIC) !== 0 || t.sleepState === ie.SLEEPING));
  }
  intersectionTest(e, t, n, i) {
    this.useBoundingBoxes ? this.doBoundingBoxBroadphase(e, t, n, i) : this.doBoundingSphereBroadphase(e, t, n, i);
  }
  doBoundingSphereBroadphase(e, t, n, i) {
    const s = pd;
    t.position.vsub(e.position, s);
    const o = (e.boundingRadius + t.boundingRadius) ** 2;
    s.lengthSquared() < o && (n.push(e), i.push(t));
  }
  doBoundingBoxBroadphase(e, t, n, i) {
    e.aabbNeedsUpdate && e.updateAABB(), t.aabbNeedsUpdate && t.updateAABB(), e.aabb.overlaps(t.aabb) && (n.push(e), i.push(t));
  }
  makePairsUnique(e, t) {
    const n = md, i = gd, s = _d, o = e.length;
    for (let r = 0; r !== o; r++)
      i[r] = e[r], s[r] = t[r];
    e.length = 0, t.length = 0;
    for (let r = 0; r !== o; r++) {
      const l = i[r].id, a = s[r].id, c = l < a ? `${l},${a}` : `${a},${l}`;
      n[c] = r, n.keys.push(c);
    }
    for (let r = 0; r !== n.keys.length; r++) {
      const l = n.keys.pop(), a = n[l];
      e.push(i[a]), t.push(s[a]), delete n[l];
    }
  }
  setWorld(e) {
  }
  static boundingSphereCheck(e, t) {
    const n = new b();
    e.position.vsub(t.position, n);
    const i = e.shapes[0], s = t.shapes[0];
    return Math.pow(i.boundingSphereRadius + s.boundingSphereRadius, 2) > n.lengthSquared();
  }
  aabbQuery(e, t, n) {
    return console.warn(".aabbQuery is not implemented in this Broadphase subclass."), [];
  }
}
const pd = new b();
new b();
new je();
new b();
const md = {
  keys: []
}, gd = [], _d = [];
new b();
new b();
new b();
class wo extends fd {
  constructor() {
    super();
  }
  collisionPairs(e, t, n) {
    const i = e.bodies, s = i.length;
    let o, r;
    for (let l = 0; l !== s; l++)
      for (let a = 0; a !== l; a++)
        o = i[l], r = i[a], this.needBroadphaseCollision(o, r) && this.intersectionTest(o, r, t, n);
  }
  aabbQuery(e, t, n) {
    n === void 0 && (n = []);
    for (let i = 0; i < e.bodies.length; i++) {
      const s = e.bodies[i];
      s.aabbNeedsUpdate && s.updateAABB(), s.aabb.overlaps(t) && n.push(s);
    }
    return n;
  }
}
class Xi {
  constructor() {
    this.rayFromWorld = new b(), this.rayToWorld = new b(), this.hitNormalWorld = new b(), this.hitPointWorld = new b(), this.hasHit = !1, this.shape = null, this.body = null, this.hitFaceIndex = -1, this.distance = -1, this.shouldStop = !1;
  }
  reset() {
    this.rayFromWorld.setZero(), this.rayToWorld.setZero(), this.hitNormalWorld.setZero(), this.hitPointWorld.setZero(), this.hasHit = !1, this.shape = null, this.body = null, this.hitFaceIndex = -1, this.distance = -1, this.shouldStop = !1;
  }
  abort() {
    this.shouldStop = !0;
  }
  set(e, t, n, i, s, o, r) {
    this.rayFromWorld.copy(e), this.rayToWorld.copy(t), this.hitNormalWorld.copy(n), this.hitPointWorld.copy(i), this.shape = s, this.body = o, this.distance = r;
  }
}
let Mo, So, Eo, To, Ao, Co, Lo;
const qs = {
  CLOSEST: 1,
  ANY: 2,
  ALL: 4
};
Mo = le.types.SPHERE;
So = le.types.PLANE;
Eo = le.types.BOX;
To = le.types.CYLINDER;
Ao = le.types.CONVEXPOLYHEDRON;
Co = le.types.HEIGHTFIELD;
Lo = le.types.TRIMESH;
class Xe {
  get [Mo]() {
    return this._intersectSphere;
  }
  get [So]() {
    return this._intersectPlane;
  }
  get [Eo]() {
    return this._intersectBox;
  }
  get [To]() {
    return this._intersectConvex;
  }
  get [Ao]() {
    return this._intersectConvex;
  }
  get [Co]() {
    return this._intersectHeightfield;
  }
  get [Lo]() {
    return this._intersectTrimesh;
  }
  constructor(e, t) {
    e === void 0 && (e = new b()), t === void 0 && (t = new b()), this.from = e.clone(), this.to = t.clone(), this.direction = new b(), this.precision = 1e-4, this.checkCollisionResponse = !0, this.skipBackfaces = !1, this.collisionFilterMask = -1, this.collisionFilterGroup = -1, this.mode = Xe.ANY, this.result = new Xi(), this.hasHit = !1, this.callback = (n) => {
    };
  }
  intersectWorld(e, t) {
    return this.mode = t.mode || Xe.ANY, this.result = t.result || new Xi(), this.skipBackfaces = !!t.skipBackfaces, this.collisionFilterMask = typeof t.collisionFilterMask < "u" ? t.collisionFilterMask : -1, this.collisionFilterGroup = typeof t.collisionFilterGroup < "u" ? t.collisionFilterGroup : -1, this.checkCollisionResponse = typeof t.checkCollisionResponse < "u" ? t.checkCollisionResponse : !0, t.from && this.from.copy(t.from), t.to && this.to.copy(t.to), this.callback = t.callback || (() => {
    }), this.hasHit = !1, this.result.reset(), this.updateDirection(), this.getAABB(Ur), Ls.length = 0, e.broadphase.aabbQuery(e, Ur, Ls), this.intersectBodies(Ls), this.hasHit;
  }
  intersectBody(e, t) {
    t && (this.result = t, this.updateDirection());
    const n = this.checkCollisionResponse;
    if (n && !e.collisionResponse || (this.collisionFilterGroup & e.collisionFilterMask) === 0 || (e.collisionFilterGroup & this.collisionFilterMask) === 0)
      return;
    const i = vd, s = xd;
    for (let o = 0, r = e.shapes.length; o < r; o++) {
      const l = e.shapes[o];
      if (!(n && !l.collisionResponse) && (e.quaternion.mult(e.shapeOrientations[o], s), e.quaternion.vmult(e.shapeOffsets[o], i), i.vadd(e.position, i), this.intersectShape(l, s, i, e), this.result.shouldStop))
        break;
    }
  }
  intersectBodies(e, t) {
    t && (this.result = t, this.updateDirection());
    for (let n = 0, i = e.length; !this.result.shouldStop && n < i; n++)
      this.intersectBody(e[n]);
  }
  updateDirection() {
    this.to.vsub(this.from, this.direction), this.direction.normalize();
  }
  intersectShape(e, t, n, i) {
    const s = this.from;
    if (Pd(s, this.direction, n) > e.boundingSphereRadius)
      return;
    const r = this[e.type];
    r && r.call(this, e, t, n, i, e);
  }
  _intersectBox(e, t, n, i, s) {
    return this._intersectConvex(e.convexPolyhedronRepresentation, t, n, i, s);
  }
  _intersectPlane(e, t, n, i, s) {
    const o = this.from, r = this.to, l = this.direction, a = new b(0, 0, 1);
    t.vmult(a, a);
    const c = new b();
    o.vsub(n, c);
    const d = c.dot(a);
    r.vsub(n, c);
    const u = c.dot(a);
    if (d * u > 0 || o.distanceTo(r) < d)
      return;
    const m = a.dot(l);
    if (Math.abs(m) < this.precision)
      return;
    const g = new b(), p = new b(), f = new b();
    o.vsub(n, g);
    const v = -a.dot(g) / m;
    l.scale(v, p), o.vadd(p, f), this.reportIntersection(a, f, s, i, -1);
  }
  getAABB(e) {
    const {
      lowerBound: t,
      upperBound: n
    } = e, i = this.to, s = this.from;
    t.x = Math.min(i.x, s.x), t.y = Math.min(i.y, s.y), t.z = Math.min(i.z, s.z), n.x = Math.max(i.x, s.x), n.y = Math.max(i.y, s.y), n.z = Math.max(i.z, s.z);
  }
  _intersectHeightfield(e, t, n, i, s) {
    e.data, e.elementSize;
    const o = yd;
    o.from.copy(this.from), o.to.copy(this.to), Pe.pointToLocalFrame(n, t, o.from, o.from), Pe.pointToLocalFrame(n, t, o.to, o.to), o.updateDirection();
    const r = bd;
    let l, a, c, d;
    l = a = 0, c = d = e.data.length - 1;
    const u = new vt();
    o.getAABB(u), e.getIndexOfPosition(u.lowerBound.x, u.lowerBound.y, r, !0), l = Math.max(l, r[0]), a = Math.max(a, r[1]), e.getIndexOfPosition(u.upperBound.x, u.upperBound.y, r, !0), c = Math.min(c, r[0] + 1), d = Math.min(d, r[1] + 1);
    for (let m = l; m < c; m++)
      for (let g = a; g < d; g++) {
        if (this.result.shouldStop)
          return;
        if (e.getAabbAtIndex(m, g, u), !!u.overlapsRay(o)) {
          if (e.getConvexTrianglePillar(m, g, !1), Pe.pointToWorldFrame(n, t, e.pillarOffset, Ni), this._intersectConvex(e.pillarConvex, t, Ni, i, s, Gr), this.result.shouldStop)
            return;
          e.getConvexTrianglePillar(m, g, !0), Pe.pointToWorldFrame(n, t, e.pillarOffset, Ni), this._intersectConvex(e.pillarConvex, t, Ni, i, s, Gr);
        }
      }
  }
  _intersectSphere(e, t, n, i, s) {
    const o = this.from, r = this.to, l = e.radius, a = (r.x - o.x) ** 2 + (r.y - o.y) ** 2 + (r.z - o.z) ** 2, c = 2 * ((r.x - o.x) * (o.x - n.x) + (r.y - o.y) * (o.y - n.y) + (r.z - o.z) * (o.z - n.z)), d = (o.x - n.x) ** 2 + (o.y - n.y) ** 2 + (o.z - n.z) ** 2 - l ** 2, u = c ** 2 - 4 * a * d, m = wd, g = Md;
    if (!(u < 0))
      if (u === 0)
        o.lerp(r, u, m), m.vsub(n, g), g.normalize(), this.reportIntersection(g, m, s, i, -1);
      else {
        const p = (-c - Math.sqrt(u)) / (2 * a), f = (-c + Math.sqrt(u)) / (2 * a);
        if (p >= 0 && p <= 1 && (o.lerp(r, p, m), m.vsub(n, g), g.normalize(), this.reportIntersection(g, m, s, i, -1)), this.result.shouldStop)
          return;
        f >= 0 && f <= 1 && (o.lerp(r, f, m), m.vsub(n, g), g.normalize(), this.reportIntersection(g, m, s, i, -1));
      }
  }
  _intersectConvex(e, t, n, i, s, o) {
    const r = Sd, l = kr, a = o && o.faceList || null, c = e.faces, d = e.vertices, u = e.faceNormals, m = this.direction, g = this.from, p = this.to, f = g.distanceTo(p), v = a ? a.length : c.length, _ = this.result;
    for (let w = 0; !_.shouldStop && w < v; w++) {
      const x = a ? a[w] : w, M = c[x], E = u[x], R = t, y = n;
      l.copy(d[M[0]]), R.vmult(l, l), l.vadd(y, l), l.vsub(g, l), R.vmult(E, r);
      const A = m.dot(r);
      if (Math.abs(A) < this.precision)
        continue;
      const F = r.dot(l) / A;
      if (!(F < 0)) {
        m.scale(F, ht), ht.vadd(g, ht), Ct.copy(d[M[0]]), R.vmult(Ct, Ct), y.vadd(Ct, Ct);
        for (let P = 1; !_.shouldStop && P < M.length - 1; P++) {
          It.copy(d[M[P]]), zt.copy(d[M[P + 1]]), R.vmult(It, It), R.vmult(zt, zt), y.vadd(It, It), y.vadd(zt, zt);
          const G = ht.distanceTo(g);
          !(Xe.pointInTriangle(ht, Ct, It, zt) || Xe.pointInTriangle(ht, It, Ct, zt)) || G > f || this.reportIntersection(r, ht, s, i, x);
        }
      }
    }
  }
  _intersectTrimesh(e, t, n, i, s, o) {
    const r = Ed, l = Fd, a = Dd, c = kr, d = Td, u = Ad, m = Cd, g = Rd, p = Ld, f = e.indices;
    e.vertices;
    const v = this.from, _ = this.to, w = this.direction;
    a.position.copy(n), a.quaternion.copy(t), Pe.vectorToLocalFrame(n, t, w, d), Pe.pointToLocalFrame(n, t, v, u), Pe.pointToLocalFrame(n, t, _, m), m.x *= e.scale.x, m.y *= e.scale.y, m.z *= e.scale.z, u.x *= e.scale.x, u.y *= e.scale.y, u.z *= e.scale.z, m.vsub(u, d), d.normalize();
    const x = u.distanceSquared(m);
    e.tree.rayQuery(this, a, l);
    for (let M = 0, E = l.length; !this.result.shouldStop && M !== E; M++) {
      const R = l[M];
      e.getNormal(R, r), e.getVertex(f[R * 3], Ct), Ct.vsub(u, c);
      const y = d.dot(r), A = r.dot(c) / y;
      if (A < 0)
        continue;
      d.scale(A, ht), ht.vadd(u, ht), e.getVertex(f[R * 3 + 1], It), e.getVertex(f[R * 3 + 2], zt);
      const F = ht.distanceSquared(u);
      !(Xe.pointInTriangle(ht, It, Ct, zt) || Xe.pointInTriangle(ht, Ct, It, zt)) || F > x || (Pe.vectorToWorldFrame(t, r, p), Pe.pointToWorldFrame(n, t, ht, g), this.reportIntersection(p, g, s, i, R));
    }
    l.length = 0;
  }
  reportIntersection(e, t, n, i, s) {
    const o = this.from, r = this.to, l = o.distanceTo(t), a = this.result;
    if (!(this.skipBackfaces && e.dot(this.direction) > 0))
      switch (a.hitFaceIndex = typeof s < "u" ? s : -1, this.mode) {
        case Xe.ALL:
          this.hasHit = !0, a.set(o, r, e, t, n, i, l), a.hasHit = !0, this.callback(a);
          break;
        case Xe.CLOSEST:
          (l < a.distance || !a.hasHit) && (this.hasHit = !0, a.hasHit = !0, a.set(o, r, e, t, n, i, l));
          break;
        case Xe.ANY:
          this.hasHit = !0, a.hasHit = !0, a.set(o, r, e, t, n, i, l), a.shouldStop = !0;
          break;
      }
  }
  static pointInTriangle(e, t, n, i) {
    i.vsub(t, xn), n.vsub(t, ii), e.vsub(t, Rs);
    const s = xn.dot(xn), o = xn.dot(ii), r = xn.dot(Rs), l = ii.dot(ii), a = ii.dot(Rs);
    let c, d;
    return (c = l * r - o * a) >= 0 && (d = s * a - o * r) >= 0 && c + d < s * l - o * o;
  }
}
Xe.CLOSEST = qs.CLOSEST;
Xe.ANY = qs.ANY;
Xe.ALL = qs.ALL;
const Ur = new vt(), Ls = [], ii = new b(), Rs = new b(), vd = new b(), xd = new je(), ht = new b(), Ct = new b(), It = new b(), zt = new b();
new b();
new Xi();
const Gr = {
  faceList: [0]
}, Ni = new b(), yd = new Xe(), bd = [], wd = new b(), Md = new b(), Sd = new b();
new b();
new b();
const kr = new b(), Ed = new b(), Td = new b(), Ad = new b(), Cd = new b(), Ld = new b(), Rd = new b();
new vt();
const Fd = [], Dd = new Pe(), xn = new b(), Oi = new b();
function Pd(h, e, t) {
  t.vsub(h, xn);
  const n = xn.dot(e);
  return e.scale(n, Oi), Oi.vadd(h, Oi), t.distanceTo(Oi);
}
class Id {
  static defaults(e, t) {
    e === void 0 && (e = {});
    for (let n in t)
      n in e || (e[n] = t[n]);
    return e;
  }
}
class Wr {
  constructor() {
    this.spatial = new b(), this.rotational = new b();
  }
  multiplyElement(e) {
    return e.spatial.dot(this.spatial) + e.rotational.dot(this.rotational);
  }
  multiplyVectors(e, t) {
    return e.dot(this.spatial) + t.dot(this.rotational);
  }
}
class mi {
  constructor(e, t, n, i) {
    n === void 0 && (n = -1e6), i === void 0 && (i = 1e6), this.id = mi.idCounter++, this.minForce = n, this.maxForce = i, this.bi = e, this.bj = t, this.a = 0, this.b = 0, this.eps = 0, this.jacobianElementA = new Wr(), this.jacobianElementB = new Wr(), this.enabled = !0, this.multiplier = 0, this.setSpookParams(1e7, 4, 1 / 60);
  }
  setSpookParams(e, t, n) {
    const i = t, s = e, o = n;
    this.a = 4 / (o * (1 + 4 * i)), this.b = 4 * i / (1 + 4 * i), this.eps = 4 / (o * o * s * (1 + 4 * i));
  }
  computeB(e, t, n) {
    const i = this.computeGW(), s = this.computeGq(), o = this.computeGiMf();
    return -s * e - i * t - o * n;
  }
  computeGq() {
    const e = this.jacobianElementA, t = this.jacobianElementB, n = this.bi, i = this.bj, s = n.position, o = i.position;
    return e.spatial.dot(s) + t.spatial.dot(o);
  }
  computeGW() {
    const e = this.jacobianElementA, t = this.jacobianElementB, n = this.bi, i = this.bj, s = n.velocity, o = i.velocity, r = n.angularVelocity, l = i.angularVelocity;
    return e.multiplyVectors(s, r) + t.multiplyVectors(o, l);
  }
  computeGWlambda() {
    const e = this.jacobianElementA, t = this.jacobianElementB, n = this.bi, i = this.bj, s = n.vlambda, o = i.vlambda, r = n.wlambda, l = i.wlambda;
    return e.multiplyVectors(s, r) + t.multiplyVectors(o, l);
  }
  computeGiMf() {
    const e = this.jacobianElementA, t = this.jacobianElementB, n = this.bi, i = this.bj, s = n.force, o = n.torque, r = i.force, l = i.torque, a = n.invMassSolve, c = i.invMassSolve;
    return s.scale(a, Vr), r.scale(c, Hr), n.invInertiaWorldSolve.vmult(o, qr), i.invInertiaWorldSolve.vmult(l, Xr), e.multiplyVectors(Vr, qr) + t.multiplyVectors(Hr, Xr);
  }
  computeGiMGt() {
    const e = this.jacobianElementA, t = this.jacobianElementB, n = this.bi, i = this.bj, s = n.invMassSolve, o = i.invMassSolve, r = n.invInertiaWorldSolve, l = i.invInertiaWorldSolve;
    let a = s + o;
    return r.vmult(e.rotational, Ui), a += Ui.dot(e.rotational), l.vmult(t.rotational, Ui), a += Ui.dot(t.rotational), a;
  }
  addToWlambda(e) {
    const t = this.jacobianElementA, n = this.jacobianElementB, i = this.bi, s = this.bj, o = zd;
    i.vlambda.addScaledVector(i.invMassSolve * e, t.spatial, i.vlambda), s.vlambda.addScaledVector(s.invMassSolve * e, n.spatial, s.vlambda), i.invInertiaWorldSolve.vmult(t.rotational, o), i.wlambda.addScaledVector(e, o, i.wlambda), s.invInertiaWorldSolve.vmult(n.rotational, o), s.wlambda.addScaledVector(e, o, s.wlambda);
  }
  computeC() {
    return this.computeGiMGt() + this.eps;
  }
}
mi.idCounter = 0;
const Vr = new b(), Hr = new b(), qr = new b(), Xr = new b(), Ui = new b(), zd = new b();
class Bd extends mi {
  constructor(e, t, n) {
    n === void 0 && (n = 1e6), super(e, t, 0, n), this.restitution = 0, this.ri = new b(), this.rj = new b(), this.ni = new b();
  }
  computeB(e) {
    const t = this.a, n = this.b, i = this.bi, s = this.bj, o = this.ri, r = this.rj, l = Nd, a = Od, c = i.velocity, d = i.angularVelocity;
    i.force, i.torque;
    const u = s.velocity, m = s.angularVelocity;
    s.force, s.torque;
    const g = Ud, p = this.jacobianElementA, f = this.jacobianElementB, v = this.ni;
    o.cross(v, l), r.cross(v, a), v.negate(p.spatial), l.negate(p.rotational), f.spatial.copy(v), f.rotational.copy(a), g.copy(s.position), g.vadd(r, g), g.vsub(i.position, g), g.vsub(o, g);
    const _ = v.dot(g), w = this.restitution + 1, x = w * u.dot(v) - w * c.dot(v) + m.dot(a) - d.dot(l), M = this.computeGiMf();
    return -_ * t - x * n - e * M;
  }
  getImpactVelocityAlongNormal() {
    const e = Gd, t = kd, n = Wd, i = Vd, s = Hd;
    return this.bi.position.vadd(this.ri, n), this.bj.position.vadd(this.rj, i), this.bi.getVelocityAtWorldPoint(n, e), this.bj.getVelocityAtWorldPoint(i, t), e.vsub(t, s), this.ni.dot(s);
  }
}
const Nd = new b(), Od = new b(), Ud = new b(), Gd = new b(), kd = new b(), Wd = new b(), Vd = new b(), Hd = new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
class jr extends mi {
  constructor(e, t, n) {
    super(e, t, -n, n), this.ri = new b(), this.rj = new b(), this.t = new b();
  }
  computeB(e) {
    this.a;
    const t = this.b;
    this.bi, this.bj;
    const n = this.ri, i = this.rj, s = qd, o = Xd, r = this.t;
    n.cross(r, s), i.cross(r, o);
    const l = this.jacobianElementA, a = this.jacobianElementB;
    r.negate(l.spatial), s.negate(l.rotational), a.spatial.copy(r), a.rotational.copy(o);
    const c = this.computeGW(), d = this.computeGiMf();
    return -c * t - e * d;
  }
}
const qd = new b(), Xd = new b();
class Mn {
  constructor(e, t, n) {
    n = Id.defaults(n, {
      friction: 0.3,
      restitution: 0.3,
      contactEquationStiffness: 1e7,
      contactEquationRelaxation: 3,
      frictionEquationStiffness: 1e7,
      frictionEquationRelaxation: 3
    }), this.id = Mn.idCounter++, this.materials = [e, t], this.friction = n.friction, this.restitution = n.restitution, this.contactEquationStiffness = n.contactEquationStiffness, this.contactEquationRelaxation = n.contactEquationRelaxation, this.frictionEquationStiffness = n.frictionEquationStiffness, this.frictionEquationRelaxation = n.frictionEquationRelaxation;
  }
}
Mn.idCounter = 0;
class Sn {
  constructor(e) {
    e === void 0 && (e = {});
    let t = "";
    typeof e == "string" && (t = e, e = {}), this.name = t, this.id = Sn.idCounter++, this.friction = typeof e.friction < "u" ? e.friction : -1, this.restitution = typeof e.restitution < "u" ? e.restitution : -1;
  }
}
Sn.idCounter = 0;
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new Xe();
new b();
new b();
new b();
new b(1, 0, 0), new b(0, 1, 0), new b(0, 0, 1);
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
class jd extends wn {
  constructor(e, t, n, i) {
    if (e === void 0 && (e = 1), t === void 0 && (t = 1), n === void 0 && (n = 1), i === void 0 && (i = 8), e < 0)
      throw new Error("The cylinder radiusTop cannot be negative.");
    if (t < 0)
      throw new Error("The cylinder radiusBottom cannot be negative.");
    const s = i, o = [], r = [], l = [], a = [], c = [], d = Math.cos, u = Math.sin;
    o.push(new b(-t * u(0), -n * 0.5, t * d(0))), a.push(0), o.push(new b(-e * u(0), n * 0.5, e * d(0))), c.push(1);
    for (let g = 0; g < s; g++) {
      const p = 2 * Math.PI / s * (g + 1), f = 2 * Math.PI / s * (g + 0.5);
      g < s - 1 ? (o.push(new b(-t * u(p), -n * 0.5, t * d(p))), a.push(2 * g + 2), o.push(new b(-e * u(p), n * 0.5, e * d(p))), c.push(2 * g + 3), l.push([2 * g, 2 * g + 1, 2 * g + 3, 2 * g + 2])) : l.push([2 * g, 2 * g + 1, 1, 0]), (s % 2 === 1 || g < s / 2) && r.push(new b(-u(f), 0, d(f)));
    }
    l.push(a), r.push(new b(0, 1, 0));
    const m = [];
    for (let g = 0; g < c.length; g++)
      m.push(c[c.length - g - 1]);
    l.push(m), super({
      vertices: o,
      faces: l,
      axes: r
    }), this.type = le.types.CYLINDER, this.radiusTop = e, this.radiusBottom = t, this.height = n, this.numSegments = i;
  }
}
class si extends le {
  constructor() {
    super({
      type: le.types.PLANE
    }), this.worldNormal = new b(), this.worldNormalNeedsUpdate = !0, this.boundingSphereRadius = Number.MAX_VALUE;
  }
  computeWorldNormal(e) {
    const t = this.worldNormal;
    t.set(0, 0, 1), e.vmult(t, t), this.worldNormalNeedsUpdate = !1;
  }
  calculateLocalInertia(e, t) {
    return t === void 0 && (t = new b()), t;
  }
  volume() {
    return Number.MAX_VALUE;
  }
  calculateWorldAABB(e, t, n, i) {
    jt.set(0, 0, 1), t.vmult(jt, jt);
    const s = Number.MAX_VALUE;
    n.set(-s, -s, -s), i.set(s, s, s), jt.x === 1 ? i.x = e.x : jt.x === -1 && (n.x = e.x), jt.y === 1 ? i.y = e.y : jt.y === -1 && (n.y = e.y), jt.z === 1 ? i.z = e.z : jt.z === -1 && (n.z = e.z);
  }
  updateBoundingSphereRadius() {
    this.boundingSphereRadius = Number.MAX_VALUE;
  }
}
const jt = new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new vt();
new b();
new vt();
new b();
new b();
new b();
new b();
new b();
new b();
new b();
new vt();
new b();
new Pe();
new vt();
class Yd {
  constructor() {
    this.equations = [];
  }
  solve(e, t) {
    return 0;
  }
  addEquation(e) {
    e.enabled && !e.bi.isTrigger && !e.bj.isTrigger && this.equations.push(e);
  }
  removeEquation(e) {
    const t = this.equations, n = t.indexOf(e);
    n !== -1 && t.splice(n, 1);
  }
  removeAllEquations() {
    this.equations.length = 0;
  }
}
class Zd extends Yd {
  constructor() {
    super(), this.iterations = 10, this.tolerance = 1e-7;
  }
  solve(e, t) {
    let n = 0;
    const i = this.iterations, s = this.tolerance * this.tolerance, o = this.equations, r = o.length, l = t.bodies, a = l.length, c = e;
    let d, u, m, g, p, f;
    if (r !== 0)
      for (let x = 0; x !== a; x++)
        l[x].updateSolveMassProperties();
    const v = Kd, _ = Jd, w = $d;
    v.length = r, _.length = r, w.length = r;
    for (let x = 0; x !== r; x++) {
      const M = o[x];
      w[x] = 0, _[x] = M.computeB(c), v[x] = 1 / M.computeC();
    }
    if (r !== 0) {
      for (let E = 0; E !== a; E++) {
        const R = l[E], y = R.vlambda, A = R.wlambda;
        y.set(0, 0, 0), A.set(0, 0, 0);
      }
      for (n = 0; n !== i; n++) {
        g = 0;
        for (let E = 0; E !== r; E++) {
          const R = o[E];
          d = _[E], u = v[E], f = w[E], p = R.computeGWlambda(), m = u * (d - p - R.eps * f), f + m < R.minForce ? m = R.minForce - f : f + m > R.maxForce && (m = R.maxForce - f), w[E] += m, g += m > 0 ? m : -m, R.addToWlambda(m);
        }
        if (g * g < s)
          break;
      }
      for (let E = 0; E !== a; E++) {
        const R = l[E], y = R.velocity, A = R.angularVelocity;
        R.vlambda.vmul(R.linearFactor, R.vlambda), y.vadd(R.vlambda, y), R.wlambda.vmul(R.angularFactor, R.wlambda), A.vadd(R.wlambda, A);
      }
      let x = o.length;
      const M = 1 / c;
      for (; x--; )
        o[x].multiplier = w[x] * M;
    }
    return n;
  }
}
const $d = [], Kd = [], Jd = [];
ie.STATIC;
class Qd {
  constructor() {
    this.objects = [], this.type = Object;
  }
  release() {
    const e = arguments.length;
    for (let t = 0; t !== e; t++)
      this.objects.push(t < 0 || arguments.length <= t ? void 0 : arguments[t]);
    return this;
  }
  get() {
    return this.objects.length === 0 ? this.constructObject() : this.objects.pop();
  }
  constructObject() {
    throw new Error("constructObject() not implemented in this Pool subclass yet!");
  }
  resize(e) {
    const t = this.objects;
    for (; t.length > e; )
      t.pop();
    for (; t.length < e; )
      t.push(this.constructObject());
    return this;
  }
}
class ef extends Qd {
  constructor() {
    super(...arguments), this.type = b;
  }
  constructObject() {
    return new b();
  }
}
const Ue = {
  sphereSphere: le.types.SPHERE,
  spherePlane: le.types.SPHERE | le.types.PLANE,
  boxBox: le.types.BOX | le.types.BOX,
  sphereBox: le.types.SPHERE | le.types.BOX,
  planeBox: le.types.PLANE | le.types.BOX,
  convexConvex: le.types.CONVEXPOLYHEDRON,
  sphereConvex: le.types.SPHERE | le.types.CONVEXPOLYHEDRON,
  planeConvex: le.types.PLANE | le.types.CONVEXPOLYHEDRON,
  boxConvex: le.types.BOX | le.types.CONVEXPOLYHEDRON,
  sphereHeightfield: le.types.SPHERE | le.types.HEIGHTFIELD,
  boxHeightfield: le.types.BOX | le.types.HEIGHTFIELD,
  convexHeightfield: le.types.CONVEXPOLYHEDRON | le.types.HEIGHTFIELD,
  sphereParticle: le.types.PARTICLE | le.types.SPHERE,
  planeParticle: le.types.PLANE | le.types.PARTICLE,
  boxParticle: le.types.BOX | le.types.PARTICLE,
  convexParticle: le.types.PARTICLE | le.types.CONVEXPOLYHEDRON,
  cylinderCylinder: le.types.CYLINDER,
  sphereCylinder: le.types.SPHERE | le.types.CYLINDER,
  planeCylinder: le.types.PLANE | le.types.CYLINDER,
  boxCylinder: le.types.BOX | le.types.CYLINDER,
  convexCylinder: le.types.CONVEXPOLYHEDRON | le.types.CYLINDER,
  heightfieldCylinder: le.types.HEIGHTFIELD | le.types.CYLINDER,
  particleCylinder: le.types.PARTICLE | le.types.CYLINDER,
  sphereTrimesh: le.types.SPHERE | le.types.TRIMESH,
  planeTrimesh: le.types.PLANE | le.types.TRIMESH
};
class tf {
  get [Ue.sphereSphere]() {
    return this.sphereSphere;
  }
  get [Ue.spherePlane]() {
    return this.spherePlane;
  }
  get [Ue.boxBox]() {
    return this.boxBox;
  }
  get [Ue.sphereBox]() {
    return this.sphereBox;
  }
  get [Ue.planeBox]() {
    return this.planeBox;
  }
  get [Ue.convexConvex]() {
    return this.convexConvex;
  }
  get [Ue.sphereConvex]() {
    return this.sphereConvex;
  }
  get [Ue.planeConvex]() {
    return this.planeConvex;
  }
  get [Ue.boxConvex]() {
    return this.boxConvex;
  }
  get [Ue.sphereHeightfield]() {
    return this.sphereHeightfield;
  }
  get [Ue.boxHeightfield]() {
    return this.boxHeightfield;
  }
  get [Ue.convexHeightfield]() {
    return this.convexHeightfield;
  }
  get [Ue.sphereParticle]() {
    return this.sphereParticle;
  }
  get [Ue.planeParticle]() {
    return this.planeParticle;
  }
  get [Ue.boxParticle]() {
    return this.boxParticle;
  }
  get [Ue.convexParticle]() {
    return this.convexParticle;
  }
  get [Ue.cylinderCylinder]() {
    return this.convexConvex;
  }
  get [Ue.sphereCylinder]() {
    return this.sphereConvex;
  }
  get [Ue.planeCylinder]() {
    return this.planeConvex;
  }
  get [Ue.boxCylinder]() {
    return this.boxConvex;
  }
  get [Ue.convexCylinder]() {
    return this.convexConvex;
  }
  get [Ue.heightfieldCylinder]() {
    return this.heightfieldCylinder;
  }
  get [Ue.particleCylinder]() {
    return this.particleCylinder;
  }
  get [Ue.sphereTrimesh]() {
    return this.sphereTrimesh;
  }
  get [Ue.planeTrimesh]() {
    return this.planeTrimesh;
  }
  constructor(e) {
    this.contactPointPool = [], this.frictionEquationPool = [], this.result = [], this.frictionResult = [], this.v3pool = new ef(), this.world = e, this.currentContactMaterial = e.defaultContactMaterial, this.enableFrictionReduction = !1;
  }
  createContactEquation(e, t, n, i, s, o) {
    let r;
    this.contactPointPool.length ? (r = this.contactPointPool.pop(), r.bi = e, r.bj = t) : r = new Bd(e, t), r.enabled = e.collisionResponse && t.collisionResponse && n.collisionResponse && i.collisionResponse;
    const l = this.currentContactMaterial;
    r.restitution = l.restitution, r.setSpookParams(l.contactEquationStiffness, l.contactEquationRelaxation, this.world.dt);
    const a = n.material || e.material, c = i.material || t.material;
    return a && c && a.restitution >= 0 && c.restitution >= 0 && (r.restitution = a.restitution * c.restitution), r.si = s || n, r.sj = o || i, r;
  }
  createFrictionEquationsFromContact(e, t) {
    const n = e.bi, i = e.bj, s = e.si, o = e.sj, r = this.world, l = this.currentContactMaterial;
    let a = l.friction;
    const c = s.material || n.material, d = o.material || i.material;
    if (c && d && c.friction >= 0 && d.friction >= 0 && (a = c.friction * d.friction), a > 0) {
      const u = a * (r.frictionGravity || r.gravity).length();
      let m = n.invMass + i.invMass;
      m > 0 && (m = 1 / m);
      const g = this.frictionEquationPool, p = g.length ? g.pop() : new jr(n, i, u * m), f = g.length ? g.pop() : new jr(n, i, u * m);
      return p.bi = f.bi = n, p.bj = f.bj = i, p.minForce = f.minForce = -u * m, p.maxForce = f.maxForce = u * m, p.ri.copy(e.ri), p.rj.copy(e.rj), f.ri.copy(e.ri), f.rj.copy(e.rj), e.ni.tangents(p.t, f.t), p.setSpookParams(l.frictionEquationStiffness, l.frictionEquationRelaxation, r.dt), f.setSpookParams(l.frictionEquationStiffness, l.frictionEquationRelaxation, r.dt), p.enabled = f.enabled = e.enabled, t.push(p, f), !0;
    }
    return !1;
  }
  createFrictionFromAverage(e) {
    let t = this.result[this.result.length - 1];
    if (!this.createFrictionEquationsFromContact(t, this.frictionResult) || e === 1)
      return;
    const n = this.frictionResult[this.frictionResult.length - 2], i = this.frictionResult[this.frictionResult.length - 1];
    mn.setZero(), qn.setZero(), Xn.setZero();
    const s = t.bi;
    t.bj;
    for (let r = 0; r !== e; r++)
      t = this.result[this.result.length - 1 - r], t.bi !== s ? (mn.vadd(t.ni, mn), qn.vadd(t.ri, qn), Xn.vadd(t.rj, Xn)) : (mn.vsub(t.ni, mn), qn.vadd(t.rj, qn), Xn.vadd(t.ri, Xn));
    const o = 1 / e;
    qn.scale(o, n.ri), Xn.scale(o, n.rj), i.ri.copy(n.ri), i.rj.copy(n.rj), mn.normalize(), mn.tangents(n.t, i.t);
  }
  getContacts(e, t, n, i, s, o, r) {
    this.contactPointPool = s, this.frictionEquationPool = r, this.result = i, this.frictionResult = o;
    const l = rf, a = of, c = nf, d = sf;
    for (let u = 0, m = e.length; u !== m; u++) {
      const g = e[u], p = t[u];
      let f = null;
      g.material && p.material && (f = n.getContactMaterial(g.material, p.material) || null);
      const v = g.type & ie.KINEMATIC && p.type & ie.STATIC || g.type & ie.STATIC && p.type & ie.KINEMATIC || g.type & ie.KINEMATIC && p.type & ie.KINEMATIC;
      for (let _ = 0; _ < g.shapes.length; _++) {
        g.quaternion.mult(g.shapeOrientations[_], l), g.quaternion.vmult(g.shapeOffsets[_], c), c.vadd(g.position, c);
        const w = g.shapes[_];
        for (let x = 0; x < p.shapes.length; x++) {
          p.quaternion.mult(p.shapeOrientations[x], a), p.quaternion.vmult(p.shapeOffsets[x], d), d.vadd(p.position, d);
          const M = p.shapes[x];
          if (!(w.collisionFilterMask & M.collisionFilterGroup && M.collisionFilterMask & w.collisionFilterGroup) || c.distanceTo(d) > w.boundingSphereRadius + M.boundingSphereRadius)
            continue;
          let E = null;
          w.material && M.material && (E = n.getContactMaterial(w.material, M.material) || null), this.currentContactMaterial = E || f || n.defaultContactMaterial;
          const R = w.type | M.type, y = this[R];
          if (y) {
            let A = !1;
            w.type < M.type ? A = y.call(this, w, M, c, d, l, a, g, p, w, M, v) : A = y.call(this, M, w, d, c, a, l, p, g, w, M, v), A && v && (n.shapeOverlapKeeper.set(w.id, M.id), n.bodyOverlapKeeper.set(g.id, p.id));
          }
        }
      }
    }
  }
  sphereSphere(e, t, n, i, s, o, r, l, a, c, d) {
    if (d)
      return n.distanceSquared(i) < (e.radius + t.radius) ** 2;
    const u = this.createContactEquation(r, l, e, t, a, c);
    i.vsub(n, u.ni), u.ni.normalize(), u.ri.copy(u.ni), u.rj.copy(u.ni), u.ri.scale(e.radius, u.ri), u.rj.scale(-t.radius, u.rj), u.ri.vadd(n, u.ri), u.ri.vsub(r.position, u.ri), u.rj.vadd(i, u.rj), u.rj.vsub(l.position, u.rj), this.result.push(u), this.createFrictionEquationsFromContact(u, this.frictionResult);
  }
  spherePlane(e, t, n, i, s, o, r, l, a, c, d) {
    const u = this.createContactEquation(r, l, e, t, a, c);
    if (u.ni.set(0, 0, 1), o.vmult(u.ni, u.ni), u.ni.negate(u.ni), u.ni.normalize(), u.ni.scale(e.radius, u.ri), n.vsub(i, Gi), u.ni.scale(u.ni.dot(Gi), Yr), Gi.vsub(Yr, u.rj), -Gi.dot(u.ni) <= e.radius) {
      if (d)
        return !0;
      const m = u.ri, g = u.rj;
      m.vadd(n, m), m.vsub(r.position, m), g.vadd(i, g), g.vsub(l.position, g), this.result.push(u), this.createFrictionEquationsFromContact(u, this.frictionResult);
    }
  }
  boxBox(e, t, n, i, s, o, r, l, a, c, d) {
    return e.convexPolyhedronRepresentation.material = e.material, t.convexPolyhedronRepresentation.material = t.material, e.convexPolyhedronRepresentation.collisionResponse = e.collisionResponse, t.convexPolyhedronRepresentation.collisionResponse = t.collisionResponse, this.convexConvex(e.convexPolyhedronRepresentation, t.convexPolyhedronRepresentation, n, i, s, o, r, l, e, t, d);
  }
  sphereBox(e, t, n, i, s, o, r, l, a, c, d) {
    const u = this.v3pool, m = Df;
    n.vsub(i, ki), t.getSideNormals(m, o);
    const g = e.radius;
    let p = !1;
    const f = If, v = zf, _ = Bf;
    let w = null, x = 0, M = 0, E = 0, R = null;
    for (let D = 0, q = m.length; D !== q && p === !1; D++) {
      const k = Lf;
      k.copy(m[D]);
      const N = k.length();
      k.normalize();
      const H = ki.dot(k);
      if (H < N + g && H > 0) {
        const J = Rf, V = Ff;
        J.copy(m[(D + 1) % 3]), V.copy(m[(D + 2) % 3]);
        const ee = J.length(), ce = V.length();
        J.normalize(), V.normalize();
        const ge = ki.dot(J), $ = ki.dot(V);
        if (ge < ee && ge > -ee && $ < ce && $ > -ce) {
          const De = Math.abs(H - N - g);
          if ((R === null || De < R) && (R = De, M = ge, E = $, w = N, f.copy(k), v.copy(J), _.copy(V), x++, d))
            return !0;
        }
      }
    }
    if (x) {
      p = !0;
      const D = this.createContactEquation(r, l, e, t, a, c);
      f.scale(-g, D.ri), D.ni.copy(f), D.ni.negate(D.ni), f.scale(w, f), v.scale(M, v), f.vadd(v, f), _.scale(E, _), f.vadd(_, D.rj), D.ri.vadd(n, D.ri), D.ri.vsub(r.position, D.ri), D.rj.vadd(i, D.rj), D.rj.vsub(l.position, D.rj), this.result.push(D), this.createFrictionEquationsFromContact(D, this.frictionResult);
    }
    let y = u.get();
    const A = Pf;
    for (let D = 0; D !== 2 && !p; D++)
      for (let q = 0; q !== 2 && !p; q++)
        for (let k = 0; k !== 2 && !p; k++)
          if (y.set(0, 0, 0), D ? y.vadd(m[0], y) : y.vsub(m[0], y), q ? y.vadd(m[1], y) : y.vsub(m[1], y), k ? y.vadd(m[2], y) : y.vsub(m[2], y), i.vadd(y, A), A.vsub(n, A), A.lengthSquared() < g * g) {
            if (d)
              return !0;
            p = !0;
            const N = this.createContactEquation(r, l, e, t, a, c);
            N.ri.copy(A), N.ri.normalize(), N.ni.copy(N.ri), N.ri.scale(g, N.ri), N.rj.copy(y), N.ri.vadd(n, N.ri), N.ri.vsub(r.position, N.ri), N.rj.vadd(i, N.rj), N.rj.vsub(l.position, N.rj), this.result.push(N), this.createFrictionEquationsFromContact(N, this.frictionResult);
          }
    u.release(y), y = null;
    const F = u.get(), P = u.get(), G = u.get(), z = u.get(), L = u.get(), I = m.length;
    for (let D = 0; D !== I && !p; D++)
      for (let q = 0; q !== I && !p; q++)
        if (D % 3 !== q % 3) {
          m[q].cross(m[D], F), F.normalize(), m[D].vadd(m[q], P), G.copy(n), G.vsub(P, G), G.vsub(i, G);
          const k = G.dot(F);
          F.scale(k, z);
          let N = 0;
          for (; N === D % 3 || N === q % 3; )
            N++;
          L.copy(n), L.vsub(z, L), L.vsub(P, L), L.vsub(i, L);
          const H = Math.abs(k), J = L.length();
          if (H < m[N].length() && J < g) {
            if (d)
              return !0;
            p = !0;
            const V = this.createContactEquation(r, l, e, t, a, c);
            P.vadd(z, V.rj), V.rj.copy(V.rj), L.negate(V.ni), V.ni.normalize(), V.ri.copy(V.rj), V.ri.vadd(i, V.ri), V.ri.vsub(n, V.ri), V.ri.normalize(), V.ri.scale(g, V.ri), V.ri.vadd(n, V.ri), V.ri.vsub(r.position, V.ri), V.rj.vadd(i, V.rj), V.rj.vsub(l.position, V.rj), this.result.push(V), this.createFrictionEquationsFromContact(V, this.frictionResult);
          }
        }
    u.release(F, P, G, z, L);
  }
  planeBox(e, t, n, i, s, o, r, l, a, c, d) {
    return t.convexPolyhedronRepresentation.material = t.material, t.convexPolyhedronRepresentation.collisionResponse = t.collisionResponse, t.convexPolyhedronRepresentation.id = t.id, this.planeConvex(e, t.convexPolyhedronRepresentation, n, i, s, o, r, l, e, t, d);
  }
  convexConvex(e, t, n, i, s, o, r, l, a, c, d, u, m) {
    const g = Kf;
    if (!(n.distanceTo(i) > e.boundingSphereRadius + t.boundingSphereRadius) && e.findSeparatingAxis(t, n, s, i, o, g, u, m)) {
      const p = [], f = Jf;
      e.clipAgainstHull(n, s, t, i, o, g, -100, 100, p);
      let v = 0;
      for (let _ = 0; _ !== p.length; _++) {
        if (d)
          return !0;
        const w = this.createContactEquation(r, l, e, t, a, c), x = w.ri, M = w.rj;
        g.negate(w.ni), p[_].normal.negate(f), f.scale(p[_].depth, f), p[_].point.vadd(f, x), M.copy(p[_].point), x.vsub(n, x), M.vsub(i, M), x.vadd(n, x), x.vsub(r.position, x), M.vadd(i, M), M.vsub(l.position, M), this.result.push(w), v++, this.enableFrictionReduction || this.createFrictionEquationsFromContact(w, this.frictionResult);
      }
      this.enableFrictionReduction && v && this.createFrictionFromAverage(v);
    }
  }
  sphereConvex(e, t, n, i, s, o, r, l, a, c, d) {
    const u = this.v3pool;
    n.vsub(i, Nf);
    const m = t.faceNormals, g = t.faces, p = t.vertices, f = e.radius;
    let v = !1;
    for (let _ = 0; _ !== p.length; _++) {
      const w = p[_], x = kf;
      o.vmult(w, x), i.vadd(x, x);
      const M = Gf;
      if (x.vsub(n, M), M.lengthSquared() < f * f) {
        if (d)
          return !0;
        v = !0;
        const E = this.createContactEquation(r, l, e, t, a, c);
        E.ri.copy(M), E.ri.normalize(), E.ni.copy(E.ri), E.ri.scale(f, E.ri), x.vsub(i, E.rj), E.ri.vadd(n, E.ri), E.ri.vsub(r.position, E.ri), E.rj.vadd(i, E.rj), E.rj.vsub(l.position, E.rj), this.result.push(E), this.createFrictionEquationsFromContact(E, this.frictionResult);
        return;
      }
    }
    for (let _ = 0, w = g.length; _ !== w && v === !1; _++) {
      const x = m[_], M = g[_], E = Wf;
      o.vmult(x, E);
      const R = Vf;
      o.vmult(p[M[0]], R), R.vadd(i, R);
      const y = Hf;
      E.scale(-f, y), n.vadd(y, y);
      const A = qf;
      y.vsub(R, A);
      const F = A.dot(E), P = Xf;
      if (n.vsub(R, P), F < 0 && P.dot(E) > 0) {
        const G = [];
        for (let z = 0, L = M.length; z !== L; z++) {
          const I = u.get();
          o.vmult(p[M[z]], I), i.vadd(I, I), G.push(I);
        }
        if (Cf(G, E, n)) {
          if (d)
            return !0;
          v = !0;
          const z = this.createContactEquation(r, l, e, t, a, c);
          E.scale(-f, z.ri), E.negate(z.ni);
          const L = u.get();
          E.scale(-F, L);
          const I = u.get();
          E.scale(-f, I), n.vsub(i, z.rj), z.rj.vadd(I, z.rj), z.rj.vadd(L, z.rj), z.rj.vadd(i, z.rj), z.rj.vsub(l.position, z.rj), z.ri.vadd(n, z.ri), z.ri.vsub(r.position, z.ri), u.release(L), u.release(I), this.result.push(z), this.createFrictionEquationsFromContact(z, this.frictionResult);
          for (let D = 0, q = G.length; D !== q; D++)
            u.release(G[D]);
          return;
        } else
          for (let z = 0; z !== M.length; z++) {
            const L = u.get(), I = u.get();
            o.vmult(p[M[(z + 1) % M.length]], L), o.vmult(p[M[(z + 2) % M.length]], I), i.vadd(L, L), i.vadd(I, I);
            const D = Of;
            I.vsub(L, D);
            const q = Uf;
            D.unit(q);
            const k = u.get(), N = u.get();
            n.vsub(L, N);
            const H = N.dot(q);
            q.scale(H, k), k.vadd(L, k);
            const J = u.get();
            if (k.vsub(n, J), H > 0 && H * H < D.lengthSquared() && J.lengthSquared() < f * f) {
              if (d)
                return !0;
              const V = this.createContactEquation(r, l, e, t, a, c);
              k.vsub(i, V.rj), k.vsub(n, V.ni), V.ni.normalize(), V.ni.scale(f, V.ri), V.rj.vadd(i, V.rj), V.rj.vsub(l.position, V.rj), V.ri.vadd(n, V.ri), V.ri.vsub(r.position, V.ri), this.result.push(V), this.createFrictionEquationsFromContact(V, this.frictionResult);
              for (let ee = 0, ce = G.length; ee !== ce; ee++)
                u.release(G[ee]);
              u.release(L), u.release(I), u.release(k), u.release(J), u.release(N);
              return;
            }
            u.release(L), u.release(I), u.release(k), u.release(J), u.release(N);
          }
        for (let z = 0, L = G.length; z !== L; z++)
          u.release(G[z]);
      }
    }
  }
  planeConvex(e, t, n, i, s, o, r, l, a, c, d) {
    const u = jf, m = Yf;
    m.set(0, 0, 1), s.vmult(m, m);
    let g = 0;
    const p = Zf;
    for (let f = 0; f !== t.vertices.length; f++)
      if (u.copy(t.vertices[f]), o.vmult(u, u), i.vadd(u, u), u.vsub(n, p), m.dot(p) <= 0) {
        if (d)
          return !0;
        const _ = this.createContactEquation(r, l, e, t, a, c), w = $f;
        m.scale(m.dot(p), w), u.vsub(w, w), w.vsub(n, _.ri), _.ni.copy(m), u.vsub(i, _.rj), _.ri.vadd(n, _.ri), _.ri.vsub(r.position, _.ri), _.rj.vadd(i, _.rj), _.rj.vsub(l.position, _.rj), this.result.push(_), g++, this.enableFrictionReduction || this.createFrictionEquationsFromContact(_, this.frictionResult);
      }
    this.enableFrictionReduction && g && this.createFrictionFromAverage(g);
  }
  boxConvex(e, t, n, i, s, o, r, l, a, c, d) {
    return e.convexPolyhedronRepresentation.material = e.material, e.convexPolyhedronRepresentation.collisionResponse = e.collisionResponse, this.convexConvex(e.convexPolyhedronRepresentation, t, n, i, s, o, r, l, e, t, d);
  }
  sphereHeightfield(e, t, n, i, s, o, r, l, a, c, d) {
    const u = t.data, m = e.radius, g = t.elementSize, p = hp, f = cp;
    Pe.pointToLocalFrame(i, o, n, f);
    let v = Math.floor((f.x - m) / g) - 1, _ = Math.ceil((f.x + m) / g) + 1, w = Math.floor((f.y - m) / g) - 1, x = Math.ceil((f.y + m) / g) + 1;
    if (_ < 0 || x < 0 || v > u.length || w > u[0].length)
      return;
    v < 0 && (v = 0), _ < 0 && (_ = 0), w < 0 && (w = 0), x < 0 && (x = 0), v >= u.length && (v = u.length - 1), _ >= u.length && (_ = u.length - 1), x >= u[0].length && (x = u[0].length - 1), w >= u[0].length && (w = u[0].length - 1);
    const M = [];
    t.getRectMinMax(v, w, _, x, M);
    const E = M[0], R = M[1];
    if (f.z - m > R || f.z + m < E)
      return;
    const y = this.result;
    for (let A = v; A < _; A++)
      for (let F = w; F < x; F++) {
        const P = y.length;
        let G = !1;
        if (t.getConvexTrianglePillar(A, F, !1), Pe.pointToWorldFrame(i, o, t.pillarOffset, p), n.distanceTo(p) < t.pillarConvex.boundingSphereRadius + e.boundingSphereRadius && (G = this.sphereConvex(e, t.pillarConvex, n, p, s, o, r, l, e, t, d)), d && G || (t.getConvexTrianglePillar(A, F, !0), Pe.pointToWorldFrame(i, o, t.pillarOffset, p), n.distanceTo(p) < t.pillarConvex.boundingSphereRadius + e.boundingSphereRadius && (G = this.sphereConvex(e, t.pillarConvex, n, p, s, o, r, l, e, t, d)), d && G))
          return !0;
        if (y.length - P > 2)
          return;
      }
  }
  boxHeightfield(e, t, n, i, s, o, r, l, a, c, d) {
    return e.convexPolyhedronRepresentation.material = e.material, e.convexPolyhedronRepresentation.collisionResponse = e.collisionResponse, this.convexHeightfield(e.convexPolyhedronRepresentation, t, n, i, s, o, r, l, e, t, d);
  }
  convexHeightfield(e, t, n, i, s, o, r, l, a, c, d) {
    const u = t.data, m = t.elementSize, g = e.boundingSphereRadius, p = ap, f = lp, v = op;
    Pe.pointToLocalFrame(i, o, n, v);
    let _ = Math.floor((v.x - g) / m) - 1, w = Math.ceil((v.x + g) / m) + 1, x = Math.floor((v.y - g) / m) - 1, M = Math.ceil((v.y + g) / m) + 1;
    if (w < 0 || M < 0 || _ > u.length || x > u[0].length)
      return;
    _ < 0 && (_ = 0), w < 0 && (w = 0), x < 0 && (x = 0), M < 0 && (M = 0), _ >= u.length && (_ = u.length - 1), w >= u.length && (w = u.length - 1), M >= u[0].length && (M = u[0].length - 1), x >= u[0].length && (x = u[0].length - 1);
    const E = [];
    t.getRectMinMax(_, x, w, M, E);
    const R = E[0], y = E[1];
    if (!(v.z - g > y || v.z + g < R))
      for (let A = _; A < w; A++)
        for (let F = x; F < M; F++) {
          let P = !1;
          if (t.getConvexTrianglePillar(A, F, !1), Pe.pointToWorldFrame(i, o, t.pillarOffset, p), n.distanceTo(p) < t.pillarConvex.boundingSphereRadius + e.boundingSphereRadius && (P = this.convexConvex(e, t.pillarConvex, n, p, s, o, r, l, null, null, d, f, null)), d && P || (t.getConvexTrianglePillar(A, F, !0), Pe.pointToWorldFrame(i, o, t.pillarOffset, p), n.distanceTo(p) < t.pillarConvex.boundingSphereRadius + e.boundingSphereRadius && (P = this.convexConvex(e, t.pillarConvex, n, p, s, o, r, l, null, null, d, f, null)), d && P))
            return !0;
        }
  }
  sphereParticle(e, t, n, i, s, o, r, l, a, c, d) {
    const u = np;
    if (u.set(0, 0, 1), i.vsub(n, u), u.lengthSquared() <= e.radius * e.radius) {
      if (d)
        return !0;
      const g = this.createContactEquation(l, r, t, e, a, c);
      u.normalize(), g.rj.copy(u), g.rj.scale(e.radius, g.rj), g.ni.copy(u), g.ni.negate(g.ni), g.ri.set(0, 0, 0), this.result.push(g), this.createFrictionEquationsFromContact(g, this.frictionResult);
    }
  }
  planeParticle(e, t, n, i, s, o, r, l, a, c, d) {
    const u = Qf;
    u.set(0, 0, 1), r.quaternion.vmult(u, u);
    const m = ep;
    if (i.vsub(r.position, m), u.dot(m) <= 0) {
      if (d)
        return !0;
      const p = this.createContactEquation(l, r, t, e, a, c);
      p.ni.copy(u), p.ni.negate(p.ni), p.ri.set(0, 0, 0);
      const f = tp;
      u.scale(u.dot(i), f), i.vsub(f, f), p.rj.copy(f), this.result.push(p), this.createFrictionEquationsFromContact(p, this.frictionResult);
    }
  }
  boxParticle(e, t, n, i, s, o, r, l, a, c, d) {
    return e.convexPolyhedronRepresentation.material = e.material, e.convexPolyhedronRepresentation.collisionResponse = e.collisionResponse, this.convexParticle(e.convexPolyhedronRepresentation, t, n, i, s, o, r, l, e, t, d);
  }
  convexParticle(e, t, n, i, s, o, r, l, a, c, d) {
    let u = -1;
    const m = sp, g = rp;
    let p = null;
    const f = ip;
    if (f.copy(i), f.vsub(n, f), s.conjugate(Zr), Zr.vmult(f, f), e.pointIsInside(f)) {
      e.worldVerticesNeedsUpdate && e.computeWorldVertices(n, s), e.worldFaceNormalsNeedsUpdate && e.computeWorldFaceNormals(s);
      for (let v = 0, _ = e.faces.length; v !== _; v++) {
        const w = [e.worldVertices[e.faces[v][0]]], x = e.worldFaceNormals[v];
        i.vsub(w[0], $r);
        const M = -x.dot($r);
        if (p === null || Math.abs(M) < Math.abs(p)) {
          if (d)
            return !0;
          p = M, u = v, m.copy(x);
        }
      }
      if (u !== -1) {
        const v = this.createContactEquation(l, r, t, e, a, c);
        m.scale(p, g), g.vadd(i, g), g.vsub(n, g), v.rj.copy(g), m.negate(v.ni), v.ri.set(0, 0, 0);
        const _ = v.ri, w = v.rj;
        _.vadd(i, _), _.vsub(l.position, _), w.vadd(n, w), w.vsub(r.position, w), this.result.push(v), this.createFrictionEquationsFromContact(v, this.frictionResult);
      } else
        console.warn("Point found inside convex, but did not find penetrating face!");
    }
  }
  heightfieldCylinder(e, t, n, i, s, o, r, l, a, c, d) {
    return this.convexHeightfield(t, e, i, n, o, s, l, r, a, c, d);
  }
  particleCylinder(e, t, n, i, s, o, r, l, a, c, d) {
    return this.convexParticle(t, e, i, n, o, s, l, r, a, c, d);
  }
  sphereTrimesh(e, t, n, i, s, o, r, l, a, c, d) {
    const u = pf, m = mf, g = gf, p = _f, f = vf, v = xf, _ = Mf, w = ff, x = uf, M = Sf;
    Pe.pointToLocalFrame(i, o, n, f);
    const E = e.radius;
    _.lowerBound.set(f.x - E, f.y - E, f.z - E), _.upperBound.set(f.x + E, f.y + E, f.z + E), t.getTrianglesInAABB(_, M);
    const R = df, y = e.radius * e.radius;
    for (let z = 0; z < M.length; z++)
      for (let L = 0; L < 3; L++)
        if (t.getVertex(t.indices[M[z] * 3 + L], R), R.vsub(f, x), x.lengthSquared() <= y) {
          if (w.copy(R), Pe.pointToWorldFrame(i, o, w, R), R.vsub(n, x), d)
            return !0;
          let I = this.createContactEquation(r, l, e, t, a, c);
          I.ni.copy(x), I.ni.normalize(), I.ri.copy(I.ni), I.ri.scale(e.radius, I.ri), I.ri.vadd(n, I.ri), I.ri.vsub(r.position, I.ri), I.rj.copy(R), I.rj.vsub(l.position, I.rj), this.result.push(I), this.createFrictionEquationsFromContact(I, this.frictionResult);
        }
    for (let z = 0; z < M.length; z++)
      for (let L = 0; L < 3; L++) {
        t.getVertex(t.indices[M[z] * 3 + L], u), t.getVertex(t.indices[M[z] * 3 + (L + 1) % 3], m), m.vsub(u, g), f.vsub(m, v);
        const I = v.dot(g);
        f.vsub(u, v);
        let D = v.dot(g);
        if (D > 0 && I < 0 && (f.vsub(u, v), p.copy(g), p.normalize(), D = v.dot(p), p.scale(D, v), v.vadd(u, v), v.distanceTo(f) < e.radius)) {
          if (d)
            return !0;
          const k = this.createContactEquation(r, l, e, t, a, c);
          v.vsub(f, k.ni), k.ni.normalize(), k.ni.scale(e.radius, k.ri), k.ri.vadd(n, k.ri), k.ri.vsub(r.position, k.ri), Pe.pointToWorldFrame(i, o, v, v), v.vsub(l.position, k.rj), Pe.vectorToWorldFrame(o, k.ni, k.ni), Pe.vectorToWorldFrame(o, k.ri, k.ri), this.result.push(k), this.createFrictionEquationsFromContact(k, this.frictionResult);
        }
      }
    const A = yf, F = bf, P = wf, G = hf;
    for (let z = 0, L = M.length; z !== L; z++) {
      t.getTriangleVertices(M[z], A, F, P), t.getNormal(M[z], G), f.vsub(A, v);
      let I = v.dot(G);
      if (G.scale(I, v), f.vsub(v, v), I = v.distanceTo(f), Xe.pointInTriangle(v, A, F, P) && I < e.radius) {
        if (d)
          return !0;
        let D = this.createContactEquation(r, l, e, t, a, c);
        v.vsub(f, D.ni), D.ni.normalize(), D.ni.scale(e.radius, D.ri), D.ri.vadd(n, D.ri), D.ri.vsub(r.position, D.ri), Pe.pointToWorldFrame(i, o, v, v), v.vsub(l.position, D.rj), Pe.vectorToWorldFrame(o, D.ni, D.ni), Pe.vectorToWorldFrame(o, D.ri, D.ri), this.result.push(D), this.createFrictionEquationsFromContact(D, this.frictionResult);
      }
    }
    M.length = 0;
  }
  planeTrimesh(e, t, n, i, s, o, r, l, a, c, d) {
    const u = new b(), m = af;
    m.set(0, 0, 1), s.vmult(m, m);
    for (let g = 0; g < t.vertices.length / 3; g++) {
      t.getVertex(g, u);
      const p = new b();
      p.copy(u), Pe.pointToWorldFrame(i, o, p, u);
      const f = lf;
      if (u.vsub(n, f), m.dot(f) <= 0) {
        if (d)
          return !0;
        const _ = this.createContactEquation(r, l, e, t, a, c);
        _.ni.copy(m);
        const w = cf;
        m.scale(f.dot(m), w), u.vsub(w, w), _.ri.copy(w), _.ri.vsub(r.position, _.ri), _.rj.copy(u), _.rj.vsub(l.position, _.rj), this.result.push(_), this.createFrictionEquationsFromContact(_, this.frictionResult);
      }
    }
  }
}
const mn = new b(), qn = new b(), Xn = new b(), nf = new b(), sf = new b(), rf = new je(), of = new je(), af = new b(), lf = new b(), cf = new b(), hf = new b(), uf = new b();
new b();
const df = new b(), ff = new b(), pf = new b(), mf = new b(), gf = new b(), _f = new b(), vf = new b(), xf = new b(), yf = new b(), bf = new b(), wf = new b(), Mf = new vt(), Sf = [], Gi = new b(), Yr = new b(), Ef = new b(), Tf = new b(), Af = new b();
function Cf(h, e, t) {
  let n = null;
  const i = h.length;
  for (let s = 0; s !== i; s++) {
    const o = h[s], r = Ef;
    h[(s + 1) % i].vsub(o, r);
    const l = Tf;
    r.cross(e, l);
    const a = Af;
    t.vsub(o, a);
    const c = l.dot(a);
    if (n === null || c > 0 && n === !0 || c <= 0 && n === !1) {
      n === null && (n = c > 0);
      continue;
    } else
      return !1;
  }
  return !0;
}
const ki = new b(), Lf = new b(), Rf = new b(), Ff = new b(), Df = [new b(), new b(), new b(), new b(), new b(), new b()], Pf = new b(), If = new b(), zf = new b(), Bf = new b(), Nf = new b(), Of = new b(), Uf = new b(), Gf = new b(), kf = new b(), Wf = new b(), Vf = new b(), Hf = new b(), qf = new b(), Xf = new b();
new b();
new b();
const jf = new b(), Yf = new b(), Zf = new b(), $f = new b(), Kf = new b(), Jf = new b(), Qf = new b(), ep = new b(), tp = new b(), np = new b(), Zr = new je(), ip = new b();
new b();
const sp = new b(), $r = new b(), rp = new b(), op = new b(), ap = new b(), lp = [0], cp = new b(), hp = new b();
class Kr {
  constructor() {
    this.current = [], this.previous = [];
  }
  getKey(e, t) {
    if (t < e) {
      const n = t;
      t = e, e = n;
    }
    return e << 16 | t;
  }
  set(e, t) {
    const n = this.getKey(e, t), i = this.current;
    let s = 0;
    for (; n > i[s]; )
      s++;
    if (n !== i[s]) {
      for (let o = i.length - 1; o >= s; o--)
        i[o + 1] = i[o];
      i[s] = n;
    }
  }
  tick() {
    const e = this.current;
    this.current = this.previous, this.previous = e, this.current.length = 0;
  }
  getDiff(e, t) {
    const n = this.current, i = this.previous, s = n.length, o = i.length;
    let r = 0;
    for (let l = 0; l < s; l++) {
      let a = !1;
      const c = n[l];
      for (; c > i[r]; )
        r++;
      a = c === i[r], a || Jr(e, c);
    }
    r = 0;
    for (let l = 0; l < o; l++) {
      let a = !1;
      const c = i[l];
      for (; c > n[r]; )
        r++;
      a = n[r] === c, a || Jr(t, c);
    }
  }
}
function Jr(h, e) {
  h.push((e & 4294901760) >> 16, e & 65535);
}
const Fs = (h, e) => h < e ? `${h}-${e}` : `${e}-${h}`;
class up {
  constructor() {
    this.data = {
      keys: []
    };
  }
  get(e, t) {
    const n = Fs(e, t);
    return this.data[n];
  }
  set(e, t, n) {
    const i = Fs(e, t);
    this.get(e, t) || this.data.keys.push(i), this.data[i] = n;
  }
  delete(e, t) {
    const n = Fs(e, t), i = this.data.keys.indexOf(n);
    i !== -1 && this.data.keys.splice(i, 1), delete this.data[n];
  }
  reset() {
    const e = this.data, t = e.keys;
    for (; t.length > 0; ) {
      const n = t.pop();
      delete e[n];
    }
  }
}
class dp extends bo {
  constructor(e) {
    e === void 0 && (e = {}), super(), this.dt = -1, this.allowSleep = !!e.allowSleep, this.contacts = [], this.frictionEquations = [], this.quatNormalizeSkip = e.quatNormalizeSkip !== void 0 ? e.quatNormalizeSkip : 0, this.quatNormalizeFast = e.quatNormalizeFast !== void 0 ? e.quatNormalizeFast : !1, this.time = 0, this.stepnumber = 0, this.default_dt = 1 / 60, this.nextId = 0, this.gravity = new b(), e.gravity && this.gravity.copy(e.gravity), e.frictionGravity && (this.frictionGravity = new b(), this.frictionGravity.copy(e.frictionGravity)), this.broadphase = e.broadphase !== void 0 ? e.broadphase : new wo(), this.bodies = [], this.hasActiveBodies = !1, this.solver = e.solver !== void 0 ? e.solver : new Zd(), this.constraints = [], this.narrowphase = new tf(this), this.collisionMatrix = new Nr(), this.collisionMatrixPrevious = new Nr(), this.bodyOverlapKeeper = new Kr(), this.shapeOverlapKeeper = new Kr(), this.contactmaterials = [], this.contactMaterialTable = new up(), this.defaultMaterial = new Sn("default"), this.defaultContactMaterial = new Mn(this.defaultMaterial, this.defaultMaterial, {
      friction: 0.3,
      restitution: 0
    }), this.doProfiling = !1, this.profile = {
      solve: 0,
      makeContactConstraints: 0,
      broadphase: 0,
      integrate: 0,
      narrowphase: 0
    }, this.accumulator = 0, this.subsystems = [], this.addBodyEvent = {
      type: "addBody",
      body: null
    }, this.removeBodyEvent = {
      type: "removeBody",
      body: null
    }, this.idToBodyMap = {}, this.broadphase.setWorld(this);
  }
  getContactMaterial(e, t) {
    return this.contactMaterialTable.get(e.id, t.id);
  }
  collisionMatrixTick() {
    const e = this.collisionMatrixPrevious;
    this.collisionMatrixPrevious = this.collisionMatrix, this.collisionMatrix = e, this.collisionMatrix.reset(), this.bodyOverlapKeeper.tick(), this.shapeOverlapKeeper.tick();
  }
  addConstraint(e) {
    this.constraints.push(e);
  }
  removeConstraint(e) {
    const t = this.constraints.indexOf(e);
    t !== -1 && this.constraints.splice(t, 1);
  }
  rayTest(e, t, n) {
    n instanceof Xi ? this.raycastClosest(e, t, {
      skipBackfaces: !0
    }, n) : this.raycastAll(e, t, {
      skipBackfaces: !0
    }, n);
  }
  raycastAll(e, t, n, i) {
    return n === void 0 && (n = {}), n.mode = Xe.ALL, n.from = e, n.to = t, n.callback = i, Ds.intersectWorld(this, n);
  }
  raycastAny(e, t, n, i) {
    return n === void 0 && (n = {}), n.mode = Xe.ANY, n.from = e, n.to = t, n.result = i, Ds.intersectWorld(this, n);
  }
  raycastClosest(e, t, n, i) {
    return n === void 0 && (n = {}), n.mode = Xe.CLOSEST, n.from = e, n.to = t, n.result = i, Ds.intersectWorld(this, n);
  }
  addBody(e) {
    this.bodies.includes(e) || (e.index = this.bodies.length, this.bodies.push(e), e.world = this, e.initPosition.copy(e.position), e.initVelocity.copy(e.velocity), e.timeLastSleepy = this.time, e instanceof ie && (e.initAngularVelocity.copy(e.angularVelocity), e.initQuaternion.copy(e.quaternion)), this.collisionMatrix.setNumObjects(this.bodies.length), this.addBodyEvent.body = e, this.idToBodyMap[e.id] = e, this.dispatchEvent(this.addBodyEvent));
  }
  removeBody(e) {
    e.world = null;
    const t = this.bodies.length - 1, n = this.bodies, i = n.indexOf(e);
    if (i !== -1) {
      n.splice(i, 1);
      for (let s = 0; s !== n.length; s++)
        n[s].index = s;
      this.collisionMatrix.setNumObjects(t), this.removeBodyEvent.body = e, delete this.idToBodyMap[e.id], this.dispatchEvent(this.removeBodyEvent);
    }
  }
  getBodyById(e) {
    return this.idToBodyMap[e];
  }
  getShapeById(e) {
    const t = this.bodies;
    for (let n = 0; n < t.length; n++) {
      const i = t[n].shapes;
      for (let s = 0; s < i.length; s++) {
        const o = i[s];
        if (o.id === e)
          return o;
      }
    }
    return null;
  }
  addContactMaterial(e) {
    this.contactmaterials.push(e), this.contactMaterialTable.set(e.materials[0].id, e.materials[1].id, e);
  }
  removeContactMaterial(e) {
    const t = this.contactmaterials.indexOf(e);
    t !== -1 && (this.contactmaterials.splice(t, 1), this.contactMaterialTable.delete(e.materials[0].id, e.materials[1].id));
  }
  fixedStep(e, t) {
    e === void 0 && (e = 1 / 60), t === void 0 && (t = 10);
    const n = Ze.now() / 1e3;
    if (!this.lastCallTime)
      this.step(e, void 0, t);
    else {
      const i = n - this.lastCallTime;
      this.step(e, i, t);
    }
    this.lastCallTime = n;
  }
  step(e, t, n) {
    if (n === void 0 && (n = 10), t === void 0)
      this.internalStep(e), this.time += e;
    else {
      this.accumulator += t;
      const i = Ze.now();
      let s = 0;
      for (; this.accumulator >= e && s < n && (this.internalStep(e), this.accumulator -= e, s++, !(Ze.now() - i > e * 1e3)); )
        ;
      this.accumulator = this.accumulator % e;
      const o = this.accumulator / e;
      for (let r = 0; r !== this.bodies.length; r++) {
        const l = this.bodies[r];
        l.previousPosition.lerp(l.position, o, l.interpolatedPosition), l.previousQuaternion.slerp(l.quaternion, o, l.interpolatedQuaternion), l.previousQuaternion.normalize();
      }
      this.time += t;
    }
  }
  internalStep(e) {
    this.dt = e;
    const t = this.contacts, n = _p, i = vp, s = this.bodies.length, o = this.bodies, r = this.solver, l = this.gravity, a = this.doProfiling, c = this.profile, d = ie.DYNAMIC;
    let u = -1 / 0;
    const m = this.constraints, g = gp;
    l.length();
    const p = l.x, f = l.y, v = l.z;
    let _ = 0;
    for (a && (u = Ze.now()), _ = 0; _ !== s; _++) {
      const z = o[_];
      if (z.type === d) {
        const L = z.force, I = z.mass;
        L.x += I * p, L.y += I * f, L.z += I * v;
      }
    }
    for (let z = 0, L = this.subsystems.length; z !== L; z++)
      this.subsystems[z].update();
    a && (u = Ze.now()), n.length = 0, i.length = 0, this.broadphase.collisionPairs(this, n, i), a && (c.broadphase = Ze.now() - u);
    let w = m.length;
    for (_ = 0; _ !== w; _++) {
      const z = m[_];
      if (!z.collideConnected)
        for (let L = n.length - 1; L >= 0; L -= 1)
          (z.bodyA === n[L] && z.bodyB === i[L] || z.bodyB === n[L] && z.bodyA === i[L]) && (n.splice(L, 1), i.splice(L, 1));
    }
    this.collisionMatrixTick(), a && (u = Ze.now());
    const x = mp, M = t.length;
    for (_ = 0; _ !== M; _++)
      x.push(t[_]);
    t.length = 0;
    const E = this.frictionEquations.length;
    for (_ = 0; _ !== E; _++)
      g.push(this.frictionEquations[_]);
    for (this.frictionEquations.length = 0, this.narrowphase.getContacts(
      n,
      i,
      this,
      t,
      x,
      this.frictionEquations,
      g
    ), a && (c.narrowphase = Ze.now() - u), a && (u = Ze.now()), _ = 0; _ < this.frictionEquations.length; _++)
      r.addEquation(this.frictionEquations[_]);
    const R = t.length;
    for (let z = 0; z !== R; z++) {
      const L = t[z], I = L.bi, D = L.bj, q = L.si, k = L.sj;
      let N;
      if (I.material && D.material ? N = this.getContactMaterial(I.material, D.material) || this.defaultContactMaterial : N = this.defaultContactMaterial, N.friction, I.material && D.material && (I.material.friction >= 0 && D.material.friction >= 0 && I.material.friction * D.material.friction, I.material.restitution >= 0 && D.material.restitution >= 0 && (L.restitution = I.material.restitution * D.material.restitution)), r.addEquation(L), I.allowSleep && I.type === ie.DYNAMIC && I.sleepState === ie.SLEEPING && D.sleepState === ie.AWAKE && D.type !== ie.STATIC) {
        const H = D.velocity.lengthSquared() + D.angularVelocity.lengthSquared(), J = D.sleepSpeedLimit ** 2;
        H >= J * 2 && (I.wakeUpAfterNarrowphase = !0);
      }
      if (D.allowSleep && D.type === ie.DYNAMIC && D.sleepState === ie.SLEEPING && I.sleepState === ie.AWAKE && I.type !== ie.STATIC) {
        const H = I.velocity.lengthSquared() + I.angularVelocity.lengthSquared(), J = I.sleepSpeedLimit ** 2;
        H >= J * 2 && (D.wakeUpAfterNarrowphase = !0);
      }
      this.collisionMatrix.set(I, D, !0), this.collisionMatrixPrevious.get(I, D) || (ri.body = D, ri.contact = L, I.dispatchEvent(ri), ri.body = I, D.dispatchEvent(ri)), this.bodyOverlapKeeper.set(I.id, D.id), this.shapeOverlapKeeper.set(q.id, k.id);
    }
    for (this.emitContactEvents(), a && (c.makeContactConstraints = Ze.now() - u, u = Ze.now()), _ = 0; _ !== s; _++) {
      const z = o[_];
      z.wakeUpAfterNarrowphase && (z.wakeUp(), z.wakeUpAfterNarrowphase = !1);
    }
    for (w = m.length, _ = 0; _ !== w; _++) {
      const z = m[_];
      z.update();
      for (let L = 0, I = z.equations.length; L !== I; L++) {
        const D = z.equations[L];
        r.addEquation(D);
      }
    }
    r.solve(e, this), a && (c.solve = Ze.now() - u), r.removeAllEquations();
    const y = Math.pow;
    for (_ = 0; _ !== s; _++) {
      const z = o[_];
      if (z.type & d) {
        const L = y(1 - z.linearDamping, e), I = z.velocity;
        I.scale(L, I);
        const D = z.angularVelocity;
        if (D) {
          const q = y(1 - z.angularDamping, e);
          D.scale(q, D);
        }
      }
    }
    this.dispatchEvent(pp), a && (u = Ze.now());
    const F = this.stepnumber % (this.quatNormalizeSkip + 1) === 0, P = this.quatNormalizeFast;
    for (_ = 0; _ !== s; _++)
      o[_].integrate(e, F, P);
    this.clearForces(), this.broadphase.dirty = !0, a && (c.integrate = Ze.now() - u), this.stepnumber += 1, this.dispatchEvent(fp);
    let G = !0;
    if (this.allowSleep)
      for (G = !1, _ = 0; _ !== s; _++) {
        const z = o[_];
        z.sleepTick(this.time), z.sleepState !== ie.SLEEPING && (G = !0);
      }
    this.hasActiveBodies = G;
  }
  emitContactEvents() {
    const e = this.hasAnyEventListener("beginContact"), t = this.hasAnyEventListener("endContact");
    if ((e || t) && this.bodyOverlapKeeper.getDiff(Yt, Zt), e) {
      for (let s = 0, o = Yt.length; s < o; s += 2)
        oi.bodyA = this.getBodyById(Yt[s]), oi.bodyB = this.getBodyById(Yt[s + 1]), this.dispatchEvent(oi);
      oi.bodyA = oi.bodyB = null;
    }
    if (t) {
      for (let s = 0, o = Zt.length; s < o; s += 2)
        ai.bodyA = this.getBodyById(Zt[s]), ai.bodyB = this.getBodyById(Zt[s + 1]), this.dispatchEvent(ai);
      ai.bodyA = ai.bodyB = null;
    }
    Yt.length = Zt.length = 0;
    const n = this.hasAnyEventListener("beginShapeContact"), i = this.hasAnyEventListener("endShapeContact");
    if ((n || i) && this.shapeOverlapKeeper.getDiff(Yt, Zt), n) {
      for (let s = 0, o = Yt.length; s < o; s += 2) {
        const r = this.getShapeById(Yt[s]), l = this.getShapeById(Yt[s + 1]);
        $t.shapeA = r, $t.shapeB = l, r && ($t.bodyA = r.body), l && ($t.bodyB = l.body), this.dispatchEvent($t);
      }
      $t.bodyA = $t.bodyB = $t.shapeA = $t.shapeB = null;
    }
    if (i) {
      for (let s = 0, o = Zt.length; s < o; s += 2) {
        const r = this.getShapeById(Zt[s]), l = this.getShapeById(Zt[s + 1]);
        Kt.shapeA = r, Kt.shapeB = l, r && (Kt.bodyA = r.body), l && (Kt.bodyB = l.body), this.dispatchEvent(Kt);
      }
      Kt.bodyA = Kt.bodyB = Kt.shapeA = Kt.shapeB = null;
    }
  }
  clearForces() {
    const e = this.bodies, t = e.length;
    for (let n = 0; n !== t; n++) {
      const i = e[n];
      i.force, i.torque, i.force.set(0, 0, 0), i.torque.set(0, 0, 0);
    }
  }
}
new vt();
const Ds = new Xe(), Ze = globalThis.performance || {};
if (!Ze.now) {
  let h = Date.now();
  Ze.timing && Ze.timing.navigationStart && (h = Ze.timing.navigationStart), Ze.now = () => Date.now() - h;
}
new b();
const fp = {
  type: "postStep"
}, pp = {
  type: "preStep"
}, ri = {
  type: ie.COLLIDE_EVENT_NAME,
  body: null,
  contact: null
}, mp = [], gp = [], _p = [], vp = [], Yt = [], Zt = [], oi = {
  type: "beginContact",
  bodyA: null,
  bodyB: null
}, ai = {
  type: "endContact",
  bodyA: null,
  bodyB: null
}, $t = {
  type: "beginShapeContact",
  bodyA: null,
  bodyB: null,
  shapeA: null,
  shapeB: null
}, Kt = {
  type: "endShapeContact",
  bodyA: null,
  bodyB: null,
  shapeA: null,
  shapeB: null
};
class Qr {
  constructor(e) {
    typeof e == "object" && (e = e.notation), this.set = [], this.setkeys = [], this.setid = 0, this.groups = [], this.totalDice = 0, this.op = "", this.constant = null, this.result = [], this.error = !1, this.boost = 1, this.notation = "", this.vectors = [], (!e || e == "0") && (this.error = !0), this.parseNotation(e);
  }
  parseNotation(e) {
    if (e) {
      let u = e.split("!").length - 1 || 0;
      u > 0 && (this.boost = Math.min(Math.max(u, 0), 3) * 4), e = e.split("!").join(""), e = e.split(" ").join("");
      let m = e.split("(").length - 1, g = e.split(")").length - 1;
      m != g && (this.error = !0);
    }
    const t = this.notation.length > 0 ? "+" : "";
    this.notation += t + e;
    let n = e.split("@"), i = n[0], s = new RegExp(/(\+|\-|\*|\/|\%|\^|){0,1}()(\d*)([a-z]+\d+|[a-z]+|)(?:\{([a-z]+)(.*?|)\}|)()/, "i"), o = new RegExp(/(\b)*(\-\d+|\d+)(\b)*/, "gi"), r, l = 0, a = 30, c = 0, d = 0;
    for (; !this.error && i.length > 0 && (r = s.exec(i)) !== null && l < a; ) {
      l++, i = i.substring(r[0].length);
      let u = r[1], m = r[2] && r[2].length > 0, g = r[3], p = r[4], f = r[5] || "", v = r[6] || "", _ = r[7] && r[7].length > 0, w = !0;
      m && (c += r[2].length), v = v.split(","), (!v || v.length < 1) && (v = ""), v.shift(), l == 1 && i.length == 0 && !p && u && g ? (p = "d20", this.op = u, this.constant = parseInt(g), g = 1) : l > 1 && i.length == 0 && !p && (this.op = u, this.constant = parseInt(g), w = !1), w && this.addSet(g, p, d, c, f, v, u), _ && (c -= r[7].length, d += r[7].length);
    }
    !this.error && n[1] && (r = n[1].match(o)) !== null && this.result.push(...r);
  }
  stringify(e = !0) {
    let t = "";
    if (this.set.length < 1)
      return t;
    for (let n = 0; n < this.set.length; n++) {
      let i = this.set[n];
      t += n > 0 && i.op ? i.op : "", t += i.num + i.type, i.func && (t += "{", t += i.func ? i.func : "", t += i.args ? "," + (Array.isArray(i.args) ? i.args.join(",") : i.args) : "", t += "}");
    }
    return t += this.constant ? this.op + "" + Math.abs(this.constant) : "", e && this.result && this.result.length > 0 && (t += "@" + this.result.join(",")), this.boost > 1 && (t += "!".repeat(this.boost / 4)), t;
  }
  addSet(e, t, n = 0, i = 0, s = "", o = "", r = "+") {
    e = Math.abs(parseInt(e || 1));
    let l = r + "" + t + n + i + s + o, a = this.setkeys[l] != null, c = {};
    a && (c = this.set[this.setkeys[l] - 1]), e > 0 && (c.num = a ? e + c.num : e, c.type = t, c.sid = this.setid, c.gid = n, c.glvl = i, s && (c.func = s), o && (c.args = o), r && (c.op = r), a ? this.set[this.setkeys[l] - 1] = c : this.setkeys[l] = this.set.push(c)), a || ++this.setid;
  }
  static mergeNotation(e, t) {
    return {
      ...e,
      constant: e.constant + t.constant,
      notation: e.notation + "+" + t.notation,
      set: [
        ...e.set,
        ...t.set
      ],
      totalDice: e.vectors.length + t.vectors.length,
      vectors: [
        ...e.vectors,
        ...t.vectors
      ]
    };
  }
}
const Ps = {
  d2: {
    name: "d2",
    labels: ["1", "2"],
    values: [1, 2],
    inertia: 8,
    mass: 400,
    scale: 0.9,
    system: "dweird"
  },
  dc: {
    type: "d2",
    name: "Coin",
    labels: [
      "textures/silvercoin/tail.png",
      "textures/silvercoin/heads.png"
    ],
    setBumpMaps: [
      "textures/silvercoin/tail_bump.png",
      "textures/silvercoin/heads_bump.png"
    ],
    values: [0, 1],
    inertia: 8,
    mass: 400,
    scale: 0.9,
    colorset: "coin_silver"
  },
  d1: {
    name: "One-sided Dice",
    type: "d6",
    labels: ["1"],
    values: [1, 1],
    scale: 0.9,
    system: "dweird"
  },
  d3: {
    name: "Three-Sided Dice",
    type: "d6",
    labels: ["1", "2", "3"],
    values: [1, 3],
    scale: 0.9,
    system: "dweird"
  },
  df: {
    name: "Fudge Dice",
    type: "d6",
    labels: ["-", "0", "+"],
    values: [-1, 1],
    scale: 0.9,
    system: "dweird"
  },
  d4: {
    name: "Four-Sided Dice",
    labels: ["1", "2", "3", "4"],
    values: [1, 4],
    inertia: 5,
    scale: 1.2
  },
  d6: {
    name: "Six-Sided Dice (Numbers)",
    labels: ["1", "2", "3", "4", "5", "6"],
    values: [1, 6],
    scale: 0.9
  },
  dpip: {
    name: "Six-Sided Dice (Pips)",
    type: "d6",
    labels: [
      `   
 \u2B24 
   `,
      `\u2B24  
   
  \u2B24`,
      `\u2B24  
 \u2B24 
  \u2B24`,
      `\u2B24 \u2B24
   
\u2B24 \u2B24`,
      `\u2B24 \u2B24
 \u2B24 
\u2B24 \u2B24`,
      `\u2B24 \u2B24
\u2B24 \u2B24
\u2B24 \u2B24`
    ],
    values: [1, 6],
    scale: 0.9,
    font: "monospace"
  },
  dsex: {
    name: "Sex-Sided Emoji Dice",
    type: "d6",
    labels: ["\u{1F346}", "\u{1F351}", "\u{1F44C}", "\u{1F4A6}", "\u{1F64F}", "\u{1F4A5}"],
    values: [1, 6],
    scale: 0.9,
    display: "labels",
    system: "dweird"
  },
  dpoker: {
    name: "Poker Dice (9-Ace)",
    type: "d6",
    labels: ["A", "9", "10", "J", "Q", "K"],
    values: [1, 6],
    scale: 0.9,
    display: "labels",
    system: "dweird",
    font: "Times New Roman"
  },
  dspanpoker: {
    name: "Spanish Poker Dice (7-Ace)",
    type: "d8",
    labels: ["A", "7", "8", "9", "10", "J", "Q", "K"],
    values: [1, 8],
    display: "labels",
    system: "dweird",
    font: "Times New Roman"
  },
  disotope: {
    name: "Radioactive Twelve-Sided Dice",
    type: "d12",
    labels: ["", "", "", "", "", "", "", "", "", "", "", "\u2622\uFE0F"],
    values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    mass: 350,
    inertia: 8,
    scale: 0.9,
    system: "dweird"
  },
  dsuit: {
    name: "Four-Suited Dice",
    type: "d4",
    labels: ["\u2660\uFE0F", "\u2665\uFE0F", "\u2666\uFE0F", "\u2663\uFE0F"],
    values: [1, 4],
    inertia: 5,
    scale: 1.2,
    display: "labels",
    system: "dweird"
  },
  d8: {
    name: "Eight-Sided Dice",
    labels: ["1", "2", "3", "4", "5", "6", "7", "8"],
    values: [1, 8]
  },
  d10: {
    name: "Ten-Sided Dice (Single Digit)",
    labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    values: [1, 10],
    mass: 350,
    inertia: 9,
    scale: 0.9
  },
  d100: {
    name: "Ten-Sided Dice (Tens Digit)",
    type: "d10",
    labels: ["10", "20", "30", "40", "50", "60", "70", "80", "90", "00"],
    values: [10, 100, 10],
    mass: 350,
    inertia: 9,
    scale: 0.9
  },
  d12: {
    name: "Twelve-Sided Dice",
    labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
    values: [1, 12],
    mass: 350,
    inertia: 8,
    scale: 0.9
  },
  d20: {
    name: "Twenty-Sided Dice",
    labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"],
    values: [1, 20],
    mass: 400,
    inertia: 6
  },
  dabi: {
    name: "Star Wars RPG: Ability Dice",
    type: "d8",
    labels: ["s", "a", `s
a`, `s
s`, "a", "s", `a
a`, ""],
    values: [1, 8],
    font: "SWRPG-Symbol-Regular",
    color: "#00FF00",
    colorset: "swrpg_abi",
    display: "labels",
    system: "swrpg"
  },
  ddif: {
    name: "Star Wars RPG: Difficulty Dice",
    type: "d8",
    labels: ["t", "f", `f
t`, "t", "", `t
t`, `f
f`, "t"],
    values: [1, 8],
    font: "SWRPG-Symbol-Regular",
    color: "#8000FC",
    colorset: "swrpg_dif",
    display: "labels",
    system: "swrpg"
  },
  dpro: {
    name: "Star Wars RPG: Proficiency Dice",
    type: "d12",
    labels: [`a
a`, "a", `a
a`, "x", "s", `s
a`, "s", `s
a`, `s
s`, `s
a`, `s
s`, ""],
    values: [1, 12],
    mass: 350,
    inertia: 8,
    scale: 0.9,
    font: "SWRPG-Symbol-Regular",
    color: "#FFFF00",
    colorset: "swrpg_pro",
    display: "labels",
    system: "swrpg"
  },
  dcha: {
    name: "Star Wars RPG: Challenge Dice",
    type: "d12",
    labels: [`t
t`, "t", `t
t`, "t", `t
f`, "f", `t
f`, "f", `f
f`, "y", `f
f`, ""],
    values: [1, 12],
    mass: 350,
    inertia: 8,
    scale: 0.9,
    font: "SWRPG-Symbol-Regular",
    color: "#FF0000",
    colorset: "swrpg_cha",
    display: "labels",
    system: "swrpg"
  },
  dfor: {
    name: "Star Wars RPG: Force Dice",
    type: "d12",
    labels: ["z", `Z
Z`, "z", `Z
Z`, "z", `Z
Z`, "z", "Z", "z", "Z", "z", `z
z`],
    values: [1, 12],
    mass: 350,
    inertia: 8,
    scale: 0.9,
    font: "SWRPG-Symbol-Regular",
    color: "#FFFFFF",
    colorset: "swrpg_for",
    display: "labels",
    system: "swrpg"
  },
  dboo: {
    name: "Star Wars RPG: Boost Dice",
    type: "d6",
    labels: [`s  
  a`, `a  
  a`, "s", "a", "", ""],
    values: [1, 6],
    scale: 0.9,
    font: "SWRPG-Symbol-Regular",
    color: "#00FFFF",
    colorset: "swrpg_boo",
    display: "labels",
    system: "swrpg"
  },
  dset: {
    name: "Star Wars RPG: Setback Dice",
    type: "d6",
    labels: ["", "t", "f"],
    values: [1, 3],
    scale: 0.9,
    font: "SWRPG-Symbol-Regular",
    color: "#111111",
    colorset: "swrpg_set",
    display: "labels",
    system: "swrpg"
  },
  swar: {
    name: "Star Wars Armada: Red Attack Dice",
    type: "d8",
    labels: ["F", "F", `F
F`, "E", "E", "G", "", ""],
    values: [1, 8],
    font: "Armada-Symbol-Regular",
    color: "#FF0000",
    colorset: "swa_red",
    display: "labels",
    system: "swarmada"
  },
  swab: {
    name: "Star Wars Armada: Blue Attack Dice",
    type: "d8",
    labels: ["F", "F", "F", "F", "E", "E", "G", "G"],
    values: [1, 8],
    font: "Armada-Symbol-Regular",
    color: "#0000FF",
    colorset: "swa_blue",
    display: "labels",
    system: "swarmada"
  },
  swak: {
    name: "Star Wars Armada: Black Attack Dice",
    type: "d8",
    labels: ["F", "F", "F", "F", `F
E`, `F
E`, "", ""],
    values: [1, 8],
    font: "Armada-Symbol-Regular",
    color: "#111111",
    colorset: "swa_black",
    display: "labels",
    system: "swarmada"
  },
  xwatk: {
    name: "Star Wars X-Wing: Red Attack Dice",
    type: "d8",
    labels: ["c", "d", "d", "d", "f", "f", "", ""],
    values: [1, 8],
    font: "XWing-Symbol-Regular",
    color: "#FF0000",
    colorset: "xwing_red",
    display: "labels",
    system: "xwing"
  },
  xwdef: {
    name: "Star Wars X-Wing: Green Defense Dice",
    type: "d8",
    labels: ["e", "e", "e", "f", "f", "", "", ""],
    values: [1, 8],
    font: "XWing-Symbol-Regular",
    color: "#00FF00",
    colorset: "xwing_green",
    display: "labels",
    system: "xwing"
  },
  swlar: {
    name: "Star Wars Legion: Red Attack Dice",
    type: "d8",
    labels: ["h", "h", "h", "h", "h", "c", "o", ""],
    values: [1, 8],
    font: "Legion-Symbol-Regular",
    color: "#FF0000",
    colorset: "swl_atkred",
    display: "labels",
    system: "legion"
  },
  swlab: {
    name: "Star Wars Legion: Black Attack Dice",
    type: "d8",
    labels: ["h", "h", "h", "", "", "c", "o", ""],
    values: [1, 8],
    font: "Legion-Symbol-Regular",
    color: "#111111",
    colorset: "swl_atkblack",
    display: "labels",
    system: "legion"
  },
  swlaw: {
    name: "Star Wars Legion: White Attack Dice",
    type: "d8",
    labels: ["h", "", "", "", "", "c", "o", ""],
    values: [1, 8],
    font: "Legion-Symbol-Regular",
    color: "#FFFFFF",
    colorset: "swl_atkwhite",
    display: "labels",
    system: "legion"
  },
  swldr: {
    name: "Star Wars Legion: Red Defense Dice",
    type: "d6",
    labels: ["s", "s", "s", "d", "", ""],
    values: [1, 6],
    scale: 0.9,
    font: "Legion-Symbol-Regular",
    color: "#FF0000",
    colorset: "swl_defred",
    display: "labels",
    system: "legion"
  },
  swldw: {
    name: "Star Wars Legion: White Defense Dice",
    type: "d6",
    labels: ["s", "", "", "d", "", ""],
    values: [1, 6],
    scale: 0.9,
    font: "Legion-Symbol-Regular",
    color: "#FFFFFF",
    colorset: "swl_defwhite",
    display: "labels",
    system: "legion"
  }
}, wt = {
  d4: {
    vertices: [[1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]],
    faces: [[1, 0, 2, 1], [0, 1, 3, 2], [0, 3, 2, 3], [1, 2, 3, 4]]
  },
  d6: {
    vertices: [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]],
    faces: [[0, 3, 2, 1, 1], [1, 2, 6, 5, 2], [0, 1, 5, 4, 3], [3, 7, 6, 2, 4], [0, 4, 7, 3, 5], [4, 5, 6, 7, 6]]
  },
  d8: {
    vertices: [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]],
    faces: [[0, 2, 4, 1], [0, 4, 3, 2], [0, 3, 5, 3], [0, 5, 2, 4], [1, 3, 4, 5], [1, 4, 2, 6], [1, 2, 5, 7], [1, 5, 3, 8]]
  },
  d10: {
    vertices: [[1, 0, -0.105], [0.809, 0.5877, 0.105], [0.309, 0.951, -0.105], [-0.309, 0.951, 0.105], [-0.809, 0.5877, -0.105], [-1, 0, 0.105], [-0.809, -0.587, -0.105], [-0.309, -0.951, 0.105], [0.309, -0.951, -0.105], [0.809, -0.5877, 0.105], [0, 0, -1], [0, 0, 1]],
    faces: [[5, 6, 7, 11, 0], [4, 3, 2, 10, 1], [1, 2, 3, 11, 2], [0, 9, 8, 10, 3], [7, 8, 9, 11, 4], [8, 7, 6, 10, 5], [9, 0, 1, 11, 6], [2, 1, 0, 10, 7], [3, 4, 5, 11, 8], [6, 5, 4, 10, 9]]
  },
  d12: {
    vertices: [[0, 0.618, 1.618], [0, 0.618, -1.618], [0, -0.618, 1.618], [0, -0.618, -1.618], [1.618, 0, 0.618], [1.618, 0, -0.618], [-1.618, 0, 0.618], [-1.618, 0, -0.618], [0.618, 1.618, 0], [0.618, -1.618, 0], [-0.618, 1.618, 0], [-0.618, -1.618, 0], [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1], [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1]],
    faces: [[2, 14, 4, 12, 0, 1], [15, 9, 11, 19, 3, 2], [16, 10, 17, 7, 6, 3], [6, 7, 19, 11, 18, 4], [6, 18, 2, 0, 16, 5], [18, 11, 9, 14, 2, 6], [1, 17, 10, 8, 13, 7], [1, 13, 5, 15, 3, 8], [13, 8, 12, 4, 5, 9], [5, 4, 14, 9, 15, 10], [0, 12, 8, 10, 16, 11], [3, 19, 7, 17, 1, 12]]
  },
  d20: {
    vertices: [[-1, 1.618, 0], [1, 1.618, 0], [-1, -1.618, 0], [1, -1.618, 0], [0, -1, 1.618], [0, 1, 1.618], [0, -1, -1.618], [0, 1, -1.618], [1.618, 0, -1], [1.618, 0, 1], [-1.618, 0, -1], [-1.618, 0, 1]],
    faces: [[0, 11, 5, 1], [0, 5, 1, 2], [0, 1, 7, 3], [0, 7, 10, 4], [0, 10, 11, 5], [1, 5, 9, 6], [5, 11, 4, 7], [11, 10, 2, 8], [10, 7, 6, 9], [7, 1, 8, 10], [3, 9, 4, 11], [3, 4, 2, 12], [3, 2, 6, 13], [3, 6, 8, 14], [3, 8, 9, 15], [4, 9, 5, 16], [2, 4, 11, 17], [6, 2, 10, 18], [8, 6, 7, 19], [9, 8, 1, 20]]
  }
}, xp = {
  name: "",
  scale: 1,
  font: "Arial",
  color: "",
  labels: [],
  valueMap: [],
  values: [],
  normals: [],
  mass: 300,
  inertia: 13,
  geometry: null,
  display: "values",
  system: "d20"
};
class yp {
  constructor(e) {
    if (!Ps.hasOwnProperty(e))
      return console.error("dice type unavailable");
    Object.assign(this, xp, Ps[e]), this.shape = Ps[e].type || e, this.type = e, this.setLabels(this.labels), this.setValues(this.values[0], this.values[1], this.values[2]), this.setValueMap(this.valueMap), this.bumpMaps && this.setBumpMaps(this.bumpMaps);
  }
  setValues(e = 1, t = 20, n = 1) {
    this.values = this.range(e, t, n);
  }
  setValueMap(e) {
    for (let t = 0; t < this.values.length; t++) {
      let n = this.values[t];
      e[n] != null && (this.valueMap[n] = e[n]);
    }
  }
  registerFaces(e, t = "labels") {
    let n;
    if (t == "labels" ? n = this.labels : n = this.normals, n.unshift(""), ["d2", "d10"].includes(this.shape) || n.unshift(""), this.shape == "d4") {
      let i = e[0], s = e[1], o = e[2], r = e[3];
      this.labels = [
        [[], [0, 0, 0], [s, r, o], [i, o, r], [s, i, r], [i, s, o]],
        [[], [0, 0, 0], [s, o, r], [o, i, r], [s, r, i], [o, s, i]],
        [[], [0, 0, 0], [r, o, s], [o, r, i], [r, s, i], [o, i, s]],
        [[], [0, 0, 0], [r, s, o], [i, r, o], [r, i, s], [i, o, s]]
      ];
    } else
      Array.prototype.push.apply(n, e);
  }
  setLabels(e) {
    this.loadTextures(e, this.registerFaces.bind(this), "labels");
  }
  setBumpMaps(e) {
    this.loadTextures(e, this.registerFaces.bind(this), "bump");
  }
  loadTextures(e, t, n) {
    let i = 0, s = e.length, o = /\.(PNG|JPG|GIF|WEBP)$/i, r = Array(e.length), l = !1;
    for (let a = 0; a < s; a++) {
      if (e[a] == "" || !e[a].match(o)) {
        r[a] = e[a], ++i;
        continue;
      }
      l = !0, r[a] = new Image(), r[a].onload = function() {
        ++i >= s && t(r, n);
      }, r[a].src = e[a];
    }
    l || t(r, n);
  }
  range(e, t, n = 1) {
    for (var i = [e], s = e; s < t; )
      i.push(s += n || 1);
    return i;
  }
}
const bp = {
  none: {
    name: "Plastic"
  },
  perfectmetal: {
    name: "Perfect Metal",
    color: 14540253,
    roughness: 0,
    metalness: 1,
    envMapIntensity: 1
  },
  metal: {
    name: "Metal",
    color: 14540253,
    roughness: 0.5,
    metalness: 0.6,
    envMapIntensity: 1
  },
  wood: {
    name: "Wood",
    color: 14540253,
    roughness: 0.9,
    metalness: 0,
    envMapIntensity: 1
  },
  glass: {
    name: "Glass",
    color: 14540253,
    roughness: 0.1,
    metalness: 0,
    envMapIntensity: 1
  }
}, wp = {
  baseScale: 100,
  bumpMapping: !0
}, Yn = class {
  constructor(e) {
    this.geometries = {}, this.materials_cache = {}, this.cache_hits = 0, this.cache_misses = 0, this.label_color = "", this.dice_color = "", this.edge_color = "", this.label_outline = "", this.dice_texture = "", this.dice_material = "", this.material_options = {
      specular: 16777215,
      color: 11908533,
      shininess: 5,
      flatShading: !0
    }, Object.assign(this, wp, e);
  }
  updateConfig(e = {}) {
    Object.assign(this, e), e.scale && this.scaleGeometry();
  }
  setBumpMapping(e) {
    this.bumpMapping = e, this.materials_cache = {};
  }
  create(e) {
    let t = this.get(e);
    if (!t)
      return null;
    let n = this.geometries[e];
    if (n || (n = this.createGeometry(t.shape, t.scale * this.baseScale), this.geometries[e] = n), !n)
      return null;
    this.setMaterialInfo();
    let i = new Nt(n, this.createMaterials(t, this.baseScale / 2, 1));
    switch (i.result = [], i.shape = t.shape, i.rerolls = 0, i.resultReason = "natural", i.mass = t.mass, i.getFaceValue = function() {
      let s = this.resultReason, o = new O(0, 0, this.shape == "d4" ? -1 : 1), r, l = Math.PI * 2, a = this.geometry.getAttribute("normal").array;
      for (let p = 0, f = this.geometry.groups.length; p < f; ++p) {
        let v = this.geometry.groups[p];
        if (v.materialIndex == 0)
          continue;
        let _ = p * 9, x = new O(a[_], a[_ + 1], a[_ + 2]).clone().applyQuaternion(this.body.quaternion).angleTo(o);
        x < l && (l = x, r = v);
      }
      let c = r.materialIndex - 1, d = 2;
      const u = Yn.dice[this.notation.type];
      if (this.shape == "d4") {
        let p = c - 1 == 0 ? 5 : c;
        return { value: c, label: u.labels[c - 1][p][0], reason: s };
      }
      ["d10", "d2"].includes(this.shape) && (c += 1, d -= 1);
      let m = u.values[(c - 1) % u.values.length], g = u.labels[(c - 1) % (u.labels.length - 2) + d];
      return { value: m, label: g, reason: s };
    }, i.storeRolledValue = function(s) {
      this.resultReason = s || this.resultReason, this.result.push(this.getFaceValue());
    }, i.getLastValue = function() {
      return !this.result || this.result.length < 1 ? { value: void 0, label: "", reason: "" } : this.result[this.result.length - 1];
    }, i.ignoreLastValue = function(s) {
      let o = this.getLastValue();
      o.value !== void 0 && (o.ignore = s, this.setLastValue(o));
    }, i.setLastValue = function(s) {
      if (!(!this.result || this.result.length < 1) && !(!s || s.length < 1))
        return this.result[this.result.length - 1] = s;
    }, t.color && (i.material[0].color = new Ae(t.color), i.material[0].emissive = new Ae(t.color), i.material[0].emissiveIntensity = 1, i.material[0].needsUpdate = !0), t.values.length) {
      case 1:
        return this.fixmaterials(i, 1);
      case 2:
        return this.fixmaterials(i, 2);
      case 3:
        return this.fixmaterials(i, 3);
      default:
        return i;
    }
  }
  get(e) {
    let t;
    return Yn.dice.hasOwnProperty(e) ? t = Yn.dice[e] : (t = new yp(e), Yn.dice[e] = t), t;
  }
  getGeometry(e) {
    return this.geometries[e];
  }
  scaleGeometry() {
  }
  createMaterials(e, t, n, i = !0, s = 0) {
    let o = [], r = e.labels;
    e.shape == "d4" && (r = e.labels[s], t = this.baseScale / 2, n = this.baseScale * 2);
    for (var l = 0; l < r.length; ++l) {
      var a;
      this.dice_material != "none" ? (a = new Uu(bp[this.dice_material]), a.envMapIntensity = 0) : a = new Gu(this.material_options);
      let c;
      if (l == 0) {
        let d = { name: "none" };
        this.dice_texture_rand.composite != "source-over" && (d = this.dice_texture_rand), c = this.createTextMaterial(e, r, l, t, n, d, this.label_color_rand, this.label_outline_rand, this.edge_color_rand, i), a.map = c.composite;
      } else if (c = this.createTextMaterial(e, r, l, t, n, this.dice_texture_rand, this.label_color_rand, this.label_outline_rand, this.dice_color_rand, i), a.map = c.composite, this.bumpMapping) {
        {
          let d = 0.75;
          t > 35 && (d = 1), t > 40 && (d = 2.5), t > 45 && (d = 4), a.bumpScale = d;
        }
        c.bump && (a.bumpMap = c.bump), e.shape != "d4" && e.normals[l] && (a.bumpMap = new _t(e.normals[l]), a.bumpScale = 4, a.bumpMap.needsUpdate = !0);
      }
      a.opacity = 1, a.transparent = !0, a.depthTest = !1, a.needUpdate = !0, o.push(a);
    }
    return o;
  }
  createTextMaterial(e, t, n, i, s, o, r, l, a, c) {
    if (t[n] === void 0)
      return null;
    o = o || this.dice_texture_rand, r = r || this.label_color_rand, l = l || this.label_outline_rand, a = a || this.dice_color_rand, c = c == null ? !0 : c;
    let d = t[n], u = !1, m = d;
    d instanceof HTMLImageElement ? m = d.src : d instanceof Array && d.forEach((y) => {
      m += y.src;
    });
    let g = e.type + m + n + o.name + r + l + a;
    if (e.shape == "d4" && (g = e.type + m + o.name + r + l + a), c && this.materials_cache[g] != null)
      return this.cache_hits++, this.materials_cache[g];
    let p = document.createElement("canvas"), f = p.getContext("2d", { alpha: !0 });
    f.globalAlpha = 0, f.clearRect(0, 0, p.width, p.height);
    let v = document.createElement("canvas"), _ = v.getContext("2d", { alpha: !0 });
    _.globalAlpha = 0, _.clearRect(0, 0, v.width, v.height);
    let w;
    if (e.shape == "d4" ? w = this.calc_texture_size(i + s) * 4 : w = this.calc_texture_size(i + i * 2 * s) * 4, p.width = p.height = w, v.width = v.height = w, f.fillStyle = a, f.fillRect(0, 0, p.width, p.height), _.fillStyle = "#FFFFFF", _.fillRect(0, 0, v.width, v.height), o.texture && o.name != "" && o.name != "none" ? (f.globalCompositeOperation = o.composite || "source-over", f.drawImage(o.texture, 0, 0, p.width, p.height), f.globalCompositeOperation = "source-over", o.bump && (_.globalCompositeOperation = "source-over", _.drawImage(o.bump, 0, 0, p.width, p.height))) : f.globalCompositeOperation = "source-over", f.globalCompositeOperation = "source-over", f.textAlign = "center", f.textBaseline = "middle", _.textAlign = "center", _.textBaseline = "middle", e.shape != "d4") {
      let A = {
        d8: { even: -7.5, odd: -127.5 },
        d10: { all: -6 },
        d12: { all: 5 },
        d20: { all: -7.5 }
      }[e.shape];
      if (A) {
        let F;
        if (A.hasOwnProperty("all") ? F = A.all : n > 0 && n % 2 != 0 ? F = A.odd : F = A.even, F && F != 0) {
          var x = p.width / 2, M = p.height / 2;
          f.translate(x, M), f.rotate(F * (Math.PI / 180)), f.translate(-x, -M), _.translate(x, M), _.rotate(F * (Math.PI / 180)), _.translate(-x, -M);
        }
      }
      if (d instanceof HTMLImageElement)
        u = !0, f.drawImage(d, 0, 0, d.width, d.height, 0, 0, p.width, p.height);
      else {
        let F = w / (1 + 2 * s), P = p.height / 2 + 10, G = p.width / 2;
        e.shape == "d10" ? (F = F * 0.75, P = P * 1.15 - 10) : e.shape == "d20" && (G = G * 0.98), f.font = F + "pt " + e.font, _.font = F + "pt " + e.font;
        let z = f.measureText("M").width * 1.4, L = d.split(`
`);
        L.length > 1 && (F = F / L.length, f.font = F + "pt " + e.font, _.font = F + "pt " + e.font, z = f.measureText("M").width * 1.2, P -= z * L.length / 2);
        for (let I = 0, D = L.length; I < D; I++) {
          let q = L[I].trim();
          l != "none" && l != a && (f.strokeStyle = l, f.lineWidth = 5, f.strokeText(L[I], G, P), _.strokeStyle = "#000000", _.lineWidth = 5, _.strokeText(L[I], G, P), (q == "6" || q == "9") && (f.strokeText("  .", G, P), _.strokeText("  .", G, P))), f.fillStyle = r, f.fillText(L[I], G, P), _.fillStyle = "#000000", _.fillText(L[I], G, P), (q == "6" || q == "9") && (f.fillText("  .", G, P), _.fillText("  .", G, P)), P += z * 1.5;
        }
      }
    } else {
      var x = p.width / 2, M = p.height / 2;
      f.font = w / 128 * 24 + "pt " + e.font, _.font = w / 128 * 24 + "pt " + e.font;
      for (let F = 0; F < d.length; F++) {
        if (d[F] instanceof HTMLImageElement) {
          let P = d[F].width / p.width;
          f.drawImage(d[F], 0, 0, d[F].width, d[F].height, 100 / P, 25 / P, 60 / P, 60 / P);
        } else
          l != "none" && l != a && (f.strokeStyle = l, f.lineWidth = 5, f.strokeText(d[F], x, M - w * 0.3), _.strokeStyle = "#000000", _.lineWidth = 5, _.strokeText(d[F], x, M - w * 0.3)), f.fillStyle = r, f.fillText(d[F], x, M - w * 0.3), _.fillStyle = "#000000", _.fillText(d[F], x, M - w * 0.3);
        f.translate(x, M), f.rotate(Math.PI * 2 / 3), f.translate(-x, -M), _.translate(x, M), _.rotate(Math.PI * 2 / 3), _.translate(-x, -M);
      }
    }
    var E = new Rr(p), R;
    return u ? R = null : R = new Rr(v), c && (this.cache_misses++, this.materials_cache[g] = { composite: E, bump: R }), { composite: E, bump: R };
  }
  applyColorSet(e) {
    var t;
    this.colordata = e, this.label_color = e.foreground, this.dice_color = e.background, this.label_outline = e.outline, this.dice_texture = e.texture, this.dice_material = ((t = e == null ? void 0 : e.texture) == null ? void 0 : t.material) || "none", this.edge_color = e.hasOwnProperty("edge") ? e.edge : e.background;
  }
  setMaterialInfo(e = "") {
    let t = this.colordata, n = this.dice_texture, i = this.dice_material;
    if (this.dice_color_rand = "", this.label_color_rand = "", this.label_outline_rand = "", this.dice_texture_rand = "", this.dice_material_rand = "", this.edge_color_rand = "", Array.isArray(this.dice_color)) {
      var s = Math.floor(Math.random() * this.dice_color.length);
      Array.isArray(this.label_color) && this.label_color.length == this.dice_color.length && (this.label_color_rand = this.label_color[s], Array.isArray(this.label_outline) && this.label_outline.length == this.label_color.length && (this.label_outline_rand = this.label_outline[s])), Array.isArray(this.dice_texture) && this.dice_texture.length == this.dice_color.length && (this.dice_texture_rand = this.dice_texture[s], this.dice_material_rand = this.dice_texture_rand.material), Array.isArray(this.edge_color) && this.edge_color.length == this.dice_color.length && (this.edge_color_rand = this.edge_color[s]), this.dice_color_rand = this.dice_color[s];
    } else
      this.dice_color_rand = this.dice_color;
    if (this.edge_color_rand == "")
      if (Array.isArray(this.edge_color)) {
        var s = Math.floor(Math.random() * this.edge_color.length);
        this.edge_color_rand = this.edge_color[s];
      } else
        this.edge_color_rand = this.edge_color;
    if (this.label_color_rand == "" && Array.isArray(this.label_color)) {
      var s = this.label_color[Math.floor(Math.random() * this.label_color.length)];
      Array.isArray(this.label_outline) && this.label_outline.length == this.label_color.length && (this.label_outline_rand = this.label_outline[s]), this.label_color_rand = this.label_color[s];
    } else
      this.label_color_rand == "" && (this.label_color_rand = this.label_color);
    if (this.label_outline_rand == "" && Array.isArray(this.label_outline)) {
      var s = this.label_outline[Math.floor(Math.random() * this.label_outline.length)];
      this.label_outline_rand = this.label_outline[s];
    } else
      this.label_outline_rand == "" && (this.label_outline_rand = this.label_outline);
    this.dice_texture_rand == "" && Array.isArray(this.dice_texture) ? (this.dice_texture_rand = this.dice_texture[Math.floor(Math.random() * this.dice_texture.length)], this.dice_material_rand = this.dice_texture_rand.material || this.dice_material) : this.dice_texture_rand == "" && (this.dice_texture_rand = this.dice_texture, this.dice_material_rand = this.dice_texture_rand.material || this.dice_material), this.dice_material_rand == "" && Array.isArray(this.dice_material) ? this.dice_material_rand = this.dice_material[Math.floor(Math.random() * this.dice_material.length)] : this.dice_material_rand == "" && (this.dice_material_rand = this.dice_material), this.colordata && this.colordata.id != t.id && this.applyColorSet(t, n, i);
  }
  calc_texture_size(e) {
    return Math.pow(2, Math.floor(Math.log(e) / Math.log(2)));
  }
  createGeometry(e, t, n = !1) {
    const i = n ? "create_shape" : "create_geom";
    switch (e) {
      case "d2":
        var s = new ks(1 * t, 1 * t, 0.1 * t, 32);
        return s.cannon_shape = new jd(1 * t, 1 * t, 0.1 * t, 8), s;
      case "d4":
        return this[i](wt.d4.vertices, wt.d4.faces, t, -0.1, Math.PI * 7 / 6, 0.96);
      case "d6":
        return this[i](wt.d6.vertices, wt.d6.faces, t, 0.1, Math.PI / 4, 0.96);
      case "d8":
        return this[i](wt.d8.vertices, wt.d8.faces, t, 0, -Math.PI / 4 / 2, 0.965);
      case "d10":
        return this[i](wt.d10.vertices, wt.d10.faces, t, 0.3, Math.PI, 0.945);
      case "d12":
        return this[i](wt.d12.vertices, wt.d12.faces, t, 0.2, -Math.PI / 4 / 2, 0.968);
      case "d20":
        return this[i](wt.d20.vertices, wt.d20.faces, t, -0.2, -Math.PI / 4 / 2, 0.955);
      default:
        return console.error(`Geometry for ${e} is not available`), null;
    }
  }
  fixmaterials(e, t) {
    for (let i = 0, s = e.geometry.groups.length; i < s; ++i) {
      var n = e.geometry.groups[i].materialIndex - 2;
      if (n < t)
        continue;
      let o = n % t;
      e.geometry.groups[i].materialIndex = o + 2;
    }
    return e.geometry.elementsNeedUpdate = !0, e;
  }
  create_shape(e, t, n) {
    for (var i = new Array(e.length), s = 0; s < e.length; ++s)
      i[s] = new O().fromArray(e[s]).normalize();
    for (var o = new Array(e.length), r = new Array(t.length), s = 0; s < i.length; ++s) {
      var l = i[s];
      o[s] = new b(l.x * n, l.y * n, l.z * n);
    }
    for (var s = 0; s < t.length; ++s)
      r[s] = t[s].slice(0, t[s].length - 1);
    return new wn({ vertices: o, faces: r });
  }
  make_geom(e, t, n, i, s) {
    let o = new Ut();
    for (let g = 0; g < e.length; ++g)
      e[g] = e[g].multiplyScalar(n);
    let r = [];
    const l = [], a = [], c = new O(), d = new O();
    let u, m = 0;
    for (let g = 0; g < t.length; ++g) {
      let p = t[g], f = p.length - 1, v = Math.PI * 2 / f;
      u = p[f] + 1;
      for (let w = 0; w < f - 2; ++w)
        r.push(...e[p[0]].toArray()), r.push(...e[p[w + 1]].toArray()), r.push(...e[p[w + 2]].toArray()), c.subVectors(e[p[w + 2]], e[p[w + 1]]), d.subVectors(e[p[0]], e[p[w + 1]]), c.cross(d), c.normalize(), l.push(...c.toArray()), l.push(...c.toArray()), l.push(...c.toArray()), a.push((Math.cos(s) + 1 + i) / 2 / (1 + i), (Math.sin(s) + 1 + i) / 2 / (1 + i)), a.push((Math.cos(v * (w + 1) + s) + 1 + i) / 2 / (1 + i), (Math.sin(v * (w + 1) + s) + 1 + i) / 2 / (1 + i)), a.push((Math.cos(v * (w + 2) + s) + 1 + i) / 2 / (1 + i), (Math.sin(v * (w + 2) + s) + 1 + i) / 2 / (1 + i));
      let _ = (f - 2) * 3;
      for (let w = 0; w < _ / 3; w++)
        o.addGroup(m, 3, u), m += 3;
    }
    return o.setAttribute("position", new st(r, 3)), o.setAttribute("normal", new st(l, 3)), o.setAttribute("uv", new st(a, 2)), o.boundingSphere = new ci(new O(), n), o;
  }
  make_d10_geom(e, t, n, i, s) {
    let o = new Ut();
    for (let w = 0; w < e.length; ++w)
      e[w] = e[w].multiplyScalar(n);
    let r = [];
    const l = [], a = [], c = new O(), d = new O();
    let u, m = 0;
    for (let w = 0; w < t.length; ++w) {
      let x = t[w], M = x.length - 1, E = Math.PI * 2 / M;
      u = x[M] + 1;
      var g = 0.65, p = 0.85, f = 1 - 1 * p, v = 1 - 0.895 / 1.105 * p, _ = 1;
      for (let y = 0; y < M - 2; ++y)
        r.push(...e[x[0]].toArray()), r.push(...e[x[y + 1]].toArray()), r.push(...e[x[y + 2]].toArray()), c.subVectors(e[x[y + 2]], e[x[y + 1]]), d.subVectors(e[x[0]], e[x[y + 1]]), c.cross(d), c.normalize(), l.push(...c.toArray()), l.push(...c.toArray()), l.push(...c.toArray()), t[w][t[w].length - 1] == -1 || y >= 2 ? (a.push((Math.cos(s) + 1 + i) / 2 / (1 + i), (Math.sin(s) + 1 + i) / 2 / (1 + i)), a.push((Math.cos(E * (y + 1) + s) + 1 + i) / 2 / (1 + i), (Math.sin(E * (y + 1) + s) + 1 + i) / 2 / (1 + i)), a.push((Math.cos(E * (y + 2) + s) + 1 + i) / 2 / (1 + i), (Math.sin(E * (y + 2) + s) + 1 + i) / 2 / (1 + i))) : y == 0 ? (a.push(0.5 - g / 2, v), a.push(0.5, f), a.push(0.5 + g / 2, v)) : y == 1 && (a.push(0.5 - g / 2, v), a.push(0.5 + g / 2, v), a.push(0.5, _));
      let R = (M - 2) * 3;
      for (let y = 0; y < R / 3; y++)
        o.addGroup(m, 3, u), m += 3;
    }
    return o.setAttribute("position", new st(r, 3)), o.setAttribute("normal", new st(l, 3)), o.setAttribute("uv", new st(a, 2)), o.boundingSphere = new ci(new O(), n), o;
  }
  chamfer_geom(e, t, n) {
    for (var i = [], s = [], o = new Array(e.length), r = 0; r < e.length; ++r)
      o[r] = [];
    for (var r = 0; r < t.length; ++r) {
      for (var l = t[r], a = l.length - 1, c = new O(), d = new Array(a), u = 0; u < a; ++u) {
        var m = e[l[u]].clone();
        c.add(m), o[l[u]].push(d[u] = i.push(m) - 1);
      }
      c.divideScalar(a);
      for (var u = 0; u < a; ++u) {
        var m = i[d[u]];
        m.subVectors(m, c).multiplyScalar(n).addVectors(m, c);
      }
      d.push(l[a]), s.push(d);
    }
    for (var r = 0; r < t.length - 1; ++r)
      for (var u = r + 1; u < t.length; ++u) {
        for (var g = [], p = -1, f = 0; f < t[r].length - 1; ++f) {
          var v = t[u].indexOf(t[r][f]);
          v >= 0 && v < t[u].length - 1 && (p >= 0 && f != p + 1 ? g.unshift([r, f], [u, v]) : g.push([r, f], [u, v]), p = f);
        }
        g.length == 4 && s.push([
          s[g[0][0]][g[0][1]],
          s[g[1][0]][g[1][1]],
          s[g[3][0]][g[3][1]],
          s[g[2][0]][g[2][1]],
          -1
        ]);
      }
    for (var r = 0; r < o.length; ++r) {
      for (var _ = o[r], d = [_[0]], w = _.length - 1; w; ) {
        for (var f = t.length; f < s.length; ++f) {
          var x = s[f].indexOf(d[d.length - 1]);
          if (x >= 0 && x < 4) {
            --x == -1 && (x = 3);
            var M = s[f][x];
            if (_.indexOf(M) >= 0) {
              d.push(M);
              break;
            }
          }
        }
        --w;
      }
      d.push(-1), s.push(d);
    }
    return { vectors: i, faces: s };
  }
  create_geom(e, t, n, i, s, o) {
    for (var r = new Array(e.length), l = 0; l < e.length; ++l)
      r[l] = new O().fromArray(e[l]).normalize();
    var a = this.chamfer_geom(r, t, o);
    if (t.length != 10)
      var c = this.make_geom(a.vectors, a.faces, n, i, s);
    else
      var c = this.make_d10_geom(a.vectors, a.faces, n, i, s);
    return c.cannon_shape = this.create_shape(e, t, n), c.name = "d" + t.length, c;
  }
};
let Hi = Yn;
Ys(Hi, "dice", {});
const Is = {
  cloudy: {
    name: "Clouds (Transparent)",
    composite: "destination-in",
    source: "textures/cloudy.webp",
    source_bump: "textures/cloudy.alt.webp"
  },
  cloudy_2: {
    name: "Clouds",
    composite: "multiply",
    source: "textures/cloudy.alt.webp",
    source_bump: "textures/cloudy.alt.webp"
  },
  fire: {
    name: "Fire",
    composite: "multiply",
    source: "textures/fire.webp",
    source_bump: "textures/fire.webp",
    material: "metal"
  },
  marble: {
    name: "Marble",
    composite: "multiply",
    source: "textures/marble.webp",
    source_bump: "",
    material: "glass"
  },
  water: {
    name: "Water",
    composite: "destination-in",
    source: "textures/water.webp",
    source_bump: "textures/water.webp",
    material: "glass"
  },
  ice: {
    name: "Ice",
    composite: "destination-in",
    source: "textures/ice.webp",
    source_bump: "textures/ice.webp",
    material: "glass"
  },
  paper: {
    name: "Paper",
    composite: "multiply",
    source: "textures/paper.webp",
    source_bump: "textures/paper-bump.webp",
    material: "wood"
  },
  speckles: {
    name: "Speckles",
    composite: "multiply",
    source: "textures/speckles.webp",
    source_bump: "textures/speckles.webp",
    material: "none"
  },
  glitter: {
    name: "Glitter",
    composite: "multiply",
    source: "textures/glitter.webp",
    source_bump: "textures/glitter-bump.webp",
    material: "none"
  },
  glitter_2: {
    name: "Glitter (Transparent)",
    composite: "destination-in",
    source: "textures/glitter-alpha.webp",
    source_bump: "",
    material: "none"
  },
  stars: {
    name: "Stars",
    composite: "multiply",
    source: "textures/stars.webp",
    source_bump: "textures/stars.webp",
    material: "none"
  },
  stainedglass: {
    name: "Stained Glass",
    composite: "multiply",
    source: "textures/stainedglass.webp",
    source_bump: "textures/stainedglass-bump.webp",
    material: "glass"
  },
  wood: {
    name: "Wood",
    composite: "multiply",
    source: "textures/wood.webp",
    source_bump: "textures/wood.webp",
    material: "wood"
  },
  metal: {
    name: "Stainless Steel",
    composite: "multiply",
    source: "textures/metal.webp",
    source_bump: "textures/metal-bump.webp",
    material: "metal"
  },
  skulls: {
    name: "Skulls",
    composite: "multiply",
    source: "textures/skulls.webp",
    source_bump: "textures/skulls.webp"
  },
  leopard: {
    name: "Leopard",
    composite: "multiply",
    source: "textures/leopard.webp",
    source_bump: "textures/leopard.webp",
    material: "wood"
  },
  tiger: {
    name: "Tiger",
    composite: "multiply",
    source: "textures/tiger.webp",
    source_bump: "textures/tiger.webp",
    material: "wood"
  },
  cheetah: {
    name: "Cheetah",
    composite: "multiply",
    source: "textures/cheetah.webp",
    source_bump: "textures/cheetah.webp",
    material: "wood"
  },
  dragon: {
    name: "Dragon",
    composite: "multiply",
    source: "textures/dragon.webp",
    source_bump: "textures/dragon-bump.webp",
    material: "none"
  },
  lizard: {
    name: "Lizard",
    composite: "multiply",
    source: "textures/lizard.webp",
    source_bump: "textures/lizard.webp",
    material: "none"
  },
  bird: {
    name: "Bird",
    composite: "multiply",
    source: "textures/feather.webp",
    source_bump: "textures/feather-bump.webp",
    material: "wood"
  },
  astral: {
    name: "Astral Sea",
    composite: "multiply",
    source: "textures/astral.webp",
    source_bump: "textures/stars.webp",
    material: "none"
  },
  acleaf: {
    name: "AC Leaf",
    composite: "multiply",
    source: "textures/acleaf.webp",
    source_bump: "textures/acleaf.webp",
    material: "none"
  },
  thecage: {
    name: "Nicholas Cage",
    composite: "multiply",
    source: "textures/thecage.webp",
    source_bump: "",
    material: "metal"
  },
  isabelle: {
    name: "Isabelle",
    composite: "source-over",
    source: "textures/isabelle.webp",
    source_bump: "",
    material: "none"
  },
  bronze01: {
    name: "bronze01",
    composite: "difference",
    source: "textures/bronze01.webp",
    source_bump: "",
    material: "metal"
  },
  bronze02: {
    name: "bronze02",
    composite: "difference",
    source: "textures/bronze02.webp",
    source_bump: "",
    material: "metal"
  },
  bronze03: {
    name: "bronze03",
    composite: "difference",
    source: "textures/bronze03.webp",
    source_bump: "",
    material: "metal"
  },
  bronze03a: {
    name: "bronze03a",
    composite: "difference",
    source: "textures/bronze03a.webp",
    source_bump: "",
    material: "metal"
  },
  bronze03b: {
    name: "bronze03b",
    composite: "difference",
    source: "textures/bronze03b.webp",
    source_bump: "",
    material: "metal"
  },
  bronze04: {
    name: "bronze04",
    composite: "difference",
    source: "textures/bronze04.webp",
    source_bump: "",
    material: "metal"
  },
  none: {
    name: "none",
    composite: "source-over",
    source: "",
    source_bump: "",
    material: ""
  },
  "": {
    name: "~ Preset ~",
    composite: "source-over",
    source: "",
    source_bump: "",
    material: ""
  }
}, eo = {
  coin_default: {
    name: "Gold Coin",
    description: "Gold Dragonhead Coin",
    category: "Other",
    foreground: "#f6c928",
    background: "#f6c928",
    outline: "none",
    texture: "metal"
  },
  coin_silver: {
    name: "Silver Coin",
    description: "Gold Dragonhead Coin",
    category: "Other",
    foreground: "#f6c928",
    background: "#f6c928",
    outline: "none",
    texture: "metal"
  },
  radiant: {
    name: "Radiant",
    category: "Damage Types",
    foreground: "#F9B333",
    background: "#FFFFFF",
    outline: "",
    texture: "paper",
    description: "Radiant"
  },
  fire: {
    name: "Fire",
    category: "Damage Types",
    foreground: "#f8d84f",
    background: ["#f8d84f", "#f9b02d", "#f43c04", "#910200", "#4c1009"],
    outline: "black",
    texture: "fire",
    description: "Fire"
  },
  ice: {
    name: "Ice",
    category: "Damage Types",
    foreground: "#60E9FF",
    background: ["#214fa3", "#3c6ac1", "#253f70", "#0b56e2", "#09317a"],
    outline: "black",
    texture: "ice",
    description: "Ice"
  },
  poison: {
    name: "Poison",
    category: "Damage Types",
    foreground: "#D6A8FF",
    background: ["#313866", "#504099", "#66409e", "#934fc3", "#c949fc"],
    outline: "black",
    texture: "cloudy",
    description: "Poison"
  },
  acid: {
    name: "Acid",
    category: "Damage Types",
    foreground: "#A9FF70",
    background: ["#a6ff00", "#83b625", "#5ace04", "#69f006", "#b0f006", "#93bc25"],
    outline: "black",
    texture: "marble",
    description: "Acid"
  },
  thunder: {
    name: "Thunder",
    category: "Damage Types",
    foreground: "#FFC500",
    background: "#7D7D7D",
    outline: "black",
    texture: "cloudy",
    description: "Thunder"
  },
  lightning: {
    name: "Lightning",
    category: "Damage Types",
    foreground: "#FFC500",
    background: ["#f17105", "#f3ca40", "#eddea4", "#df9a57", "#dea54b"],
    outline: "#7D7D7D",
    texture: "ice",
    description: "Lightning"
  },
  air: {
    name: "Air",
    category: "Damage Types",
    foreground: "#ffffff",
    background: ["#d0e5ea", "#c3dee5", "#a4ccd6", "#8dafb7", "#80a4ad"],
    outline: "black",
    texture: "cloudy",
    description: "Air"
  },
  water: {
    name: "Water",
    category: "Damage Types",
    foreground: "#60E9FF",
    background: ["#87b8c4", "#77a6b2", "#6b98a3", "#5b8691", "#4b757f"],
    outline: "black",
    texture: "water",
    description: "Water"
  },
  earth: {
    name: "Earth",
    category: "Damage Types",
    foreground: "#6C9943",
    background: ["#346804", "#184200", "#527f22", "#3a1d04", "#56341a", "#331c17", "#5a352a", "#302210"],
    outline: "black",
    texture: "speckles",
    description: "Earth"
  },
  force: {
    name: "Force",
    category: "Damage Types",
    foreground: "white",
    background: ["#FF97FF", "#FF68FF", "#C651C6"],
    outline: "#570000",
    texture: "stars",
    description: "Force"
  },
  psychic: {
    name: "Psychic",
    category: "Damage Types",
    foreground: "#D6A8FF",
    background: ["#313866", "#504099", "#66409E", "#934FC3", "#C949FC", "#313866"],
    outline: "black",
    texture: "speckles",
    description: "Psychic"
  },
  necrotic: {
    name: "Necrotic",
    category: "Damage Types",
    foreground: "#ffffff",
    background: "#6F0000",
    outline: "black",
    texture: "skulls",
    description: "Necrotic"
  },
  breebaby: {
    name: "Pastel Sunset",
    category: "Custom Sets",
    foreground: ["#5E175E", "#564A5E", "#45455E", "#3D5A5E", "#1E595E", "#5E3F3D", "#5E1E29", "#283C5E", "#25295E"],
    background: ["#FE89CF", "#DFD4F2", "#C2C2E8", "#CCE7FA", "#A1D9FC", "#F3C3C2", "#EB8993", "#8EA1D2", "#7477AD"],
    outline: "white",
    texture: "marble",
    description: "Pastel Sunset, for Breyanna"
  },
  pinkdreams: {
    name: "Pink Dreams",
    category: "Custom Sets",
    foreground: "white",
    background: ["#ff007c", "#df73ff", "#f400a1", "#df00ff", "#ff33cc"],
    outline: "#570000",
    texture: "skulls",
    description: "Pink Dreams, for Ethan"
  },
  inspired: {
    name: "Inspired",
    category: "Custom Sets",
    foreground: "#FFD800",
    background: "#C4C4B6",
    outline: "#8E8E86",
    texture: "none",
    description: "Inspired, for Austin"
  },
  bloodmoon: {
    name: "Blood Moon",
    category: "Custom Sets",
    foreground: "#CDB800",
    background: "#6F0000",
    outline: "black",
    texture: "marble",
    description: "Blood Moon, for Jared"
  },
  starynight: {
    name: "Stary Night",
    category: "Custom Sets",
    foreground: "#4F708F",
    background: ["#091636", "#233660", "#4F708F", "#8597AD", "#E2E2E2"],
    outline: "white",
    texture: "speckles",
    description: "Stary Night, for Mai"
  },
  glitterparty: {
    name: "Glitter Party",
    category: "Custom Sets",
    foreground: "white",
    background: ["#FFB5F5", "#7FC9FF", "#A17FFF"],
    outline: "none",
    texture: "glitter",
    description: "Glitter Party, for Austin"
  },
  astralsea: {
    name: "Astral Sea",
    category: "Custom Sets",
    foreground: "#565656",
    background: "white",
    outline: "none",
    texture: "astral",
    description: "The Astral Sea, for Austin"
  },
  bronze: {
    name: "Thylean Bronze",
    description: "Thylean Bronze by @SpencerThayer",
    category: "Custom Sets",
    foreground: ["#FF9159", "#FFB066", "#FFBF59", "#FFD059"],
    background: ["#705206", "#7A4E06", "#643100", "#7A2D06"],
    outline: ["#3D2D03", "#472D04", "#301700", "#471A04"],
    edge: ["#FF5D0D", "#FF7B00", "#FFA20D", "#FFBA0D"],
    texture: ["bronze01", "bronze02", "bronze03", "bronze03a", "bronze03b", "bronze04"]
  },
  dragons: {
    name: "Here be Dragons",
    category: "Custom Sets",
    foreground: "#FFFFFF",
    background: ["#B80000", "#4D5A5A", "#5BB8FF", "#7E934E", "#FFFFFF", "#F6ED7C", "#7797A3", "#A78437", "#862C1A", "#FFDF8A"],
    outline: "black",
    texture: ["dragon", "lizard"],
    description: "Here be Dragons"
  },
  birdup: {
    name: "Bird Up",
    category: "Custom Sets",
    foreground: "#FFFFFF",
    background: ["#F11602", "#FFC000", "#6EC832", "#0094BC", "#05608D", "#FEABB3", "#F75680", "#F3F0DF", "#C7A57F"],
    outline: "black",
    texture: "bird",
    description: "Bird Up!"
  },
  tigerking: {
    name: "Tiger King",
    category: "Other",
    foreground: "#ffffff",
    background: "#FFCC40",
    outline: "black",
    texture: ["leopard", "tiger", "cheetah"],
    description: "Leopard Print"
  },
  covid: {
    name: "COViD",
    category: "Other",
    foreground: "#A9FF70",
    background: ["#a6ff00", "#83b625", "#5ace04", "#69f006", "#b0f006", "#93bc25"],
    outline: "black",
    texture: "fire",
    description: "Covid-19"
  },
  acleaf: {
    name: "Animal Crossing",
    category: "Other",
    foreground: "#00FF00",
    background: "#07540A",
    outline: "black",
    texture: "acleaf",
    description: "Animal Crossing Leaf"
  },
  isabelle: {
    name: "Isabelle",
    category: "Other",
    foreground: "white",
    background: "#FEE5CC",
    outline: "black",
    texture: "isabelle",
    description: "Isabelle"
  },
  thecage: {
    name: "Nicholas Cage",
    category: "Other",
    foreground: "#ffffff",
    background: "#ffffff",
    outline: "black",
    texture: "thecage",
    description: "Nicholas Cage"
  },
  test: {
    name: "Test",
    category: "Colors",
    foreground: ["#00FF00", "#0000FF", "#FF0000"],
    background: ["#FF0000", "#00FF00", "#0000FF"],
    outline: "black",
    texture: "none",
    description: "Test"
  },
  rainbow: {
    name: "Rainblow",
    category: "Colors",
    foreground: ["#FF5959", "#FFA74F", "#FFFF56", "#59FF59", "#2374FF", "#00FFFF", "#FF59FF"],
    background: ["#900000", "#CE3900", "#BCBC00", "#00B500", "#00008E", "#008282", "#A500A5"],
    outline: "black",
    texture: "none",
    description: "Rainblow"
  },
  black: {
    name: "Black",
    category: "Colors",
    foreground: "#ffffff",
    background: "#000000",
    outline: "black",
    texture: "none",
    description: "Black"
  },
  white: {
    name: "White",
    category: "Colors",
    foreground: "#000000",
    background: "#FFFFFF",
    outline: "#FFFFFF",
    texture: "none",
    description: "White"
  },
  swrpg_abi: {
    name: "Star Wars RPG - Ability",
    category: "Star Wars\u2122 RPG",
    foreground: "#00FF00",
    background: ["#3D9238", "#52B848", "#5EAC56", "#9ECB9A"],
    outline: "#000000",
    texture: "cloudy_2",
    description: "Star Wars\u2122 RPG Ability Dice"
  },
  swrpg_pro: {
    name: "Star Wars RPG - Proficiency",
    category: "Star Wars\u2122 RPG",
    foreground: "#FFFF00",
    background: ["#CABB1C", "#F9E33B", "#FFE900", "#F0E49D"],
    outline: "#000000",
    texture: "paper",
    description: "Star Wars\u2122 RPG Proficiency Dice"
  },
  swrpg_dif: {
    name: "Star Wars RPG - Difficulty",
    category: "Star Wars\u2122 RPG",
    foreground: "#8000FC",
    background: ["#39165F", "#664B84", "#50247E", "#745F88"],
    outline: "#000000",
    texture: "cloudy_2",
    description: "Star Wars\u2122 RPG Difficulty Dice"
  },
  swrpg_cha: {
    name: "Star Wars RPG - Challenge",
    category: "Star Wars\u2122 RPG",
    foreground: "#FF0000",
    background: ["#A91F32", "#EB4254", "#E51836", "#BA3645"],
    outline: "#000000",
    texture: "paper",
    description: "Star Wars\u2122 RPG Challenge Dice"
  },
  swrpg_boo: {
    name: "Star Wars RPG - Boost",
    category: "Star Wars\u2122 RPG",
    foreground: "#00FFFF",
    background: ["#4B9DC6", "#689FC4", "#85CFF2", "#8FC0D8"],
    outline: "#000000",
    texture: "glitter",
    description: "Star Wars\u2122 RPG Boost Dice"
  },
  swrpg_set: {
    name: "Star Wars RPG - Setback",
    category: "Star Wars\u2122 RPG",
    foreground: "#111111",
    background: ["#252223", "#241F21", "#282828", "#111111"],
    outline: "#ffffff",
    texture: "glitter",
    description: "Star Wars\u2122 RPG Setback Dice"
  },
  swrpg_for: {
    name: "Star Wars RPG - Force",
    category: "Star Wars\u2122 RPG",
    foreground: "#000000",
    background: ["#F3F3F3", "#D3D3D3", "#BABABA", "#FFFFFF"],
    outline: "#FFFFFF",
    texture: "stars",
    description: "Star Wars\u2122 RPG Force Dice"
  },
  swa_red: {
    name: "Armada Attack - Red",
    category: "Star Wars\u2122 Armada",
    foreground: "#ffffff",
    background: ["#440D19", "#8A1425", "#C72336", "#C04551"],
    outline: "none",
    texture: "stainedglass",
    description: "Star Wars\u2122 Armada Red Attack Dice"
  },
  swa_blue: {
    name: "Armada Attack - Blue",
    category: "Star Wars\u2122 Armada",
    foreground: "#ffffff",
    background: ["#212642", "#28286E", "#2B348C", "#3D4BB5", "#5D64AB"],
    outline: "none",
    texture: "stainedglass",
    description: "Star Wars\u2122 Armada Blue Attack Dice"
  },
  swa_black: {
    name: "Armada Attack - Black",
    category: "Star Wars\u2122 Armada",
    foreground: "#ffffff",
    background: ["#252223", "#241F21", "#282828", "#111111"],
    outline: "none",
    texture: "stainedglass",
    description: "Star Wars\u2122 Armada Black Attack Dice"
  },
  xwing_red: {
    name: "X-Wing Attack - Red",
    category: "Star Wars\u2122 X-Wing",
    foreground: "#ffffff",
    background: ["#440D19", "#8A1425", "#C72336", "#C04551"],
    outline: "none",
    texture: "stars",
    description: "Star Wars\u2122 X-Wing Red Attack Dice"
  },
  xwing_green: {
    name: "X-Wing Attack - Green",
    category: "Star Wars\u2122 X-Wing",
    foreground: "#ffffff",
    background: ["#3D9238", "#52B848", "#5EAC56", "#9ECB9A"],
    outline: "none",
    texture: "stars",
    description: "Star Wars\u2122 X-Wing Green Attack Dice"
  },
  swl_atkred: {
    name: "Legion Attack - Red",
    category: "Star Wars\u2122 Legion",
    foreground: "#ffffff",
    background: ["#440D19", "#8A1425", "#C72336", "#C04551"],
    outline: "none",
    texture: "fire",
    description: "Star Wars\u2122 Legion Red Attack Dice"
  },
  swl_atkblack: {
    name: "Legion Attack - Black",
    category: "Star Wars\u2122 Legion",
    foreground: "#ffffff",
    background: ["#252223", "#241F21", "#282828", "#111111"],
    outline: "none",
    texture: "fire",
    description: "Star Wars\u2122 Legion Black Attack Dice"
  },
  swl_atkwhite: {
    name: "Legion Attack - White",
    category: "Star Wars\u2122 Legion",
    foreground: "#000000",
    background: ["#ffffff", "#DFF4FA", "#BCBCBC", "#F1EDE2", "#F2ECE0"],
    outline: "none",
    texture: "fire",
    description: "Star Wars\u2122 Legion White Attack Dice"
  },
  swl_defred: {
    name: "Legion Defense - Red",
    category: "Star Wars\u2122 Legion",
    foreground: "#ffffff",
    background: ["#440D19", "#8A1425", "#C72336", "#C04551"],
    outline: "none",
    texture: "fire",
    description: "Star Wars\u2122 Legion Red Defense Dice"
  },
  swl_defwhite: {
    name: "Legion Defense - White",
    category: "Star Wars\u2122 Legion",
    foreground: "#000000",
    background: ["#ffffff", "#DFF4FA", "#BCBCBC", "#F1EDE2", "#F2ECE0"],
    outline: "none",
    texture: "fire",
    description: "Star Wars\u2122 Legion White Defense Dice"
  }
};
class Mp {
  constructor(e = {}) {
    this.colorsets = [], this.assetPath = e.assetPath;
  }
  async ImageLoader(e) {
    if (Array.isArray(e)) {
      for (let t = 0, n = e.length; t < n; t++)
        e[t] = await this.ImageLoader(e[t]);
      return e;
    }
    return e.source && e.source != "" && (e.texture = await this.loadImage(e.source)), e.source_bump && e.source_bump != "" && (e.bump = await this.loadImage(e.source_bump)), e;
  }
  loadImage(e) {
    return new Promise((t, n) => {
      let i = new Image();
      i.onload = () => t(i), i.crossOrigin = "anonymous", i.src = this.assetPath + e, i.onerror = (s) => n(s);
    }).catch((t) => {
      console.error("Unable to load image texture");
    });
  }
  async getColorSet(e) {
    let t, n;
    if (typeof e == "string" && (t = e), typeof e == "object" && (t = e.colorset), this.colorsets.hasOwnProperty(t))
      return this.colorsets[t];
    let i = eo[t];
    return n = e.texture || i.texture, i.texture = this.getTexture(n), i.texture = await this.ImageLoader(i.texture), e.material && (i.texture.material = e.material), this.colorsets[t] = i, i;
  }
  async makeColorSet(e = {}) {
    if (this.colorsets.hasOwnProperty(e.name))
      return this.colorsets[e.name];
    let t = eo.white, n = Object.assign({}, t, e), i = this.getTexture(n.texture);
    return n.texture = await this.ImageLoader(i), e.material && (n.texture.material = e.material), n.name.toLowerCase() === "white" && (n.name = `${Date.now()}`), this.colorsets[n.name] = n, n;
  }
  getTexture(e) {
    if (Array.isArray(e)) {
      let t = [];
      for (let n = 0, i = e.length; n < i; n++)
        t.push(this.getTexture(e[n]));
      return t;
    }
    return Is.hasOwnProperty(e) ? Is[e] : Is.none;
  }
}
const Sp = {
  default: {
    name: "Solid Color",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "wood_tray",
    colors: { fg: "#9794ff", bg: "#0b1a3e" },
    cubeMap: ["envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg"]
  },
  "blue-felt": {
    name: "Blue Felt",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "felt",
    colors: { fg: "#9794ff", bg: "#0b1a3e" },
    cubeMap: ["envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg"]
  },
  "red-felt": {
    name: "Red Felt",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "felt",
    colors: { fg: "#ff9494", bg: "#4d1e1e" },
    cubeMap: ["envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg"]
  },
  "green-felt": {
    name: "Green Felt",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "felt",
    colors: { fg: "#97ff94", bg: "#244d1e" },
    cubeMap: ["envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg", "envmap.jpg"]
  },
  taverntable: {
    name: "Old Tavern Table",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "wood_table",
    colors: { fg: "#9794ff", bg: "#0b1a3e" },
    cubeMap: ["px.png", "nx.png", "py.png", "ny.png", "pz.png", "nz.png"]
  },
  mahogany: {
    name: "(Mah-Hog-Any)",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "wood_table",
    colors: { fg: "#9794ff", bg: "#0b1a3e" },
    cubeMap: ["px.png", "nx.png", "py.png", "ny.png", "pz.png", "nz.png"]
  },
  stainless: {
    name: "Stainless Steel",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "metal",
    colors: { fg: "#9794ff", bg: "#0b1a3e" },
    cubeMap: ["px.png", "nx.png", "py.png", "ny.png", "pz.png", "nz.png"]
  },
  cyberpunk: {
    name: "Neo-New-Future-City",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "metal",
    colors: { fg: "#3494A6", bg: "#440B28" },
    cubeMap: ["px.png", "nx.png", "py.png", "ny.png", "pz.png", "nz.png"]
  },
  cagetown: {
    name: "Cage Town",
    author: "MajorVictory",
    showColorPicker: !0,
    surface: "wood_table",
    colors: { fg: "#D7A866", bg: "#282811" },
    cubeMap: ["px.png", "nx.png", "py.png", "ny.png", "pz.png", "nz.png"]
  }
}, Ep = (h) => {
  let e;
  return function() {
    let t = this, n = arguments;
    e && window.cancelAnimationFrame(e), e = window.requestAnimationFrame(function() {
      h.apply(t, n);
    });
  };
}, Tp = {
  assetPath: "./",
  framerate: 1 / 60,
  sounds: !1,
  volume: 100,
  color_spotlight: 15720405,
  shadows: !0,
  theme_surface: "green-felt",
  sound_dieMaterial: "plastic",
  theme_customColorset: null,
  theme_colorset: "white",
  theme_texture: "",
  theme_material: "glass",
  gravity_multiplier: 400,
  light_intensity: 0.7,
  baseScale: 100,
  strength: 1,
  iterationLimit: 1e3,
  onRollComplete: () => {
  },
  onRerollComplete: () => {
  },
  onAddDiceComplete: () => {
  },
  onRemoveDiceComplete: () => {
  }
};
class Cp {
  constructor(e, t = {}) {
    this.initialized = !1, this.container = document.querySelector(e), this.dimensions = new Ce(this.container.clientWidth, this.container.clientHeight), this.adaptive_timestep = !1, this.last_time = 0, this.running = !1, this.rolling = !1, this.threadid, this.display = {
      currentWidth: null,
      currentHeight: null,
      containerWidth: null,
      containerHeight: null,
      aspect: null,
      scale: null
    }, this.cameraHeight = {
      max: null,
      close: null,
      medium: null,
      far: null
    }, this.scene = new Nu(), this.world = new dp(), this.dice_body_material = new Sn(), this.sounds_table = {}, this.sounds_dice = [], this.lastSoundType = "", this.lastSoundStep = 0, this.lastSound = 0, this.iteration, this.renderer, this.barrier, this.camera, this.light, this.light_amb, this.desk, this.box_body = {}, this.bodies = [], this.meshes = [], this.diceList = [], this.notationVectors = null, this.dieIndex = 0, this.soundDelay = 10, this.animstate = "", this.selector = {
      animate: !0,
      rotate: !0,
      intersected: null,
      dice: []
    }, Object.assign(this, Tp, t), this.DiceColors = new Mp({ assetPath: this.assetPath }), this.DiceFactory = new Hi({
      baseScale: this.baseScale
    }), this.DiceFactory.setBumpMapping(!0), this.surface = Sp[this.theme_surface].surface;
  }
  enableShadows() {
    this.shadows = !0, this.renderer && (this.renderer.shadowMap.enabled = this.shadows), this.light && (this.light.castShadow = this.shadows), this.desk && (this.desk.receiveShadow = this.shadows);
  }
  disableShadows() {
    this.shadows = !1, this.renderer && (this.renderer.shadowMap.enabled = this.shadows), this.light && (this.light.castShadow = this.shadows), this.desk && (this.desk.receiveShadow = this.shadows);
  }
  async initialize() {
    this.renderer = new xo({ antialias: !0, alpha: !0 }), this.container.appendChild(this.renderer.domElement), this.renderer.shadowMap.enabled = this.shadows, this.renderer.shadowMap.type = 2, this.renderer.setClearColor(0, 0), this.setDimensions(this.dimensions), this.world.gravity.set(0, 0, -9.8 * this.gravity_multiplier), this.world.broadphase = new wo(), this.world.solver.iterations = 14, this.world.allowSleep = !0, this.makeWorldBox(), this.resizeWorld(), await this.loadTheme({
      colorset: this.theme_colorset,
      texture: this.theme_texture,
      material: this.theme_material
    }).catch((e) => {
      throw new Error("Unable to load theme");
    }), this.sounds && await this.loadSounds().catch((e) => {
      throw new Error("Unable to load sounds");
    }), this.initialized = !0, this.renderer.render(this.scene, this.camera);
  }
  makeWorldBox() {
    Object.keys(this.box_body).length && (this.world.removeBody(this.box_body.desk), this.world.removeBody(this.box_body.topWall), this.world.removeBody(this.box_body.bottomWall), this.world.removeBody(this.box_body.leftWall), this.world.removeBody(this.box_body.rightWall));
    const e = new Sn(), t = new Sn();
    this.world.addContactMaterial(new Mn(e, this.dice_body_material, { mass: 0, friction: 0.6, restitution: 0.5 })), this.world.addContactMaterial(new Mn(t, this.dice_body_material, { mass: 0, friction: 0.6, restitution: 1 })), this.world.addContactMaterial(new Mn(this.dice_body_material, this.dice_body_material, { mass: 0, friction: 0.6, restitution: 0.5 })), this.box_body.desk = new ie({ allowSleep: !1, mass: 0, shape: new si(), material: e }), this.world.addBody(this.box_body.desk), this.box_body.topWall = new ie({ allowSleep: !1, mass: 0, shape: new si(), material: t }), this.box_body.topWall.quaternion.setFromAxisAngle(new b(1, 0, 0), Math.PI / 2), this.box_body.topWall.position.set(0, this.display.containerHeight * 0.93, 0), this.world.addBody(this.box_body.topWall), this.box_body.bottomWall = new ie({ allowSleep: !1, mass: 0, shape: new si(), material: t }), this.box_body.bottomWall.quaternion.setFromAxisAngle(new b(1, 0, 0), -Math.PI / 2), this.box_body.bottomWall.position.set(0, -this.display.containerHeight * 0.93, 0), this.world.addBody(this.box_body.bottomWall), this.box_body.leftWall = new ie({ allowSleep: !1, mass: 0, shape: new si(), material: t }), this.box_body.leftWall.quaternion.setFromAxisAngle(new b(0, 1, 0), -Math.PI / 2), this.box_body.leftWall.position.set(this.display.containerWidth * 0.93, 0, 0), this.world.addBody(this.box_body.leftWall), this.box_body.rightWall = new ie({ allowSleep: !1, mass: 0, shape: new si(), material: t }), this.box_body.rightWall.quaternion.setFromAxisAngle(new b(0, 1, 0), Math.PI / 2), this.box_body.rightWall.position.set(-this.display.containerWidth * 0.93, 0, 0), this.world.addBody(this.box_body.rightWall);
  }
  async loadTheme(e) {
    let t;
    this.theme_customColorset ? t = await this.DiceColors.makeColorSet(this.theme_customColorset) : t = await this.DiceColors.getColorSet(e), this.DiceFactory.applyColorSet(t), this.colorData = t;
  }
  async loadSounds() {
    let e = {
      felt: 7,
      wood_table: 7,
      wood_tray: 7,
      metal: 9
    }, t = {
      coin: 6,
      metal: 12,
      plastic: 15,
      wood: 12
    };
    const n = this.colorData.texture.material.match(/wood|metal/g);
    if (this.sound_dieMaterial = n ? this.colorData.texture.material : "plastic", !this.sounds_table.hasOwnProperty(this.surface)) {
      this.sounds_table[this.surface] = [];
      let i = e[this.surface];
      for (let s = 1; s <= i; ++s) {
        const o = await this.loadAudio(this.assetPath + "sounds/surfaces/surface_" + this.surface + s + ".mp3");
        this.sounds_table[this.surface].push(o);
      }
    }
    if (!this.sounds_dice.hasOwnProperty("coin")) {
      this.sounds_dice.coin = [];
      let i = t.coin;
      for (let s = 1; s <= i; ++s) {
        const o = await this.loadAudio(this.assetPath + "sounds/dicehit/dicehit_coin" + s + ".mp3");
        this.sounds_dice.coin.push(o);
      }
    }
    if (!this.sounds_dice.hasOwnProperty(this.sound_dieMaterial)) {
      this.sounds_dice[this.sound_dieMaterial] = [];
      let i = t[this.sound_dieMaterial];
      for (let s = 1; s <= i; ++s) {
        const o = await this.loadAudio(this.assetPath + "sounds/dicehit/dicehit_" + this.sound_dieMaterial + s + ".mp3");
        this.sounds_dice[this.sound_dieMaterial].push(o);
      }
    }
  }
  loadAudio(e) {
    return new Promise((t, n) => {
      let i = new Audio();
      i.oncanplaythrough = () => t(i), i.crossOrigin = "anonymous", i.src = e, i.onerror = (s) => n(s);
    }).catch((t) => {
      console.error("Unable to load audio");
    });
  }
  async updateConfig(e = {}) {
    Object.apply(this, e), this.theme_customColorset = e.theme_customColorset ? e.theme_customColorset : null, e.theme_colorset && (this.theme_colorset = e.theme_colorset), e.theme_texture && (this.theme_texture = e.theme_texture), e.theme_material && (this.theme_material = e.theme_material), (e.theme_colorset || e.theme_texture || e.theme_material || e.theme_customColorset) && await this.loadTheme({
      colorset: this.theme_colorset,
      texture: this.theme_texture,
      material: this.theme_material
    });
  }
  setDimensions(e) {
    switch (this.display.currentWidth = this.container.clientWidth / 2, this.display.currentHeight = this.container.clientHeight / 2, e ? (this.display.containerWidth = e.x, this.display.containerHeight = e.y) : (this.display.containerWidth = this.display.currentWidth, this.display.containerHeight = this.display.currentHeight), this.display.aspect = Math.min(this.display.currentWidth / this.display.containerWidth, this.display.currentHeight / this.display.containerHeight), this.display.scale = Math.sqrt(this.display.containerWidth * this.display.containerWidth + this.display.containerHeight * this.display.containerHeight) / 13, this.makeWorldBox(), this.renderer.setSize(this.display.currentWidth * 2, this.display.currentHeight * 2), this.cameraHeight.max = this.display.currentHeight / this.display.aspect / Math.tan(10 * Math.PI / 180), this.cameraHeight.medium = this.cameraHeight.max / 1.5, this.cameraHeight.far = this.cameraHeight.max, this.cameraHeight.close = this.cameraHeight.max / 2, this.camera && this.scene.remove(this.camera), this.camera = new gt(20, this.display.currentWidth / this.display.currentHeight, 1, this.cameraHeight.max * 1.3), this.animstate) {
      case "selector":
        this.camera.position.z = this.selector.dice.length > 9 ? this.cameraHeight.far : this.selector.dice.length < 6 ? this.cameraHeight.close : this.cameraHeight.medium;
        break;
      case "throw":
      case "afterthrow":
      default:
        this.camera.position.z = this.cameraHeight.far;
    }
    this.camera.lookAt(new O(0, 0, 0));
    const t = Math.max(this.display.containerWidth, this.display.containerHeight);
    this.light && this.scene.remove(this.light), this.light_amb && this.scene.remove(this.light_amb), this.light = new Hu(this.color_spotlight, this.light_intensity), this.light.position.set(-t / 2, t / 2, t * 3), this.light.target.position.set(0, 0, 0), this.light.distance = t * 5, this.light.angle = Math.PI / 4, this.light.castShadow = this.shadows, this.light.shadow.camera.near = t / 10, this.light.shadow.camera.far = t * 5, this.light.shadow.camera.fov = 50, this.light.shadow.bias = 1e-3, this.light.shadow.mapSize.width = 1024, this.light.shadow.mapSize.height = 1024, this.scene.add(this.light), this.light_amb = new ku(16777147, 6776689, this.light_intensity), this.scene.add(this.light_amb), this.desk && this.scene.remove(this.desk);
    let n = new Ou();
    n.opacity = 0.5, this.desk = new Nt(new ji(this.display.containerWidth * 6, this.display.containerHeight * 6, 1, 1), n), this.desk.receiveShadow = this.shadows, this.scene.add(this.desk), this.renderer.render(this.scene, this.camera);
  }
  resizeWorld() {
    const t = Ep(() => {
      const n = this.renderer.domElement, i = this.container.clientWidth, s = this.container.clientHeight, o = n.width !== i || n.height !== s;
      return o && this.setDimensions(new Ce(this.container.clientWidth, this.container.clientHeight)), o;
    });
    window.addEventListener("resize", t);
  }
  vectorRand({ x: e, y: t }) {
    let n = Math.random() * Math.PI / 5 - Math.PI / 5 / 2, i = {
      x: e * Math.cos(n) - t * Math.sin(n),
      y: e * Math.sin(n) + t * Math.cos(n)
    };
    return i.x == 0 && (i.x = 0.01), i.y == 0 && (i.y = 0.01), i;
  }
  getNotationVectors(e, t, n, i) {
    let s = new Qr(e);
    for (let o in s.set) {
      const r = this.DiceFactory.get(s.set[o].type);
      let l = s.set[o].num, a = s.set[o].op, c = s.set[o].sid, d = s.set[o].gid, u = s.set[o].glvl, m = s.set[o].func, g = s.set[o].args;
      for (let p = 0; p < l; p++) {
        let f = this.vectorRand(t);
        f.x /= i, f.y /= i;
        let v = {
          x: this.display.containerWidth * (f.x > 0 ? -1 : 1) * 0.9,
          y: this.display.containerHeight * (f.y > 0 ? -1 : 1) * 0.9,
          z: Math.random() * 200 + 200
        }, _ = Math.abs(f.x / f.y);
        _ > 1 ? v.y /= _ : v.x *= _;
        let w = this.vectorRand(t);
        w.x /= i, w.y /= i;
        let x, M, E;
        r.shape != "d2" ? (x = {
          x: w.x * n,
          y: w.y * n,
          z: -10
        }, M = {
          x: -(Math.random() * f.y * 5 + r.inertia * f.y),
          y: Math.random() * f.x * 5 + r.inertia * f.x,
          z: 0
        }, E = {
          x: Math.random(),
          y: Math.random(),
          z: Math.random(),
          a: Math.random()
        }) : (x = {
          x: w.x * n / 10,
          y: w.y * n / 10,
          z: 3e3
        }, M = {
          x: 12 * r.inertia,
          y: 1 * r.inertia,
          z: 0
        }, E = {
          x: 1,
          y: 1,
          z: Math.random(),
          a: Math.random()
        }), s.vectors.push({
          index: this.dieIndex++,
          type: r.type,
          op: a,
          sid: c,
          gid: d,
          glvl: u,
          func: m,
          args: g,
          pos: v,
          velocity: x,
          angle: M,
          axis: E
        });
      }
    }
    return s;
  }
  swapDiceFace(e, t) {
    const n = this.DiceFactory.get(e.notation.type);
    if (e.resultReason = "forced", n.shape == "d4") {
      this.swapDiceFace_D4(e, t);
      return;
    }
    n.values;
    let i = parseInt(e.getLastValue().value);
    t = parseInt(t), e.notation.type == "d10" && i == 0 && (i = 10), e.notation.type == "d100" && i == 0 && (i = 100), e.notation.type == "d100" && i > 0 && i < 10 && (i *= 10), e.notation.type == "d10" && t == 0 && (t = 10), e.notation.type == "d100" && t == 0 && (t = 100), e.notation.type == "d100" && t > 0 && t < 10 && (t *= 10);
    let s = n.values.indexOf(i), o = n.values.indexOf(t);
    if (s < 0 || o < 0 || s == o)
      return;
    let r = e.geometry.clone(), l = [], a = [], c = 2;
    n.shape == "d10" && (c = 1);
    let d, u = o + c;
    n.shape != "d2" ? (d = s + c, u = o + c) : (d = s + 1, u = o + 1);
    for (var m = 0, g = r.groups.length; m < g; ++m) {
      const f = r.groups[m].materialIndex;
      if (f == d) {
        l.push(m);
        continue;
      }
      if (f == u) {
        a.push(m);
        continue;
      }
    }
    if (!(l.length <= 0 || a.length <= 0)) {
      for (let p = 0, f = a.length; p < f; p++)
        r.groups[a[p]].materialIndex = d;
      for (let p = 0, f = l.length; p < f; p++)
        r.groups[l[p]].materialIndex = u;
      e.geometry = r, e.result = [];
    }
  }
  swapDiceFace_D4(e, t) {
    const n = this.DiceFactory.get(e.notation.type);
    let i = parseInt(e.getLastValue().value);
    if (t = parseInt(t), !(i >= 1 && i <= 4))
      return;
    let s = t - i, o = e.geometry.clone();
    for (let r = 0, l = o.groups.length; r < l; ++r) {
      const a = o.groups[r];
      let c = a.materialIndex;
      if (c != 0) {
        for (c += s - 1; c > 4; )
          c -= 4;
        for (; c < 1; )
          c += 4;
        a.materialIndex = c + 1;
      }
    }
    s != 0 && (s < 0 && (s += 4), e.material = this.DiceFactory.createMaterials(n, 0, 0, !1, s)), e.geometry = o;
  }
  spawnDice(e, t = !1) {
    const { pos: n, axis: i, angle: s, velocity: o } = e;
    let r;
    if (t)
      r = t, r.stopped = 0, this.world.removeBody(r.body);
    else {
      if (r = this.DiceFactory.create(e.type, this.colorData), !r)
        return;
      r.notation = e, r.result = [], r.stopped = 0, r.castShadow = this.shadows, this.scene.add(r), this.diceList.push(r);
    }
    r.body = new ie({ allowSleep: !0, sleepSpeedLimit: 75, sleepTimeLimit: 0.9, mass: r.mass, shape: r.geometry.cannon_shape, material: this.dice_body_material }), r.body.type = ie.DYNAMIC, r.body.position.set(n.x, n.y, n.z), r.body.quaternion.setFromAxisAngle(new b(i.x, i.y, i.z), i.a * Math.PI * 2), r.body.angularVelocity.set(s.x, s.y, s.z), r.body.velocity.set(o.x, o.y, o.z), r.body.linearDamping = 0.1, r.body.angularDamping = 0.1, r.body.diceShape = r.shape, r.body.sleepState = 0, r.body.addEventListener("collide", this.eventCollide.bind(this)), this.world.addBody(r.body);
  }
  eventCollide({ body: e, target: t }) {
    if (this.animstate == "simulate" || !this.sounds || !e || this.volume <= 0)
      return;
    let n = Date.now(), i = e.mass > 0 ? "dice" : "table";
    if (!((this.lastSoundStep == e.world.stepnumber || this.lastSound > n) && i != "dice") && !((this.lastSoundStep == e.world.stepnumber || this.lastSound > n) && i == "dice" && this.lastSoundType == "dice")) {
      if (e.mass > 0) {
        let s = e.velocity.length();
        if (s < 250)
          return;
        let o;
        e.diceShape === "d2" ? o = this.sounds_dice.coin[Math.floor(Math.random() * this.sounds_dice.coin.length)] : o = this.sounds_dice[this.sound_dieMaterial][Math.floor(Math.random() * this.sounds_dice[this.sound_dieMaterial].length)], o && (o.volume = Math.min(s / 8e3, this.volume / 100), o.play().catch((r) => {
        })), this.lastSoundType = "dice";
      } else {
        let s = t.velocity.length();
        if (s < 250)
          return;
        let o = this.surface, r = this.sounds_table[o], l = r[Math.floor(Math.random() * r.length)];
        l && (l.volume = Math.min(s / 8e3, this.volume / 100), l.play().catch((a) => {
        })), this.lastSoundType = "table";
      }
      this.lastSoundStep = e.world.stepnumber, this.lastSound = n + this.soundDelay;
    }
  }
  checkForRethrow(e) {
    let t = e.notation.func ? e.notation.func.toLowerCase() : "", n, i = !1;
    if (t != "" && n && n.method) {
      t = e.notation.func.toLowerCase();
      let s = e.notation.args || "";
      i = n.method(e, s);
    }
    return i;
  }
  throwFinished() {
    const e = this.iteration > this.iterationLimit;
    for (let t = 0, n = this.diceList.length; t < n; ++t) {
      const i = this.diceList[t], s = ie.SLEEPING;
      if (i.body.sleepState < s && !e)
        return !1;
      if (i.body.sleepState == s || e) {
        if (i.body.type === ie.KINEMATIC)
          continue;
        let o = !1;
        if (i.result.length == 0 ? (i.storeRolledValue(i.resultReason), o = this.checkForRethrow(i)) : i.result.length > 0 && i.rerolling && (i.rerolling = !1, i.storeRolledValue("reroll"), o = this.checkForRethrow(i)), o)
          return i.rerolls += 1, i.rerolling = !0, i.body.wakeUp(), i.body.type = ie.DYNAMIC, i.body.angularVelocity = new b(25, 25, 25), i.body.velocity = new b(0, 0, 3e3), !1;
        i.rerolling = !1, i.body.type = ie.KINEMATIC;
      }
    }
    return !0;
  }
  simulateThrow() {
    for (this.animstate = "simulate", this.iteration = 0, this.rolling = !0; !this.throwFinished(!0); )
      ++this.iteration, this.world.step(this.framerate);
  }
  animateThrow(e, t) {
    this.animstate = "throw";
    let n = Date.now();
    this.last_time = this.last_time || n - this.framerate * 1e3;
    let i = (n - this.last_time) / 1e3;
    ++this.iteration;
    let s = Math.floor(i / this.framerate);
    for (let o = 0; o < s; o++)
      this.world.step(this.framerate), ++this.steps;
    for (let o in this.scene.children) {
      let r = this.scene.children[o];
      r.body != null && (r.position.copy(r.body.position), r.quaternion.copy(r.body.quaternion));
    }
    if (this.renderer.render(this.scene, this.camera), this.last_time = this.last_time + s * this.framerate * 1e3, this.running == e && this.throwFinished()) {
      this.running = !1, this.rolling = !1, t && t.call(this, this.notationVectors), this.running = Date.now(), this.animateAfterThrow(this.running);
      return;
    }
    this.running == e && ((o, r, l, a, c) => {
      !l && i < this.framerate ? setTimeout(() => {
        requestAnimationFrame(() => {
          o.call(this, r, a, c);
        });
      }, (this.framerate - i) * 1e3) : requestAnimationFrame(() => {
        o.call(this, r, a, c);
      });
    }).bind(this)(this.animateThrow, e, this.adaptive_timestep, t);
  }
  animateAfterThrow(e) {
    this.animstate = "afterthrow";
    let t = Date.now(), n = (t - this.last_time) / 1e3;
    n > 3 && (n = this.framerate), this.running = !1, this.last_time = t, this.renderer.render(this.scene, this.camera), this.running == e && ((i, s, o) => {
      !o && n < this.framerate ? setTimeout(() => {
        requestAnimationFrame(() => {
          i.call(this, s);
        });
      }, (this.framerate - n) * 1e3) : requestAnimationFrame(() => {
        i.call(this, s);
      });
    }).bind(this)(this.animateAfterThrow, e, this.adaptive_timestep);
  }
  startClickThrow(e) {
    this.rolling && (this.clearDice(), this.rolling = !1);
    let t = { x: (Math.random() * 2 - 0.5) * this.display.currentWidth, y: -(Math.random() * 2 - 0.5) * this.display.currentHeight }, n = Math.sqrt(t.x * t.x + t.y * t.y) + 100, i = (Math.random() + 3) * n * this.strength;
    return this.getNotationVectors(e, t, i, n);
  }
  clearDice() {
    this.running = !1;
    let e;
    for (; e = this.diceList.pop(); )
      this.scene.remove(e), e.body && this.world.removeBody(e.body);
    this.renderer.render(this.scene, this.camera), setTimeout(() => {
      this.renderer.render(this.scene, this.camera);
    }, 100);
  }
  getDiceResults(e) {
    if (e !== void 0)
      return {
        type: this.diceList[e].shape,
        sides: parseInt(this.diceList[e].shape.substring(1)),
        id: e,
        ...this.diceList[e].result.at(-1)
      };
    let t = 0;
    const n = this.notationVectors.constant ? parseInt(`${this.notationVectors.op}${this.notationVectors.constant}`) : 0;
    let i = n;
    return {
      notation: this.notationVectors.notation,
      sets: this.notationVectors.set.map((o) => {
        const r = t + o.num - 1;
        let l = 0;
        const a = [];
        for (let d = t; d <= r; d++) {
          if (this.diceList[t].result.at(-1).reason === "remove") {
            t++;
            continue;
          }
          a.push({
            type: o.type,
            sides: parseInt(o.type.substring(1)),
            id: t,
            ...this.diceList[t].result.at(-1)
          }), l += this.diceList[t].result.at(-1).value, t++;
        }
        const c = {
          num: o.num,
          type: o.type,
          sides: parseInt(o.type.substring(1)),
          rolls: a,
          total: l
        };
        return i += l, c;
      }),
      modifier: n,
      total: i
    };
  }
  async roll(e) {
    if (this.notationVectors = this.startClickThrow(e), this.notationVectors)
      return new Promise((t, n) => {
        this.rollDice(() => {
          const i = this.getDiceResults();
          this.onRollComplete(i);
          const s = new CustomEvent("rollComplete", { detail: i });
          document.dispatchEvent(s), t(i);
        });
      });
  }
  async reroll(e) {
    return this.rolling = !0, this.running = Date.now(), this.iteration = 0, new Promise((t, n) => {
      e.forEach((i) => {
        const s = this.diceList[i];
        s.rerolls += 1, s.rerolling = !0, s.body.wakeUp(), s.body.type = ie.DYNAMIC, s.body.angularVelocity = new b(25, 25, 25), s.body.velocity = new b(0, 0, 3e3);
      }), this.animateThrow(this.running, () => {
        const i = e.map((o) => this.getDiceResults(o));
        this.onRerollComplete(i);
        const s = new CustomEvent("rerollComplete", { detail: i });
        document.dispatchEvent(s), t(i);
      });
    });
  }
  async add(e) {
    let t = this.diceList.length;
    if (!t)
      return this.roll(e);
    let n = this.startClickThrow(e), i = [];
    for (let s = 0, o = n.vectors.length; s < o; ++s)
      this.spawnDice(n.vectors[s]);
    this.simulateThrow(), this.steps = 0, this.iteration = 0;
    for (let s = 0, o = n.vectors.length; s < o; ++s) {
      const r = t + s;
      !this.diceList[r] || (this.spawnDice(n.vectors[s], this.diceList[r]), i.push(r));
    }
    if (n.result && n.result.length > 0)
      for (let s = 0; s < n.result.length; s++) {
        const o = t + s;
        let r = this.diceList[o];
        !r || r.getLastValue().value != n.result[s] && this.swapDiceFace(r, n.result[s]);
      }
    return this.notationVectors = Qr.mergeNotation(this.notationVectors, n), new Promise((s, o) => {
      const r = () => {
        const l = i.map((c) => this.getDiceResults(c));
        this.onAddDiceComplete(l);
        const a = new CustomEvent("addDiceComplete", { detail: l });
        document.dispatchEvent(a), s(l);
      };
      this.rolling = !0, this.running = Date.now(), this.last_time = 0, this.animateThrow(this.running, r);
    });
  }
  async remove(e) {
    return new Promise((t, n) => {
      const i = [];
      e.forEach((o) => {
        const r = this.diceList[o];
        r.body && this.world.removeBody(r.body), this.scene.remove(r), r.storeRolledValue("remove"), i.push(this.getDiceResults(o));
      }), this.renderer.render(this.scene, this.camera), this.onRemoveDiceComplete(i);
      const s = new CustomEvent("removeDiceComplete", { detail: i });
      document.dispatchEvent(s), t(i);
    });
  }
  rollDice(e) {
    if (this.notationVectors.error) {
      e.call(this);
      return;
    }
    this.clearDice();
    for (let t = 0, n = this.notationVectors.vectors.length; t < n; ++t)
      this.spawnDice(this.notationVectors.vectors[t]);
    this.simulateThrow(), this.steps = 0, this.iteration = 0;
    for (let t = 0, n = this.diceList.length; t < n; ++t)
      !this.diceList[t] || this.spawnDice(this.notationVectors.vectors[t], this.diceList[t]);
    if (this.notationVectors.result && this.notationVectors.result.length > 0)
      for (let t = 0; t < this.notationVectors.result.length; t++) {
        let n = this.diceList[t];
        !n || n.getLastValue().value != this.notationVectors.result[t] && this.swapDiceFace(n, this.notationVectors.result[t]);
      }
    this.rolling = !0, this.running = Date.now(), this.last_time = 0, this.animateThrow(this.running, e);
  }
}
export {
  Cp as default
};
