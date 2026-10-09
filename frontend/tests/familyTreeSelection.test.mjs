import test from 'node:test'
import assert from 'node:assert/strict'
import { getSelectedFamilyNode, getSelectedFamilyRelations } from '../src/utils/familyTreeSelection.js'
const graph = { root_id: 1, nodes: [1, 2, 3].map(id => ({ memorial_id: id, name: `Person ${id}` })), edges: [{ source: 1, target: 2, type: 'PARENT' }, { source: 2, target: 1, type: 'child' }, { source: 1, target: 3, type: 'spouse' }] }
test('parent direction and duplicate inverse records are resolved relative to selection', () => {
  assert.deepEqual(getSelectedFamilyRelations(graph, 1).map(r => [r.node.memorial_id, r.type]), [[2, 'parent'], [3, 'spouse']])
  assert.deepEqual(getSelectedFamilyRelations(graph, 2).map(r => [r.node.memorial_id, r.type]), [[1, 'child']])
})
test('newly selected person replaces root and stale or missing person falls back to current root', () => {
  assert.equal(getSelectedFamilyNode(graph, '2').memorial_id, 2)
  assert.equal(getSelectedFamilyNode(graph, 99).memorial_id, 1)
  assert.equal(getSelectedFamilyNode({ ...graph, root_id: 3 }, 99).memorial_id, 3)
})
test('unloaded and empty graphs safely have no node or selected relationships', () => {
  assert.equal(getSelectedFamilyNode(null, 1), null)
  assert.equal(getSelectedFamilyNode({ nodes: [], edges: [] }, 1), null)
  assert.deepEqual(getSelectedFamilyRelations(null, 1), [])
})
test('incoming adoptive parent edge yields child relationship; orphan targets are hidden', () => {
  const result = getSelectedFamilyRelations({ ...graph, edges: [{ source: 2, target: 1, type: 'adoptive_parent' }, { source: 1, target: 99, type: 'child' }] }, 1)
  assert.deepEqual(result.map(r => [r.node.memorial_id, r.type]), [[2, 'adoptive_child']])
})
