/**
 * Фильтрация графа full-tree для демо: Kelly / Kelly+Anderson / полный граф.
 */

import { surnameOf } from './familyTreeGenerationLayout.js'

const sid = (id) => String(id)

/**
 * - `kelly` — только фамилия Kelly (фаза 1).
 * - `kelly_anderson` — Kelly + Anderson по последнему слову имени (без Chang, Rossi и др.).
 * - `kelly_anderson_third` — Kelly + Anderson + 3-я фамилия (самая частая среди остальных).
 * - `kelly_anderson_four` — Kelly + Anderson + Chang + Rossi (если обе есть в графе; иначе — топ по частоте).
 * - `full` — весь ответ API (все связанные семьи).
 */
export const FAMILY_TREE_SCOPE = 'kelly_anderson_four'

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

function topExtraSurnames(nodes, limit = 1) {
  const counts = {}
  for (const n of nodes || []) {
    const s = surnameOf(n.name)
    if (!s || s === 'Kelly' || s === 'Anderson') continue
    counts[s] = (counts[s] || 0) + 1
  }
  const ordered = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
  return ordered.slice(0, limit).map(([s]) => s)
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

export function filterGraphToThreeFamilies(graphData) {
  if (!graphData?.nodes?.length) return graphData
  const third = topExtraSurnames(graphData.nodes, 1)[0]
  const allowed = new Set(['Kelly', 'Anderson'])
  if (third) allowed.add(third)
  const nodes = graphData.nodes.filter((n) => allowed.has(surnameOf(n.name)))
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

export function filterGraphToFourFamilies(graphData) {
  if (!graphData?.nodes?.length) return graphData
  const allNodes = graphData.nodes
  const hasChang = allNodes.some((n) => surnameOf(n.name) === 'Chang')
  const hasRossi = allNodes.some((n) => surnameOf(n.name) === 'Rossi')
  const extras =
    hasChang && hasRossi ? ['Chang', 'Rossi'] : topExtraSurnames(allNodes, 2)
  const allowed = new Set(['Kelly', 'Anderson', ...extras])
  const nodes = allNodes.filter((n) => allowed.has(surnameOf(n.name)))
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
