import test from 'node:test';
import assert from 'node:assert/strict';
import {fittedViewport, imageViewport, clampToImage, imageAspect} from '../../app/static/src/js/maps/viewport.js';

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

test('small drawings stay at 100% (a lone pin is not blown up) and degenerate bounds remain finite',()=>{
  assert.equal(fittedViewport([0,0,100,100],800,640).zoom.value,1);
  const point=fittedViewport([5,5,5,5],800,640);
  assert.equal(point.zoom.value,1);
  assert(Number.isFinite(point.scrollX) && Number.isFinite(point.scrollY));
});

// Image maps (#506): the picture fills the frame, and readers zoom and pan inside it only.
const picture=[0,0,1600,1000];
const onScreen=(bounds,{zoom,scrollX,scrollY})=>[(bounds[0]+scrollX)*zoom.value,(bounds[1]+scrollY)*zoom.value,
  (bounds[2]+scrollX)*zoom.value,(bounds[3]+scrollY)*zoom.value];

test('an image map fills its frame with no margin and may zoom past 100%',()=>{
  const view=imageViewport(picture,3200,2000);
  assert.equal(view.zoom.value,2);
  assert.deepEqual(onScreen(picture,view),[0,0,3200,2000]);
  const tall=imageViewport(picture,800,1000);  // A narrower frame: the picture is centred top to bottom.
  const [left,top,right,bottom]=onScreen(picture,tall);
  assert.equal(left,0);assert.equal(right,800);assert(Math.abs(top-(1000-bottom))<1e-9);
});

test('readers cannot zoom out past the picture or pan beyond its edges',()=>{
  const frame={width:800,height:500};
  assert.equal(clampToImage(picture,{...frame,...imageViewport(picture,800,500)}),null);  // Already inside.
  const zoomedOut=clampToImage(picture,{...frame,zoom:{value:0.1},scrollX:0,scrollY:0});
  assert.equal(zoomedOut.zoom.value,0.5);
  assert.deepEqual(onScreen(picture,zoomedOut),[0,0,800,500]);
  // Zoomed in and dragged far to the top left, then far to the bottom right: the edges stop it.
  const topLeft=clampToImage(picture,{...frame,zoom:{value:2},scrollX:900,scrollY:900});
  assert.deepEqual(onScreen(picture,topLeft).slice(0,2),[0,0]);
  const bottomRight=clampToImage(picture,{...frame,zoom:{value:2},scrollX:-5000,scrollY:-5000});
  const [, , right, bottom]=onScreen(picture,bottomRight);
  assert.equal(right,800);assert.equal(bottom,500);
});

test('the frame takes the picture\'s shape',()=>{
  assert.equal(imageAspect({elements:[{type:'text'},{type:'image',width:1600,height:1000}]}),1.6);
  assert.equal(imageAspect({elements:[{type:'image',width:1600,height:1000,isDeleted:true}]}),null);
  assert.equal(imageAspect(null),null);
});
