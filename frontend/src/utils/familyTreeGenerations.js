/**
 * Согласование поля generation для full-tree: дети всегда на один «этаж» ниже родителей,
 * супруги/братья на одном уровне. Дублирует логику backend после BFS (устаревший кэш API).
 */

const sid = (id) => String(id)

const PARENT_TYPES = new Set(['parent', 'adoptive_parent', 'step_parent'])
const CHILD_TYPES = new Set(['child', 'adoptive_child', 'step_child'])
const SAME_GEN_TYPES = new Set(['spouse', 'partner', 'ex_spouse', 'sibling', 'half_sibling'])
/** Рёбра «супруги» — для пересечения детей обоих родителей (полные сиблинги в один ряд). */
const SPOUSE_PAIR_TYPES = new Set(['spouse', 'partner', 'ex_spouse'])

function normType(t) {
  return String(t || '').toLowerCase()
}

/** Одно число поколения для ключа byGen / genToMinY (без рассинхрона 5 vs 5.0). */
export function normalizeGenerationValue(g) {
  const n = Number(g)
  return Number.isFinite(n) ? Math.round(n * 1000) / 1000 : 0
}

function buildParentsOf(edges, nodeIds) {
  const parentsOf = {}
  for (const e of edges || []) {
    const s = sid(e.source)
    const t = sid(e.target)
    if (!nodeIds.has(s) || !nodeIds.has(t)) continue
    const typ = normType(e.type)
    if (!typ) continue
    if (PARENT_TYPES.has(typ)) {
      if (!parentsOf[s]) parentsOf[s] = []
      parentsOf[s].push(t)
    } else if (CHILD_TYPES.has(typ)) {
      if (!parentsOf[t]) parentsOf[t] = []
      parentsOf[t].push(s)
    }
  }
  for (const k of Object.keys(parentsOf)) {
    parentsOf[k] = [...new Set(parentsOf[k])]
  }
  return parentsOf
}

function buildSameGenPairs(edges, nodeIds, includeCustom = false) {
  const pairs = []
  const seen = new Set()
  for (const e of edges || []) {
    const a = sid(e.source)
    const b = sid(e.target)
    if (!nodeIds.has(a) || !nodeIds.has(b)) continue
    const typ = normType(e.type)
    if (!SAME_GEN_TYPES.has(typ) && !(includeCustom && typ === 'custom')) continue
    const key = a < b ? `${a}|${b}` : `${b}|${a}`
    if (seen.has(key)) continue
    seen.add(key)
    pairs.push([a, b])
  }
  return pairs
}

/** Полные сиблинги: одинаковый набор из ≥2 родителей в parentsOf (без ребра sibling в графе). */
function inferFullSiblingPairsFromParents(parentsOf) {
  const byKey = new Map()
  for (const child of Object.keys(parentsOf)) {
    const plist = [...(parentsOf[child] || [])].sort()
    if (plist.length < 2) continue
    const k = plist.join('|')
    if (!byKey.has(k)) byKey.set(k, [])
    byKey.get(k).push(child)
  }
  const pairs = []
  const seen = new Set()
  for (const group of byKey.values()) {
    if (group.length < 2) continue
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        const a = group[i]
        const b = group[j]
        const key = a < b ? `${a}|${b}` : `${b}|${a}`
        if (seen.has(key)) continue
        seen.add(key)
        pairs.push([a, b])
      }
    }
  }
  return pairs
}

