import test from 'node:test';
import assert from 'node:assert/strict';
import articleImage, {shrinkSize} from '../../app/static/src/js/alpine/components/article-image.js';

test('big pictures shrink to 1600 px on their longest side, small ones stay', () => {
  assert.deepEqual(shrinkSize(4000, 3000), {width: 1600, height: 1200});
  assert.deepEqual(shrinkSize(900, 3600), {width: 400, height: 1600});
  assert.deepEqual(shrinkSize(640, 480), {width: 640, height: 480});
});

test('remove clears the value the form sends', () => {
  const component = articleImage();
  component.$el = {dataset: {value: '/material-images/1/abc.webp', preview: '/materials/1/image'}};
  component.init();
  assert.equal(component.value, '/material-images/1/abc.webp');
  component.clear();
  assert.equal(component.value, '');
  assert.equal(component.preview, '');
});
