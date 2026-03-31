/**
 * Фильтрация графа full-tree для демо: Kelly / Kelly+Anderson / полный граф.
 */

import { surnameOf } from './familyTreeGenerationLayout.js'

const sid = (id) => String(id)

/**
 * - `kelly` — только фамилия Kelly (фаза 1).
 * - `kelly_anderson` — Kelly + Anderson по последнему слову имени (без Chang, Rossi и др.).
 * - `full` — весь ответ API (все связанные семьи).
 */
export const FAMILY_TREE_SCOPE = 'kelly_anderson'

/** Совместимость: true только при `FAMILY_TREE_SCOPE === 'kelly'`. */
export const FAMILY_TREE_KELLY_ONLY = FAMILY_TREE_SCOPE === 'kelly'

export function isKellyFamilyMember(name) {
  return surnameOf(name) === 'Kelly'
}

export function isAndersonFamilyMember(name) {
  return surnameOf(name) === 'Anderson'
}

export function isKellyOrAndersonMember(name) {
  return isKellyFamilyMember(name) || isAndersonFamilyMember(name)
}

function oldestMemorialId(nodes) {
  const sorted = [...nodes].sort((a, b) => {
    const ya = a.birth_year ?? 9999
    const yb = b.birth_year ?? 9999
    if (ya !== yb) return ya - yb
    return sid(a.memorial_id).localeCompare(sid(b.memorial_id))
  })
  return sorted[0].memorial_id
}

function pickRootInRestrictedSet(graphData, subsetNodes) {
  const ids = new Set(subsetNodes.map((n) => sid(n.memorial_id)))
  const orig = sid(graphData.root_id)
  if (ids.has(orig)) return graphData.root_id

  const adj = {}
  for (const e of graphData.edges || []) {
    const a = sid(e.source)
    const b = sid(e.target)
    if (!adj[a]) adj[a] = []
    if (!adj[b]) adj[b] = []
    adj[a].push(b)
    adj[b].push(a)
  }
  const q = [orig]
  const seen = new Set([orig])
  while (q.length) {
    const cur = q.shift()
    if (ids.has(cur)) {
      const hit = subsetNodes.find((n) => sid(n.memorial_id) === cur)
      if (hit) return hit.memorial_id
    }
    for (const nb of adj[cur] || []) {
      if (!seen.has(nb)) {
        seen.add(nb)
        q.push(nb)
      }
    }
  }
  return oldestMemorialId(subsetNodes)
}

/**
 * Узлы с фамилией Kelly, рёбра только между ними; root_id — открытый мемориал, если он Kelly,
 * иначе ближайший Kelly по BFS от root в полном графе, иначе самый старший по году рождения.
 */
export function filterGraphToKellyFamily(graphData) {
  if (!graphData?.nodes?.length) return graphData
  const kellyNodes = graphData.nodes.filter((n) => isKellyFamilyMember(n.name))
  if (!kellyNodes.length) return graphData
  const idSet = new Set(kellyNodes.map((n) => sid(n.memorial_id)))
  const kellyEdges = graphData.edges.filter(
    (e) => idSet.has(sid(e.source)) && idSet.has(sid(e.target))
  )
  const root_id = pickRootInRestrictedSet(graphData, kellyNodes)
  return {
    ...graphData,
    nodes: kellyNodes,
    edges: kellyEdges,
    root_id,
  }
}

/**
 * Kelly + Anderson (последнее слово в имени). Мосты (напр. … Anderson Kelly) остаются в линии Kelly.
 */
export function filterGraphToKellyAndAndersonFamily(graphData) {
  if (!graphData?.nodes?.length) return graphData
  const nodes = graphData.nodes.filter((n) => isKellyOrAndersonMember(n.name))
  if (!nodes.length) return graphData
  const idSet = new Set(nodes.map((n) => sid(n.memorial_id)))
  const edges = graphData.edges.filter(
    (e) => idSet.has(sid(e.source)) && idSet.has(sid(e.target))
  )
  const root_id = pickRootInRestrictedSet(graphData, nodes)
  return {
    ...graphData,
    nodes,
    edges,
    root_id,
  }
}
