// Center parent groups above their children, moving each group as a block.
export function alignParentGroups(positions,edges,width=90,gap=40,minX=168){
 const out=Object.fromEntries(Object.entries(positions).map(([id,p])=>[id,{...p}]))
 const parents=new Map(),children=new Map()
 for(const e of edges){let p,c;const t=String(e.type).toLowerCase();if(['parent','adoptive_parent','step_parent'].includes(t)){p=String(e.target);c=String(e.source)}if(['child','adoptive_child','step_child'].includes(t)){p=String(e.source);c=String(e.target)}if(!p||!out[p]||!out[c])continue;if(!parents.has(c))parents.set(c,new Set());parents.get(c).add(p);if(!children.has(p))children.set(p,new Set());children.get(p).add(c)}
 const roots=new Map([...children.keys()].map(id=>[id,id]));const find=id=>roots.get(id)===id?id:find(roots.get(id));const union=(a,b)=>{if(roots.has(a)&&roots.has(b))roots.set(find(b),find(a))}
 for(const ids of parents.values()){const a=[...ids];for(const id of a.slice(1))if(out[a[0]].y===out[id].y)union(a[0],id)}
 for(const e of edges)if(['spouse','partner','ex_spouse'].includes(e.type)&&out[e.source]?.y===out[e.target]?.y)union(String(e.source),String(e.target))
 const groups=new Map();for(const id of roots.keys()){const key=find(id);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(id)}
 const rows=new Map()
 for(const ids of groups.values()){const y=out[ids[0]].y;if(!rows.has(y))rows.set(y,[]);rows.get(y).push(ids)}
 // Children are positioned first, then their ancestors.
 for(const [y,blocks] of [...rows].sort((a,b)=>b[0]-a[0])){
  const entries=blocks.map(ids=>{ids.sort((a,b)=>out[a].x-out[b].x);const kids=[...new Set(ids.flatMap(id=>[...children.get(id)]))];const center=kids.reduce((n,id)=>n+out[id].cx,0)/kids.length;return {ids,desired:center-(ids.length*width+(ids.length-1)*gap)/2}}).sort((a,b)=>a.desired-b.desired)
  let cursor=minX
  for(const {ids,desired} of entries){let x=Math.max(cursor,desired)
   // Respect other people on this row as well as other parent blocks.
   const others=Object.entries(out).filter(([id,p])=>p.y===y&&!roots.has(id)).map(([,p])=>p.x).sort((a,b)=>a-b)
   const blockWidth=ids.length*width+(ids.length-1)*gap
   for(const otherX of others)if(x<otherX+width+gap&&x+blockWidth+gap>otherX)x=otherX+width+gap
   ids.forEach((id,i)=>{out[id].x=x+i*(width+gap);out[id].cx=out[id].x+width/2});cursor=x+blockWidth+gap
  }
 }
 return out
}