function mergeSameGenPairs(edgePairs, inferred) {
  const seen = new Set()
  const out = []
  for (const pair of [...edgePairs, ...inferred]) {
    const key = pair[0] < pair[1] ? `${pair[0]}|${pair[1]}` : `${pair[1]}|${pair[0]}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push(pair)
  }
  return out
}

/**
 * Перенумеровать ряды: индекс 0 = ряд с самым ранним min(birth_year) среди участников,
 * далее 1, 2… (старшие поколения сверху). Затем снова выровнять родитель→ребёнок и пары одного поколения.
 */
function remapDepthRowsOldestFirst(depth, nodeIds, parentsOf, samePairs, nodeById) {
  const byLevel = new Map()
  for (const id of nodeIds) {
    const d = depth[id]
    if (d === undefined) continue
    if (!byLevel.has(d)) byLevel.set(d, [])
    byLevel.get(d).push(id)
  }
  const levels = [...byLevel.keys()]
  const out = {}
  if (levels.length === 0) {
    return { ...depth }
  }

  const minBirth = (k) => {
    let m = Infinity
    for (const id of byLevel.get(k) || []) {
      const y = nodeById.get(id)?.birth_year
      if (y != null && Number.isFinite(Number(y))) m = Math.min(m, Number(y))
    }
    return Number.isFinite(m) ? m : 9999
  }

  const sortedLevels = [...levels].sort((ka, kb) => {
    const ya = minBirth(ka)
    const yb = minBirth(kb)
    if (ya !== yb) return ya - yb
    return ka - kb
  })

  const oldToNew = new Map()
  sortedLevels.forEach((oldK, i) => oldToNew.set(oldK, i))

  for (const id of nodeIds) {
    if (depth[id] === undefined) continue
    out[id] = oldToNew.get(depth[id])
  }

  const maxIter = Math.max(200, nodeIds.size * 10)
  for (let it = 0; it < maxIter; it++) {
    let changed = false
    for (const child of Object.keys(parentsOf)) {
      if (out[child] === undefined) continue
      const plist = parentsOf[child]
      if (!plist?.length) continue
      const pd = plist.map((p) => out[p]).filter((d) => d !== undefined)
      if (pd.length !== plist.length) continue
      const need = Math.max(...pd) + 1
      if (out[child] < need) {
        out[child] = need
        changed = true
      }
    }
    for (const [a, b] of samePairs) {
      if (out[a] === undefined || out[b] === undefined) continue
      const m = Math.min(out[a], out[b])
      if (out[a] !== m || out[b] !== m) {
        out[a] = out[b] = m
        changed = true
      }
    }
    if (!changed) break
  }

  for (const id of nodeIds) {
    if (out[id] === undefined && depth[id] !== undefined) out[id] = depth[id]
  }
  return out
}

/** Для раскладки: убрать «родителей», у которых год рождения не раньше ребёнка (ошибочные рёбра в БД). */
function sanitizeParentsOfForLayout(parentsOf, nodeById) {
  const out = {}
  for (const child of Object.keys(parentsOf)) {
    const plist = parentsOf[child]
    const cy = nodeById.get(child)?.birth_year
    const cyy = cy != null && Number.isFinite(Number(cy)) ? Number(cy) : null
    const filtered = plist.filter((p) => {
      const py = nodeById.get(p)?.birth_year
      const pyy = py != null && Number.isFinite(Number(py)) ? Number(py) : null
      if (cyy == null || pyy == null) return true
      return pyy < cyy
    })
    if (filtered.length) out[child] = filtered
  }
  return out
}

function siblingPairKey(a, b) {
  const x = sid(a)
  const y = sid(b)
  if (x === y) return null
  return x < y ? `${x}|${y}` : `${y}|${x}`
}

/**
 * Удаляет рёбра parent/child между узлами, которые по остальному графу — сиблинги
 * (общий родитель; пересечение детей у пары супругов). Лечит «столбик» вместо ряда
 * при ошибочном ребре «старший брат — родитель младшего» при корректных связях к отцу/матери.
 */
export function stripSiblingConflictingParentEdges(edges, nodes) {
  if (!nodes?.length) return edges || []
  if (!edges?.length) return []
  const nodeIds = new Set(nodes.map((n) => sid(n.memorial_id)))
  const nodeById = new Map(nodes.map((n) => [sid(n.memorial_id), n]))
  const raw = buildParentsOf(edges, nodeIds)
  const parentsOf = sanitizeParentsOfForLayout(raw, nodeById)

  const childrenOf = {}
  for (const child of Object.keys(parentsOf)) {
    for (const p of parentsOf[child] || []) {
      if (!childrenOf[p]) childrenOf[p] = []
      childrenOf[p].push(child)
    }
  }
  for (const p of Object.keys(childrenOf)) {
    childrenOf[p] = [...new Set(childrenOf[p])]
  }

  const siblingKeys = new Set()
  const addPair = (a, b) => {
    const k = siblingPairKey(a, b)
    if (k) siblingKeys.add(k)
  }

  for (const p of Object.keys(childrenOf)) {
    const kids = childrenOf[p]
    if (kids.length < 2) continue
    for (let i = 0; i < kids.length; i++) {
      for (let j = i + 1; j < kids.length; j++) {
        addPair(kids[i], kids[j])
      }
    }
  }

  for (const e of edges) {
    const t = normType(e.type)
    if (!SPOUSE_PAIR_TYPES.has(t)) continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!nodeIds.has(a) || !nodeIds.has(b)) continue
    const sa = new Set(childrenOf[a] || [])
    const sb = new Set(childrenOf[b] || [])
    const common = [...sa].filter((c) => sb.has(c))
    for (let i = 0; i < common.length; i++) {
      for (let j = i + 1; j < common.length; j++) {
        addPair(common[i], common[j])
      }
    }
  }

  return edges.filter((e) => {
    const typ = normType(e.type)
    if (!PARENT_TYPES.has(typ) && !CHILD_TYPES.has(typ)) return true
    // siblingPairKey симметричен (a|b == b|a), поэтому правильность имён не влияет на результат.
    // Семантика API: PARENT edge — source=ребёнок, target=родитель; CHILD edge — source=родитель, target=ребёнок.
    let idA
    let idB
    if (PARENT_TYPES.has(typ)) {
      idA = sid(e.source) // ребёнок
      idB = sid(e.target) // родитель
    } else {
      idA = sid(e.source) // родитель
      idB = sid(e.target) // ребёнок
    }
    if (!nodeIds.has(idA) || !nodeIds.has(idB)) return true
    const k = siblingPairKey(idA, idB)
    return !k || !siblingKeys.has(k)
  })
}

/**
 * @param {{ nodes: Array, edges: Array, root_id: number }} graphData
 */
export function refineFullTreeGenerations(graphData) {
  if (!graphData?.nodes?.length || graphData.root_id == null) return graphData
  const focalId = sid(graphData.root_id)
  const nodeIds = new Set(graphData.nodes.map((n) => sid(n.memorial_id)))
  const parentsOf = buildParentsOf(graphData.edges, nodeIds)
  const samePairs = buildSameGenPairs(graphData.edges, nodeIds)

  const generation = {}
  for (const n of graphData.nodes) {
    generation[sid(n.memorial_id)] = Number(n.generation) || 0
  }
  if (!(focalId in generation)) return graphData

  const maxIter = Math.max(200, Object.keys(generation).length * 10)
  for (let it = 0; it < maxIter; it++) {
    let changed = false
    for (const [a, b] of samePairs) {
      if (!(a in generation) || !(b in generation)) continue
      const g = Math.min(generation[a], generation[b])
      if (generation[a] !== g || generation[b] !== g) {
        generation[a] = generation[b] = g
        changed = true
      }
    }
    for (const child of Object.keys(parentsOf)) {
      if (!(child in generation)) continue
      const plist = parentsOf[child]
      if (!plist?.length) continue
      const known = plist.filter((p) => p in generation)
      if (!known.length) continue
      let pg = Math.min(...known.map((p) => generation[p]))
      for (const p of known) {
        if (generation[p] !== pg) {
          generation[p] = pg
          changed = true
        }
      }
      const exp = pg + 1
      if (generation[child] !== exp) {
        generation[child] = exp
        changed = true
      }
    }
    for (const child of Object.keys(parentsOf)) {
      if (!(child in generation)) continue
      const plist = parentsOf[child]
      if (!plist?.length) continue
      const cg = generation[child]
      for (const p of plist) {
        if (!(p in generation)) {
          generation[p] = cg - 1
          changed = true
        } else if (generation[p] !== cg - 1) {
          generation[p] = cg - 1
          changed = true
        }
      }
    }
    const d = -generation[focalId]
    if (d !== 0) {
      for (const k of Object.keys(generation)) generation[k] += d
      changed = true
    }
    if (!changed) break
  }

  return {
    ...graphData,
    nodes: graphData.nodes.map((n) => ({
      ...n,
      generation: generation[sid(n.memorial_id)] ?? n.generation,
    })),
  }
}

/**
 * Глубина ряда для раскладки «сверху вниз» (верх = более старшие по году рождения).
 * Старт: индекс по уникальным годам рождения (старые годы — меньший индекс = выше).
 * Затем: дети не выше родителей (child ≥ max(parent)+1), супруги/братья/custom — один ряд (min).
 * Так «молодые корни» без рёбер PARENT не всплывают над 1848 — у них больший год и ниже старт.
 * Если ни у кого нет birth_year — fallback: только граф (корни без родителей = 0).
 * Финально ряды перенумеровываются по min(год рождения) в ряду — самый старший ряд сверху, затем остальные.
 */
export function computeLayoutDepthOldestTop(nodes, edges) {
  if (!nodes?.length) return {}
  const nodeIds = new Set(nodes.map((n) => sid(n.memorial_id)))
  const parentsOfRaw = buildParentsOf(edges, nodeIds)
  const nodeById = new Map(nodes.map((n) => [sid(n.memorial_id), n]))
  const parentsOf = sanitizeParentsOfForLayout(parentsOfRaw, nodeById)
  const samePairs = mergeSameGenPairs(
    buildSameGenPairs(edges, nodeIds, true),
    inferFullSiblingPairsFromParents(parentsOf)
  )

  const uniqueYears = [
    ...new Set(
      nodes
        .map((n) => n.birth_year)
        .filter((y) => y != null && Number.isFinite(Number(y)))
        .map((y) => Number(y))
    ),
  ].sort((a, b) => a - b)
  const yearToRow = {}
  for (let i = 0; i < uniqueYears.length; i++) {
    yearToRow[uniqueYears[i]] = i
  }
  const rowBelowAllYears = uniqueYears.length

  const depth = {}
  if (uniqueYears.length > 0) {
    for (const id of nodeIds) {
      const n = nodeById.get(id)
      const y = n?.birth_year != null ? Number(n.birth_year) : null
      if (y != null && yearToRow[y] !== undefined) {
        depth[id] = yearToRow[y]
      } else {
        depth[id] = rowBelowAllYears
      }
    }
  } else {
    for (const id of nodeIds) {
      if (!parentsOf[id]?.length) {
        depth[id] = 0
      }
    }
    if (!Object.keys(depth).length) {
      for (const id of nodeIds) depth[id] = 0
    }
  }

  const genFallback = {}
  for (const n of nodes) {
    genFallback[sid(n.memorial_id)] = Number(n.generation) || 0
  }
  let minFb = Infinity
  for (const k of Object.keys(genFallback)) minFb = Math.min(minFb, genFallback[k])
  if (!Number.isFinite(minFb)) minFb = 0

  const maxIter = Math.max(200, nodeIds.size * 15)
  for (let it = 0; it < maxIter; it++) {
    let changed = false
    for (const child of Object.keys(parentsOf)) {
      const plist = parentsOf[child]
      if (!plist?.length) continue
      const pd = plist.map((p) => depth[p]).filter((d) => d !== undefined)
      if (pd.length !== plist.length) continue
      const exp = Math.max(...pd) + 1
      if (depth[child] !== exp) {
        depth[child] = exp
        changed = true
      }
    }
    for (const [a, b] of samePairs) {
      if (depth[a] === undefined && depth[b] === undefined) continue
      if (depth[a] === undefined) {
        depth[a] = depth[b]
        changed = true
        continue
      }
      if (depth[b] === undefined) {
        depth[b] = depth[a]
        changed = true
        continue
      }
      const m = Math.min(depth[a], depth[b])
      if (depth[a] !== m || depth[b] !== m) {
        depth[a] = depth[b] = m
        changed = true
      }
    }
    if (!changed) break
  }

  for (const id of nodeIds) {
    if (depth[id] === undefined) {
      depth[id] = genFallback[id] - minFb
    }
  }

  const remapped = remapDepthRowsOldestFirst(depth, nodeIds, parentsOf, samePairs, nodeById)
  const merged = {}
  for (const id of nodeIds) {
    merged[id] = remapped[id] !== undefined ? remapped[id] : depth[id]
  }

  const vals = [...nodeIds].map((id) => merged[id]).filter((d) => d !== undefined)
  if (!vals.length) return {}
  const minD = Math.min(...vals)
  const out = {}
  for (const id of nodeIds) {
    out[id] = merged[id] - minD
  }
  const aligned = alignSiblingRowsForLayout(out, nodes, edges, nodeIds, parentsOf)
  return mergeChildrenOfSameParentToOneRow(aligned, nodeIds, parentsOf)
}

/**
 * Все дети одного родителя — один ряд (одна глубина). Иначе при неполных PARENT/CHILD в API
 * у двоих детей разный parentsOf-ключ → «полные сиблинги» не срабатывают, ряд разъезжается по годам.
 */
function mergeChildrenOfSameParentToOneRow(res, nodeIds, parentsOf) {
  const childrenOf = {}
  for (const child of Object.keys(parentsOf)) {
    for (const p of parentsOf[child] || []) {
      if (!childrenOf[p]) childrenOf[p] = new Set()
      childrenOf[p].add(child)
    }
  }
  let out = { ...res }
  let changed = true
  let iter = 0
  while (changed && iter++ < 80) {
    changed = false
    for (const [p, set] of Object.entries(childrenOf)) {
      if (!nodeIds.has(p)) continue
      const kids = [...set].filter((c) => nodeIds.has(c))
      if (kids.length < 2) continue
      const depths = kids
        .map((c) => out[c])
        .filter((d) => d !== undefined && !Number.isNaN(Number(d)))
      if (!depths.length) continue
      const pd = out[p]
      let target = Math.min(...depths)
      if (pd !== undefined) target = Math.max(target, pd + 1)
      for (const c of kids) {
        if (out[c] !== undefined && out[c] !== target) {
          out[c] = target
          changed = true
        }
      }
    }
  }
  return out
}

/**
 * Один горизонтальный ряд для брат/сестра: после year-row + remap пары всё ещё могут разъехаться
 * (разные годы рождения, частичный граф). Принудительно выравниваем глубину.
 */
function alignSiblingRowsForLayout(out, nodes, edges, nodeIds, parentsOf) {
  const res = { ...out }
  const needChildRow = (childId) => {
    const plist = parentsOf[childId]
    if (!plist?.length) return undefined
    const pds = plist
      .map((p) => res[p])
      .filter((d) => d !== undefined && !Number.isNaN(Number(d)))
    if (!pds.length) return undefined
    return Math.max(...pds) + 1
  }

  for (const group of getFullSiblingGroupsForLayout(nodes, edges)) {
    const depths = group
      .map((id) => res[id])
      .filter((d) => d !== undefined && !Number.isNaN(Number(d)))
    if (depths.length < 2) continue
    const need = needChildRow(group[0])
    let target = Math.min(...depths)
    if (need !== undefined) target = Math.max(target, need)
    for (const id of group) {
      if (res[id] !== undefined) res[id] = target
    }
  }

  for (const e of edges || []) {
    const typ = normType(e.type)
    if (typ !== 'sibling' && typ !== 'half_sibling') continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!nodeIds.has(a) || !nodeIds.has(b)) continue
    const da = res[a]
    const db = res[b]
    if (da === undefined || db === undefined) continue
    const na = needChildRow(a)
    const nb = needChildRow(b)
    let target = Math.min(da, db)
    const needs = [na, nb].filter((x) => x !== undefined)
    if (needs.length) target = Math.max(target, ...needs)
    res[a] = res[b] = target
  }

  return res
}

/**
 * Группы полных сиблингов (одинаковые двое родителей).
 * Раскладка в UI — не более двух карточек в ряд (`familyTreeGenerationLayout` режет группы на пары и переносит).
 */
export function getFullSiblingGroupsForLayout(nodes, edges) {
  if (!nodes?.length) return []
  const nodeIds = new Set(nodes.map((n) => sid(n.memorial_id)))
  const raw = buildParentsOf(edges, nodeIds)
  const nodeById = new Map(nodes.map((n) => [sid(n.memorial_id), n]))
  const parentsOf = sanitizeParentsOfForLayout(raw, nodeById)
  const byKey = new Map()
  for (const child of Object.keys(parentsOf)) {
    const plist = [...(parentsOf[child] || [])].sort()
    if (plist.length < 2) continue
    const k = plist.join('|')
    if (!byKey.has(k)) byKey.set(k, [])
    byKey.get(k).push(child)
  }
  return [...byKey.values()].filter((g) => g.length >= 2)
}

function UnionFind(ids) {
  const parent = {}
  for (const id of ids) parent[id] = id
  function find(x) {
    if (parent[x] !== x) parent[x] = find(parent[x])
    return parent[x]
  }
  return {
    union(a, b) {
      const ra = find(a)
      const rb = find(b)
      if (ra !== rb) parent[rb] = ra
    },
    components() {
      const map = new Map()
      for (const id of Object.keys(parent)) {
        const r = find(id)
        if (!map.has(r)) map.set(r, [])
        map.get(r).push(id)
      }
      return [...map.values()]
    },
  }
}

function targetGenerationForComponent(ids, parentsOf, genById) {
  const parentSet = new Set()
  for (const id of ids) {
    for (const p of parentsOf[id] || []) parentSet.add(p)
  }
  let maxPd = -Infinity
  for (const p of parentSet) {
    const g = genById.get(p)
    if (g !== undefined && Number.isFinite(Number(g))) maxPd = Math.max(maxPd, Number(g))
  }
  const needChild = maxPd === -Infinity ? undefined : maxPd + 1
  const depths = ids
    .map((id) => genById.get(id))
    .filter((d) => d !== undefined && Number.isFinite(Number(d)))
    .map(Number)
  if (!depths.length) return undefined
  let target = Math.min(...depths)
  if (needChild !== undefined) target = Math.max(target, needChild)
  return target
}

/**
 * Последний барьер: один ряд для всех, кто связан как сиблинги ИЛИ имеет общего родителя в графе,
 * либо входит в пересечение «дети A» ∩ «дети B» для пары супругов (A, B) — полные сиблинги.
 * Решает случаи, когда computeLayoutDepthOldestTop и mergeChildrenOfSameParentToOneRow не сходятся.
 */
export function finalizeSiblingGenerations(nodes, edges) {
  if (!nodes?.length) return nodes
  const nodeIds = new Set(nodes.map((n) => sid(n.memorial_id)))
  const raw = buildParentsOf(edges, nodeIds)
  const nodeById = new Map(nodes.map((n) => [sid(n.memorial_id), n]))
  const parentsOf = sanitizeParentsOfForLayout(raw, nodeById)

  const uf = UnionFind([...nodeIds])
  for (const group of getFullSiblingGroupsForLayout(nodes, edges)) {
    for (let i = 1; i < group.length; i++) uf.union(group[0], group[i])
  }
  for (const e of edges || []) {
    const t = normType(e.type)
    if (t !== 'sibling' && t !== 'half_sibling') continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (nodeIds.has(a) && nodeIds.has(b)) uf.union(a, b)
  }
  const childrenOf = {}
  for (const child of Object.keys(parentsOf)) {
    for (const p of parentsOf[child] || []) {
      if (!childrenOf[p]) childrenOf[p] = []
      childrenOf[p].push(child)
    }
  }
  for (const p of Object.keys(childrenOf)) {
    const kids = [...new Set(childrenOf[p])]
    if (kids.length < 2) continue
    for (let i = 1; i < kids.length; i++) uf.union(kids[0], kids[i])
  }

  const childrenOfSets = {}
  for (const p of Object.keys(childrenOf)) {
    childrenOfSets[p] = new Set(childrenOf[p])
  }
  for (const e of edges || []) {
    const t = normType(e.type)
    if (!SPOUSE_PAIR_TYPES.has(t)) continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!nodeIds.has(a) || !nodeIds.has(b)) continue
    const sa = childrenOfSets[a]
    const sb = childrenOfSets[b]
    if (!sa || !sb) continue
    const common = [...sa].filter((c) => sb.has(c))
    if (common.length < 2) continue
    for (let i = 1; i < common.length; i++) uf.union(common[0], common[i])
  }

  const genById = new Map()
  for (const n of nodes) {
    const id = sid(n.memorial_id)
    const g = n.generation
    if (g !== undefined && g !== null && Number.isFinite(Number(g))) genById.set(id, Number(g))
  }

  const comps = uf.components()
  for (const comp of comps) {
    if (comp.length < 2) continue
    const target = targetGenerationForComponent(comp, parentsOf, genById)
    if (target === undefined) continue
    for (const id of comp) genById.set(id, target)
  }

  return nodes.map((n) => {
    const id = sid(n.memorial_id)
    const g = genById.get(id)
    return g !== undefined ? { ...n, generation: g } : n
  })
}
