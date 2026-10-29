// Generation rows follow family relationships, never birth-year ordering.
export function relationshipDepth(nodes, edges) {
 const ids=nodes.map(n=>String(n.memorial_id)), parent=new Map(ids.map(id=>[id,id]))
 const find=id=>{let root=id;while(parent.get(root)!==root)root=parent.get(root);return root}
 const union=(a,b)=>{if(parent.has(a)&&parent.has(b))parent.set(find(b),find(a))}
 const ancestors=[], children=new Map(), parents=new Map()
 for(const e of edges){const a=String(e.source),b=String(e.target);if(!parent.has(a)||!parent.has(b))continue
  if(['spouse','partner','ex_spouse','sibling','half_sibling'].includes(e.type))union(a,b)
  let child,p
  if(['parent','adoptive_parent','step_parent'].includes(e.type)){child=a;p=b}
  if(['child','adoptive_child','step_child'].includes(e.type)){child=b;p=a}
  if(!p)continue
  ancestors.push([p,child]);if(!children.has(p))children.set(p,[]);children.get(p).push(child)
  if(!parents.has(child))parents.set(child,[]);parents.get(child).push(p)
 }
 for(const list of [...children.values(),...parents.values()])for(const id of list.slice(1))union(list[0],id)
 const adj=new Map(ids.map(id=>[find(id),[]]))
 for(const [p,c] of ancestors){const a=find(p),b=find(c);if(a===b)continue;adj.get(a).push([b,1]);adj.get(b).push([a,-1])}
 const levels=new Map()
 for(const root of adj.keys()){if(levels.has(root))continue;levels.set(root,0);const queue=[root];for(let i=0;i<queue.length;i++)for(const [next,delta]of adj.get(queue[i]))if(!levels.has(next)){levels.set(next,levels.get(queue[i])+delta);queue.push(next)}}
 const min=Math.min(...levels.values())
 return Object.fromEntries(ids.map(id=>[id,levels.get(find(id))-min]))
}
