// Reserve the full width of each descendant family before placing its parents.
// A union joins partners (including former partners) without duplicating people.
export function arrangeFamilyBlocks(positions, edges, width=90, gap=40, minX=168) {
  const out=Object.fromEntries(Object.entries(positions).map(([id,p])=>[id,{...p}]))
  const ids=Object.keys(out), roots=new Map(ids.map(id=>[id,id]))
  const find=id=>roots.get(id)===id?id:find(roots.get(id))
  for(const e of edges) {
    const a=String(e.source),b=String(e.target)
    if(['spouse','partner','ex_spouse'].includes(e.type)&&out[a]&&out[b]&&out[a].y===out[b].y)roots.set(find(b),find(a))
  }
  const coParents=new Map()
  for(const e of edges){let p,c;if(['parent','adoptive_parent','step_parent'].includes(e.type)){p=String(e.target);c=String(e.source)}if(['child','adoptive_child','step_child'].includes(e.type)){p=String(e.source);c=String(e.target)}if(!out[p]||!out[c])continue;if(!coParents.has(c))coParents.set(c,[]);coParents.get(c).push(p)}
  for(const parents of coParents.values())for(const p of parents.slice(1))if(out[p].y===out[parents[0]].y)roots.set(find(p),find(parents[0]))
  const byRoot=new Map(),owner=new Map()
  for(const id of ids){const key=find(id);if(!byRoot.has(key))byRoot.set(key,{ids:[],children:new Set(),parents:new Set()});byRoot.get(key).ids.push(id);owner.set(id,byRoot.get(key))}
  const blocks=[...byRoot.values()],rows=new Map()
  for(const block of blocks){block.ids.sort((a,b)=>out[a].x-out[b].x);block.y=out[block.ids[0]].y;block.ownWidth=block.ids.length*width+(block.ids.length-1)*gap;if(!rows.has(block.y))rows.set(block.y,[]);rows.get(block.y).push(block)}
  for(const row of rows.values())row.sort((a,b)=>out[a.ids[0]].x-out[b.ids[0]].x)
  const parentEdges=new Map()
  for(const e of edges){let p,c;if(['parent','adoptive_parent','step_parent'].includes(e.type)){p=String(e.target);c=String(e.source)}if(['child','adoptive_child','step_child'].includes(e.type)){p=String(e.source);c=String(e.target)}if(!out[p]||!out[c]||out[p].y>=out[c].y)continue;const a=owner.get(p),b=owner.get(c);a.children.add(b);b.parents.add(a);parentEdges.set(`${p}:${c}`,{p,c})}
  const ys=[...rows.keys()].sort((a,b)=>a-b)
  for(const y of [...ys].reverse())for(const block of rows.get(y)) {
    const children=[...block.children]
    block.width=Math.max(block.ownWidth,children.reduce((n,c)=>n+c.width,0)+Math.max(0,children.length-1)*gap)
  }
  // At an ancestral merge, anchor the generation containing both partners;
  // each partner's ancestors can then sit above their own side of the family.
  const anchor=Math.max(ys[0],...blocks.filter(b=>b.parents.size>1).map(b=>b.y))
  const place=(block,start)=>{block.start=start;let x=start+(block.width-block.ownWidth)/2;for(const id of block.ids){out[id].x=x;out[id].cx=x+width/2;x+=width+gap}}
  let cursor=minX
  for(const block of rows.get(anchor)){place(block,cursor);cursor+=block.width+gap}
  for(const y of ys.filter(y=>y>anchor)){
    cursor=minX
    for(const block of rows.get(y)){
      const parent=[...block.parents].filter(p=>p.start!=null).sort((a,b)=>a.start-b.start)[0]
      let desired=cursor
      if(parent){const siblings=rows.get(y).filter(b=>b.parents.has(parent));const total=siblings.reduce((n,b)=>n+b.width,0)+(siblings.length-1)*gap;desired=parent.start+(parent.width-total)/2;for(const sibling of siblings){if(sibling===block)break;desired+=sibling.width+gap}}
      place(block,Math.max(cursor,desired));cursor=block.start+block.width+gap
    }
  }
  for(const y of ys.filter(y=>y<anchor).reverse()){
    cursor=minX
    for(const block of rows.get(y)){
      const childIds=[...new Set([...parentEdges.values()].filter(e=>owner.get(e.p)===block).map(e=>e.c))]
      const center=childIds.length?(Math.min(...childIds.map(id=>out[id].cx))+Math.max(...childIds.map(id=>out[id].cx)))/2:cursor+block.ownWidth/2
      // Ancestors occupy only their own cards; descendants already own their space.
      block.width=block.ownWidth
      place(block,Math.max(cursor,center-block.ownWidth/2));cursor=block.start+block.width+gap
    }
  }
  return out
}
