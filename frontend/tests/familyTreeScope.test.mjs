import test from 'node:test'
import assert from 'node:assert/strict'
import { filterGraphToScope } from '../src/utils/familyTreeScope.js'

const graph = {
  root_id: 1,
  nodes: [1, 2, 3, 4, 5].map(id => ({ memorial_id: id, name: `Person ${id}` })),
  edges: [{ source: 1, target: 2, type: 'parent' }, { source: 2, target: 3, type: 'parent' },
    { source: 3, target: 4, type: 'parent' }, { source: 1, target: 5, type: 'custom' }],
}

test('real family starts with root and direct relatives, and offers next branch explicitly', () => {
  const result = filterGraphToScope(graph, ['Other'])
  assert.deepEqual(result.nodes.filter(n => !n._stub).map(n => n.memorial_id), [1, 2])
  assert.deepEqual(result.nodes.filter(n => n._stub).map(n => n.memorial_id), [3])
  assert.equal(result.nodes.find(n => n.memorial_id === 3)._family, 'node:3')
  assert.ok(!result.nodes.some(n => n.memorial_id === 5))
})

test('opening a branch reveals its relatives without surname assumptions', () => {
  const result = filterGraphToScope(graph, ['Other', 'node:3'])
  assert.deepEqual(result.nodes.filter(n => !n._stub).map(n => n.memorial_id), [1, 2, 3, 4])
  assert.ok(!result.edges.some(e => e.type === 'custom'))
})

test('invalid expansion IDs and orphan graph edges cannot reveal unrelated people', () => {
  const result = filterGraphToScope({ ...graph, edges: [...graph.edges, { source: 1, target: 999, type: 'child' }] }, ['Other', 'node:999'])
  assert.deepEqual(result.nodes.map(n => n.memorial_id), [1, 2, 3])
})

test('existing demo family unlock behavior is preserved', () => {
  const demo = { root_id: 1, nodes: [{ memorial_id: 1, name: 'James Kelly' }, { memorial_id: 2, name: 'Emily Chang' }, { memorial_id: 3, name: 'David Chang' }], edges: [{ source: 1, target: 2, type: 'spouse' }, { source: 2, target: 3, type: 'parent' }] }
  assert.equal(filterGraphToScope(demo, ['Kelly']).nodes.find(n => n.memorial_id === 2)._stub, true)
  assert.ok(filterGraphToScope(demo, ['Kelly', 'Chang']).nodes.every(n => !n._stub))
})
