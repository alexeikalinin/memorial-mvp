const idOf = value => String(value)

export function getSelectedFamilyNode(graph, selectedId, fallbackId = graph?.root_id) {
  return graph?.nodes?.find(node => selectedId != null && idOf(node.memorial_id) === idOf(selectedId))
    || graph?.nodes?.find(node => idOf(node.memorial_id) === idOf(fallbackId))
    || null
}

export function getSelectedFamilyRelations(graph, sourceId) {
  const reverse = { parent: 'child', child: 'parent', adoptive_parent: 'adoptive_child', adoptive_child: 'adoptive_parent', step_parent: 'step_child', step_child: 'step_parent' }
  const seen = new Set()
  return (graph?.edges || []).flatMap(edge => {
    const type = String(edge.type || '').toLowerCase()
    let other, relation
    if (idOf(edge.source) === idOf(sourceId)) { other = edge.target; relation = type }
    else if (idOf(edge.target) === idOf(sourceId)) { other = edge.source; relation = reverse[type] || type }
    else return []
    const key = `${other}:${relation}`
    if (seen.has(key)) return []
    seen.add(key)
    const node = graph?.nodes?.find(node => idOf(node.memorial_id) === idOf(other))
    return node ? [{ node, type: relation, label: edge.label }] : []
  })
}
