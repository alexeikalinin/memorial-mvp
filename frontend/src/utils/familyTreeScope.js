/**
 * familyTreeScope.js
 *
 * Data-driven family visibility for the tree.
 * Replaces the old hardcoded familyTreeKellyFilter.js / FAMILY_TREE_SCOPE constant.
 *
 * Logic:
 *  - Each node belongs to a "family" identified by its last surname token.
 *  - `visibleFamilies` is a state array the user controls (starts with one family).
 *  - Nodes in visibleFamilies → rendered as full cards.
 *  - Nodes NOT in visibleFamilies but connected (via non-custom edges) to a visible
 *    node → rendered as "stub" cards (blurred, lock icon, "Show family" button).
 *  - custom edges (historical/professional) are excluded from the layout entirely —
 *    they don't create stubs and are not drawn as connectors.
 */

import { surnameOf } from './familyTreeGenerationLayout.js'

// ── Known families for the demo dataset ──────────────────────────────────────
// Add more here as new demo/production families appear.
// `color` is used for the unlock button accent.
export const FAMILY_CONFIG = {
  Kelly:    { color: '#c8a97e', labelEn: 'Kelly',    labelRu: 'Келли' },
  Anderson: { color: '#7eb5c8', labelEn: 'Anderson', labelRu: 'Андерсон' },
  Chang:    { color: '#c87e7e', labelEn: 'Chang',    labelRu: 'Чанг' },
  Rossi:    { color: '#7ec896', labelEn: 'Rossi',    labelRu: 'Росси' },
}

/**
 * Returns the family name for a node based on its last surname token.
 * Returns 'Other' for surnames not in FAMILY_CONFIG.
 */
export function getFamilyOfNode(node) {
  const surname = surnameOf(node.name || '')
  return FAMILY_CONFIG[surname] ? surname : 'Other'
}

/**
 * Filter the full-tree API graph to only the families in `visibleFamilies`.
 *
 * Returns an augmented graph object:
 *   - `nodes`: visible full nodes + stub nodes (with `_stub: true`, `_family: string`)
 *   - `edges`: only edges between visible+stub nodes (no custom edges)
 *   - `_lockedFamilies`: array of known family names present in the full graph
 *       but NOT currently visible — used to render "Show X family" unlock buttons
 *   - `_visibleFamilies`: mirror of the input array
 *
 * @param {{ nodes: Array, edges: Array, root_id: number }} graph  Full API graph
 * @param {string[]} visibleFamilies  e.g. ['Kelly'] or ['Kelly', 'Anderson']
 */
export function filterGraphToScope(graph, visibleFamilies) {
  if (!graph?.nodes?.length) return graph


  // Real families need no demo surname registration. Reveal the root's immediate
  // relatives first; a boundary card explicitly opens another relationship branch.
  const root = graph.nodes.find(n => String(n.memorial_id) === String(graph.root_id))
  if (root && getFamilyOfNode(root) === 'Other') {
    const nodeIds = new Set(graph.nodes.map(n => String(n.memorial_id)))
    const adjacent = new Map([...nodeIds].map(id => [id, new Set()]))
    const familyEdges = graph.edges.filter(e => String(e.type).toLowerCase() !== 'custom')
    for (const e of familyEdges) {
      const source = String(e.source), target = String(e.target)
      if (!nodeIds.has(source) || !nodeIds.has(target)) continue
      adjacent.get(source).add(target); adjacent.get(target).add(source)
    }
    const opened = [String(graph.root_id), ...visibleFamilies.filter(v => v.startsWith('node:')).map(v => v.slice(5))]
    const fullIds = new Set()
    for (const id of opened) {
      if (!nodeIds.has(id)) continue
      fullIds.add(id)
      for (const neighbor of adjacent.get(id)) fullIds.add(neighbor)
    }
    const boundary = new Set()
    for (const id of fullIds) for (const neighbor of adjacent.get(id)) {
      if (!fullIds.has(neighbor)) boundary.add(neighbor)
    }
    const displayed = new Set([...fullIds, ...boundary])
    return {
      ...graph,
      nodes: graph.nodes.filter(n => displayed.has(String(n.memorial_id))).map(n => ({
        ...n, _stub: boundary.has(String(n.memorial_id)), _family: `node:${n.memorial_id}`,
      })),
      edges: familyEdges.filter(e => displayed.has(String(e.source)) && displayed.has(String(e.target))),
      _lockedFamilies: [], _visibleFamilies: [...visibleFamilies], _branchScope: true,
    }
  }

  const visible = new Set(visibleFamilies)

  // ── Classify all nodes ──────────────────────────────────────────────────────
  const allKnownFamilies = new Set()
  const visibleIds = new Set()

  for (const node of graph.nodes) {
    const fam = getFamilyOfNode(node)
    if (FAMILY_CONFIG[fam]) allKnownFamilies.add(fam)
    if (visible.has(fam)) visibleIds.add(String(node.memorial_id))
  }

  // ── Find stub nodes ─────────────────────────────────────────────────────────
  // A stub is: not in a visible family, but directly connected (non-custom edge)
  // to at least one visible node.
  const stubIds = new Set()
  for (const edge of graph.edges) {
    if (String(edge.type).toLowerCase() === 'custom') continue
    const s = String(edge.source)
    const t = String(edge.target)
    if (visibleIds.has(s) && !visibleIds.has(t)) stubIds.add(t)
    if (visibleIds.has(t) && !visibleIds.has(s)) stubIds.add(s)
  }

  const allIds = new Set([...visibleIds, ...stubIds])

  // ── Build output nodes ──────────────────────────────────────────────────────
  const outputNodes = graph.nodes
    .filter(n => allIds.has(String(n.memorial_id)))
    .map(n => ({
      ...n,
      _stub: stubIds.has(String(n.memorial_id)),
      _family: getFamilyOfNode(n),
    }))

  // ── Build output edges ──────────────────────────────────────────────────────
  // Exclude custom edges entirely. Only keep edges where both endpoints are in scope.
  const outputEdges = graph.edges.filter(e => {
    if (String(e.type).toLowerCase() === 'custom') return false
    return allIds.has(String(e.source)) && allIds.has(String(e.target))
  })

  // ── Locked families ─────────────────────────────────────────────────────────
  // Known families that exist in the full graph but are not yet visible.
  const lockedFamilies = [...allKnownFamilies].filter(f => !visible.has(f))

  return {
    ...graph,
    nodes: outputNodes,
    edges: outputEdges,
    _visibleFamilies: [...visible],
    _lockedFamilies: lockedFamilies,
  }
}
