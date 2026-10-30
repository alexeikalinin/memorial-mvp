import test from 'node:test';
import assert from 'node:assert/strict';
import { fullMemorialDate } from '../src/utils/memorialDates.js';
import { treeViewportStyle } from '../src/utils/familyTreeViewport.js';
test('full memorial calendar dates do not shift with timezone offsets',()=>{
 assert.equal(fullMemorialDate('1961-05-17T00:00:00+03:00'),'17.05.1961');
 assert.equal(fullMemorialDate('2019-10-21'),'21.10.2019');
 assert.equal(fullMemorialDate(null),null);
});
test('layout zoom preserves pan coordinates in rendered pixels, with legacy transform fallback',()=>{
 const result=treeViewportStyle({x:120,y:-90,scale:3},true,2);
 assert.equal(result.left*result.zoom,120);assert.equal(result.top*result.zoom,-90);assert.equal(result.transform,'none');
 assert.equal(treeViewportStyle({x:120,y:-90,scale:3},false).transform,'translate(120px, -90px) scale(3)');
});
