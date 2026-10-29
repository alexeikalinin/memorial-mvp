import test from 'node:test'
import assert from 'node:assert/strict'
import { buildGenerationLayout } from '../src/utils/familyTreeGenerationLayout.js'
import { resolveTreePositions } from '../src/utils/familyTreePositions.js'
import { buildOrthogonalConnectors } from '../src/utils/familyTreeOrthogonalConnectors.js'

const graph = { root_id: 1, _branchScope: true, nodes: [
  { memorial_id: 1, name: 'Калинин Николай', birth_year: 1956 },
  { memorial_id: 2, name: 'Калинина Светлана', birth_year: 1961 },
  { memorial_id: 3, name: 'Калинин Виктор Иванович', birth_year: 1950 },
  { memorial_id: 4, name: 'Калинин Евгений Иванович', birth_year: 1958 },
  { memorial_id: 5, name: 'Сачко Александр', birth_year: 1930, _stub: true },
], edges: [{ source: 1, target: 2, type: 'spouse' }, { source: 1, target: 3, type: 'sibling' }, { source: 1, target: 4, type: 'sibling' }, { source: 2, target: 5, type: 'parent' }] }

test('brothers and spouse share a row with disjoint cards; boundary parent is above', () => {
  const layout = buildGenerationLayout(graph, true)
  const p = layout.positions
  assert.equal(new Set([1, 2, 3, 4].map(id => p[id].y)).size, 1)
  assert.ok(p[5].y < p[2].y)
  const row = [1, 2, 3, 4].map(id => p[id]).sort((a,b) => a.x-b.x)
  for (let i=1;i<row.length;i++) assert.ok(row[i].x-row[i-1].x >= layout.nodeSize.w+20)
})
test('new people, overlapping legacy coordinates and invalid coordinates restore automatic placement', () => {
  const layout = buildGenerationLayout(graph, true)
  assert.equal(resolveTreePositions(layout, { 1: {x: 1, y: 1} }), layout.positions)
  const overlaps = Object.fromEntries(Object.keys(layout.positions).map(id => [id, {x: 1,y: 1}]))
  assert.equal(resolveTreePositions(layout, overlaps), layout.positions)
  const valid = Object.fromEntries(Object.entries(layout.positions).map(([id,p])=>[id,{x:p.x+10,y:p.y+10}]))
  assert.equal(resolveTreePositions(layout, valid)[1].x, layout.positions[1].x+10)
  valid[1].x = NaN
  assert.equal(resolveTreePositions(layout, valid), layout.positions)
})
test('sibling bracket terminates on both cards at different heights', () => {
  const positions = { 1: {x:0,y:80,cx:45,cy:154}, 2: {x:200,y:260,cx:245,cy:334} }
  const {lines} = buildOrthogonalConnectors({positions, nodeSize:{w:90,h:148},nodes:[],edges:[{source:1,target:2,type:'sibling'}]})
  for (const p of Object.values(positions)) assert.ok(lines.some(l => (l.x1===p.cx && l.y1===p.y)||(l.x2===p.cx && l.y2===p.y)))
})

test('each partner has their own siblings on the outside of the couple', () => {
  const family = {...graph, nodes: graph.nodes.map(n => n.memorial_id === 5 ? {...n, name:'Сачко Лариса Михайловна', birth_year:1962, _stub:false} : n), edges: [...graph.edges.slice(0,3), {source:2,target:5,type:'sibling'}]}
  for (const root of [1,2]) {
    const layout = buildGenerationLayout({...family,root_id:root}, true)
    const p = layout.positions
    assert.equal(new Set(Object.values(p).map(n=>n.y)).size,1)
    const left = p[1].x < p[2].x ? 1 : 2
    if (left === 1) { assert.ok(p[3].x < p[1].x && p[4].x < p[1].x); assert.ok(p[5].x > p[2].x) }
    else { assert.ok(p[5].x < p[2].x); assert.ok(p[3].x > p[1].x && p[4].x > p[1].x) }
    assert.ok(![3,4,5].some(id => p[id].x > Math.min(p[1].x,p[2].x) && p[id].x < Math.max(p[1].x,p[2].x)))
  }
})

test('explicit version-two manual placement preserves diagonal movement and reload',()=>{
 const layout=buildGenerationLayout(graph,true)
 const saved=Object.fromEntries(Object.entries(layout.positions).map(([id,p])=>[id,{x:p.x,y:p.y}]))
 saved[1]={x:saved[1].x+37,y:saved[1].y+53}
 const result=resolveTreePositions(layout,saved,true)
 assert.equal(result[1].x,saved[1].x);assert.equal(result[1].y,saved[1].y)
 assert.equal(resolveTreePositions(layout,{...saved,1:{x:Infinity,y:1}},true),layout.positions)
})

test('adding an undated father keeps both daughters, their spouses and brothers on one row', () => {
 const nodes=[
  {memorial_id:1,name:'Николай',birth_year:1956},
  {memorial_id:2,name:'Светлана',birth_year:1961},
  {memorial_id:3,name:'Виктор'}, {memorial_id:4,name:'Евгений'},
  {memorial_id:5,name:'Лариса',birth_year:1962},
  {memorial_id:6,name:'Михаил'}, {memorial_id:7,name:'Александр',birth_year:1962},
 ]
 const edges=[{source:1,target:2,type:'spouse'},{source:1,target:3,type:'sibling'},{source:1,target:4,type:'sibling'},{source:2,target:5,type:'sibling'},{source:5,target:7,type:'spouse'},{source:2,target:6,type:'parent'},{source:5,target:6,type:'parent'}]
 for(const root of [1,2,5,6])for(const reversed of [false,true]){
  const graph={root_id:root,_branchScope:true,nodes,edges:reversed?edges.map(e=>e.type==='parent'?{source:e.target,target:e.source,type:'child'}:e):edges}
  const p=buildGenerationLayout(graph,true).positions
  assert.equal(new Set([1,2,3,4,5,7].map(id=>p[id].y)).size,1)
  assert.ok(p[6].y<p[2].y)
 }
})

test('two undated parents are adjacent, centered over daughters and stable across input order',()=>{
 const nodes=[{memorial_id:1,name:'Бахар Михаил'},{memorial_id:2,name:'Бахар Инна'},{memorial_id:3,name:'Калинина Светлана',birth_year:1961},{memorial_id:4,name:'Сачко Лариса',birth_year:1962},{memorial_id:5,name:'Калинин Николай Иванович',birth_year:1956},{memorial_id:6,name:'Сачко Александр Антонович'}]
 const edges=[{source:3,target:1,type:'parent'},{source:4,target:1,type:'parent'},{source:3,target:2,type:'parent'},{source:4,target:2,type:'parent'},{source:3,target:5,type:'spouse'},{source:4,target:6,type:'spouse'}]
 for(const e of [edges,[...edges,{source:1,target:2,type:'spouse'}]]){
  const p=buildGenerationLayout({root_id:3,_branchScope:true,nodes,edges:e},true).positions
  assert.equal(p[1].y,p[2].y);assert.ok(p[1].y<p[3].y);assert.equal(new Set([3,4,5,6].map(id=>p[id].y)).size,1)
  assert.equal(Math.abs(p[1].x-p[2].x),130)
  assert.equal(Math.abs(p[3].x-p[4].x),130)
  assert.ok(Math.abs((p[1].cx+p[2].cx)/2-(p[3].cx+p[4].cx)/2)<1)
  for(const pair of [[3,5],[4,6]])assert.equal(Math.abs(p[pair[0]].x-p[pair[1]].x),130)
 }
})
