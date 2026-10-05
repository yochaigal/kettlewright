import test from 'node:test';
import assert from 'node:assert/strict';
import {fittedViewport} from '../../app/static/src/js/maps/viewport.js';

test('large maps fill the viewport without rounding zoom down to 10% steps',()=>{
  const bounds=[420,-200,2230,1800];
  for(const [width,height] of [[1400,640],[390,520]]) {
    const view=fittedViewport(bounds,width,height), zoom=view.zoom.value;
    const x=(bounds[0]+view.scrollX)*zoom, y=(bounds[1]+view.scrollY)*zoom;
    const sceneWidth=(bounds[2]-bounds[0])*zoom, sceneHeight=(bounds[3]-bounds[1])*zoom;
    assert(Math.abs(Math.max(sceneWidth/width,sceneHeight/height)-0.9)<1e-10);
    assert(Math.abs(x-(width-sceneWidth)/2)<1e-10);
    assert(Math.abs(y-(height-sceneHeight)/2)<1e-10);
  }
});

test('small drawings zoom in and degenerate bounds remain finite',()=>{
  assert(fittedViewport([0,0,100,100],800,640).zoom.value>1);
  const point=fittedViewport([5,5,5,5],800,640);
  assert.equal(point.zoom.value,30);
  assert(Number.isFinite(point.scrollX) && Number.isFinite(point.scrollY));
});
