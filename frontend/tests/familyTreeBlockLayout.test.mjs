import test from 'node:test'
import assert from 'node:assert/strict'
import {buildGenerationLayout} from '../src/utils/familyTreeGenerationLayout.js'
import {buildOrthogonalConnectors} from '../src/utils/familyTreeOrthogonalConnectors.js'

// Anonymous topology: two ancestral families, married siblings, twelve unions,
// two former marriages and five separate sets of grandchildren.
const nodes=Array.from({length:28},(_,i)=>({memorial_id:i+318,name:`Person ${i+318}`}))
const couples=[[318,323,'spouse'],[319,320,'spouse'],[321,328,'spouse'],[322,333,'spouse'],[324,325,'spouse'],[326,327,'spouse'],[329,330,'spouse'],[331,332,'spouse'],[334,335,'spouse'],[334,336,'ex_spouse'],[341,345,'spouse'],[342,343,'ex_spouse']]
const parents={319:[324,325],320:[326,327],321:[326,327],322:[326,327],323:[324,325],329:[321,328],331:[321,328],334:[322,333],337:[334,336],338:[334,335],339:[329,330],340:[331,332],341:[320,319],342:[319,320],344:[342,343]}
const edges=[...couples.map(([source,target,type])=>({source,target,type})),...Object.entries(parents).flatMap(([source,ps])=>ps.map(target=>({source:Number(source),target,type:'parent'}))),...[[319,323],[320,321],[320,322],[321,322],[329,331],[341,342]].map(([source,target])=>({source,target,type:'sibling'}))]
const between=(x,a,b)=>x>Math.min(a,b)+.1&&x<Math.max(a,b)-.1

function verify(graph) {
 const layout=buildGenerationLayout(graph,true),p=layout.positions
 assert.equal(Object.keys(p).length,28)
 for(const [a,b] of couples) assert.equal(Math.abs(p[a].x-p[b].x),130,`partners ${a}/${b} must be adjacent`)
 // Each child of a separate union is under that union, including two marriages.
 for(const [child,a,b] of [[337,334,336],[338,334,335],[339,329,330],[340,331,332],[344,342,343]])assert.equal(p[child].cx,(p[a].cx+p[b].cx)/2)
 assert.ok(p[323].x<p[319].x&&p[319].x<p[320].x)
 assert.ok(p[322].x>p[320].x&&p[321].x>p[320].x)
 const {lines}=buildOrthogonalConnectors({edges:graph.edges,nodes:graph.nodes,positions:p,nodeSize:layout.nodeSize})
 for(const line of lines)for(const [id,card] of Object.entries(p)){
  // A marriage bar intentionally touches its own two avatar borders by 1.2px.
  if(line.familyKey.split(':').slice(1).includes(id))continue
  if(line.x1===line.x2)assert.ok(!(between(line.x1,card.x,card.x+90)&&Math.max(line.y1,line.y2)>card.y+.1&&Math.min(line.y1,line.y2)<card.y+180-.1),`${line.familyKey} crosses card ${id}`)
  if(line.y1===line.y2)assert.ok(!(between(line.y1,card.y,card.y+180)&&Math.max(line.x1,line.x2)>card.x+.1&&Math.min(line.x1,line.x2)<card.x+90-.1),`${line.familyKey} crosses card ${id}`)
 }
 for(let i=0;i<lines.length;i++)for(let j=i+1;j<lines.length;j++){
  let h=lines[i],v=lines[j]
  if(h.familyKey===v.familyKey)continue
  if(h.x1===h.x2)[h,v]=[v,h]
  if(h.y1!==h.y2||v.x1!==v.x2)continue
  assert.ok(!(between(v.x1,h.x1,h.x2)&&between(h.y1,v.y1,v.y2)),`${h.familyKey} crosses ${v.familyKey}`)
 }
}

test('28-person expanded family reserves descendant space without crossing cards or family lines',()=>verify({root_id:319,_branchScope:true,nodes,edges}))
test('inverse records, shuffled input and selection preserve separate descendant branches',()=>{
 const reverse={parent:'child',child:'parent'}
 for(const root_id of [319,320,334,341])verify({root_id,_branchScope:true,nodes:[...nodes].reverse(),edges:[...edges].reverse().map(e=>({source:e.target,target:e.source,type:reverse[e.type]||e.type}))})
})

test('300 people retain distinct cards and complete descendant families',()=>{
 const people=[{memorial_id:1,name:'Person 1'},{memorial_id:2,name:'Person 2'}]
 const relations=[{source:1,target:2,type:'spouse'}],queue=[[1,2]]
 let next=3
 while(people.length<300){const [a,b]=queue.shift();for(let i=0;i<3&&people.length<300;i++){
  const child=next++,partner=next++
  people.push({memorial_id:child,name:`Person ${child}`},{memorial_id:partner,name:`Person ${partner}`})
  relations.push({source:child,target:partner,type:'spouse'},{source:child,target:a,type:'parent'},{source:child,target:b,type:'parent'})
  queue.push([child,partner])
 }}
 const layout=buildGenerationLayout({root_id:1,_branchScope:true,nodes:people,edges:relations},true)
 assert.equal(Object.keys(layout.positions).length,300)
 const rows=new Map()
 for(const p of Object.values(layout.positions)){assert.ok(Number.isFinite(p.x)&&Number.isFinite(p.y));if(!rows.has(p.y))rows.set(p.y,[]);rows.get(p.y).push(p)}
 for(const row of rows.values()){row.sort((a,b)=>a.x-b.x);for(let i=1;i<row.length;i++)assert.ok(row[i].x-row[i-1].x>=130)}
})
