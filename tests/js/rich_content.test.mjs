import test from 'node:test';
import assert from 'node:assert/strict';
import {imageURL, remoteImageURL} from '../../app/static/src/js/rich-content.js';

test('description image URLs allow external links and legacy uploads, reject unsafe sources', () => {
  for (const url of ['https://example.com/image?id=1&size=large', 'http://example.com/image.png']) {
    assert.equal(remoteImageURL(url),true);
    assert.equal(imageURL(url),true);
  }
  assert.equal(imageURL('data:image/png;base64,AAAA'),true);
  assert.equal(imageURL('/material-images/1/'+'a'.repeat(32)+'.webp'),true);
  assert.equal(imageURL('/material-images/1/../../secret.webp'),false);
  for (const url of ['javascript:alert(1)', '//example.com/a.png', 'file:///tmp/a.png',
    'https://user:pass@example.com/a.png', 'https://', 'https://example.com/white space.png',
    'data:image/svg+xml;base64,PHN2Zz4=', 'https://example.com\\@other.com']) {
    assert.equal(imageURL(url),false,url);
  }
});
