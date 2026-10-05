import test from 'node:test';
import assert from 'node:assert/strict';
import {previewPosition} from '../../app/static/src/js/preview-position.js';

test('article and expanded map previews leave source links clickable at viewport edges',()=>{
  for(const [viewportWidth,viewportHeight] of [[2300,1300],[1280,800],[390,844]]) {
    for(const y of [16,viewportHeight/2,viewportHeight-40]) {
      const link={left:16,right:316,top:y,bottom:y+24};
      for(const [wantedWidth,wantedHeight] of [[760,680],[1240,1160]]) {
        const width=Math.min(wantedWidth,viewportWidth-16),height=Math.min(wantedHeight,viewportHeight-16);
        const panel=previewPosition(link,width,height,viewportWidth,viewportHeight);
        const right=panel.left+width,bottom=panel.top+Math.min(height,panel.maxHeight);
        assert(panel.left>=8 && panel.top>=8);
        assert(right<=viewportWidth-8 && bottom<=viewportHeight-8);
        assert(right<=link.left || panel.left>=link.right || bottom<=link.top || panel.top>=link.bottom);
      }
    }
  }
});
