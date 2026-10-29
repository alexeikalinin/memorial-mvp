const sid = String

// Couples are indivisible blocks. Blood relatives attach to the outside of the
// appropriate partner, including relatives whose own partners have children.
export function orderFamilyRow(units, edges, rootId, positions = {}) {
  const ids = units.flatMap(u => u.ids).map(sid)
  const present = new Set(ids)
  const owner = new Map()
  const roots = new Map(ids.map(id => [id,id]))
  const find = id => roots.get(id) === id ? id : find(roots.get(id))
  for (const e of edges) if (['spouse','partner','ex_spouse'].includes(e.type) && present.has(sid(e.source)) && present.has(sid(e.target))) roots.set(find(sid(e.target)),find(sid(e.source)))
  const components = new Map()
  for (const id of ids) { const key=find(id); if(!components.has(key)) components.set(key,[]); components.get(key).push(id) }
  const blocks = [...components.values()]
  for (let i=0;i<blocks.length;i++) {
    const block=blocks[i]
    if(block.length===3){
      const degree=id=>edges.filter(e=>['spouse','partner','ex_spouse'].includes(e.type)&&((sid(e.source)===id&&block.includes(sid(e.target)))||(sid(e.target)===id&&block.includes(sid(e.source))))).length
      const center=[...block].sort((a,b)=>degree(b)-degree(a))[0]
      const partners=block.filter(id=>id!==center)
      const isEx=id=>edges.some(e=>e.type==='ex_spouse'&&[sid(e.source),sid(e.target)].includes(center)&&[sid(e.source),sid(e.target)].includes(id))
      partners.sort((a,b)=>Number(isEx(b))-Number(isEx(a)))
      blocks[i]=[partners[0],center,partners[1]]
    }
  }
  blocks.forEach((block, i) => block.forEach(id => owner.set(id, i)))
  const siblings = new Map(ids.map(id => [id, new Set()]))
  const link = (a, b) => {
    a = sid(a); b = sid(b)
    if (!present.has(a) || !present.has(b) || owner.get(a) === owner.get(b)) return
    siblings.get(a).add(b); siblings.get(b).add(a)
  }
  const children = new Map()
  for (const e of edges) {
    if (['sibling', 'half_sibling'].includes(e.type)) link(e.source, e.target)
    let parent, child
    if (e.type === 'parent') { parent = e.target; child = e.source }
    if (e.type === 'child') { parent = e.source; child = e.target }
    if (parent == null || !present.has(sid(child))) continue
    if (!children.has(sid(parent))) children.set(sid(parent), new Set())
    children.get(sid(parent)).add(sid(child))
  }
  for (const group of children.values()) {
    const list = [...group]
    for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) link(list[i], list[j])
  }
  const visited = new Set()
  const compare = (a, b) => a.localeCompare(b, undefined, { numeric: true })
  const walk = (index, anchor = null, direction = 1) => {
    if (visited.has(index)) return []
    visited.add(index)
    let block = [...blocks[index]]
    if (anchor != null && block.length === 2) {
      const other = block.find(id => id !== anchor)
      block = direction < 0 ? [other, anchor] : [anchor, other]
    }
    const relatives = (id, side) => [...siblings.get(id)].sort(compare).flatMap(next => walk(owner.get(next), next, side))
    if (block.length === 1) {
      const branch = relatives(block[0], direction)
      return direction < 0 ? [...branch, ...block] : [...block, ...branch]
    }
    const left = relatives(block[0], -1)
    const right = block.slice(1).flatMap(id => relatives(id, 1))
    return [...left, ...block, ...right]
  }
  // Start at the bridge joining the two largest sibling branches, independent
  // of API edge order. Use the selected root only to break equivalent choices.
  const ranked = blocks.map((block, index) => ({ index, score: block.length === 2 ? Math.min(...block.map(id => siblings.get(id).size)) * 100 + block.reduce((n,id) => n + siblings.get(id).size, 0) : -1 }))
    .sort((a,b) => b.score-a.score || Number(blocks[b.index].includes(sid(rootId)))-Number(blocks[a.index].includes(sid(rootId))) || compare(blocks[a.index][0],blocks[b.index][0]))
  const chunks = ranked.map(({index}) => walk(index)).filter(ids => ids.length)
  const parentCenter = ids => {
    const members = new Set(ids), parents = new Set()
    for (const e of edges) {
      if (e.type === 'parent' && members.has(sid(e.source)) && positions[e.target]) parents.add(sid(e.target))
      if (e.type === 'child' && members.has(sid(e.target)) && positions[e.source]) parents.add(sid(e.source))
    }
    return parents.size ? [...parents].reduce((n,id) => n+positions[id].cx,0)/parents.size : Infinity
  }
  chunks.sort((a,b) => parentCenter(a)-parentCenter(b))
  return chunks.flat()
}
