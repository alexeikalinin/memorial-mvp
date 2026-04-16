/**
 * Раскладка полного графа по горизонтальным «этажам» поколений + эвристика двух линий (фамилии).
 * Использует поля generation / edges из GET /family/memorials/:id/full-tree
 */

import {
  refineFullTreeGenerations,
  computeLayoutDepthOldestTop,
  getFullSiblingGroupsForLayout,
  finalizeSiblingGenerations,
  normalizeGenerationValue,
  stripSiblingConflictingParentEdges,
} from './familyTreeGenerations.js'

const sid = (id) => String(id)

// GOT-style compact circles: smaller nodes, tighter gaps
const NODE_W = 90
/** Node height: avatar (80px) + gap (4px) + name (2 lines ~26px) + years (12px) + rel label (14px) + padding = 148px.
 *  overflow:hidden clips at this boundary so text never enters the INTER_GEN_GAP. */
const NODE_H = 148
const GAP_X = 40
/** Разрыв между «полосами» линии A / центр (пересечение) / линия B — больше = семьи визуально дальше */
const LINEAGE_LANE_GAP = 260
/** Базовая высота «этажа» (для совместимости с коннекторами); фактическая высота поколения может быть больше при переносе пар */
export const ROW_H = 148
/** На одной горизонтали в сегменте — максимум карточек подряд; сиблинги и одиночки всегда в одну строку */
const MAX_CARDS_PER_HORIZONTAL = 8
/** Между подстроками внутри одного поколения (перенос пар/сиблингов) */
const SUB_ROW_GAP = 32
/** Между этажами поколений (родители → дети): ≥50px чтобы коннекторы не перекрывались с именами. */
const INTER_GEN_GAP = 56
const PAD = 48
const LABEL_W = 120

export function surnameOf(name) {
  if (!name || typeof name !== 'string') return ''
  const parts = name
    .replace(/\(.*?\)/g, '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (!parts.length) return ''
  const last = parts[parts.length - 1]
  return /^[A-Za-zА-Яа-яёЁ\-']+$/.test(last) ? last : ''
}

function lineageVal(lineageMap, id) {
  if (!lineageMap) return 'N'
  return lineageMap[id] ?? lineageMap[Number(id)] ?? lineageMap[sid(id)] ?? 'N'
}

/** Стабильный «семейный» цвет для линии N (не топ-2 фамилий) — кольца, слияния */
export function neutralSurnameRingStroke(surname) {
  if (!surname) return 'rgba(212, 188, 140, 0.98)'
  let h = 0
  for (let i = 0; i < surname.length; i++) h = (h * 33 + surname.charCodeAt(i)) >>> 0
  const palette = [
    [42, 88, 56],
    [32, 82, 54],
    [142, 62, 48],
    [18, 76, 58],
    [88, 58, 46],
    [52, 90, 52],
    [168, 55, 45],
    [24, 70, 55],
  ]
  const [hue, sat, light] = palette[h % palette.length]
  return `hsla(${hue}, ${sat}%, ${light}%, 0.97)`
}

/** Цвет ободка колец брака — по кластеру фамилий или запасной хэш */
export function lineageRingStroke(memorialId, lineageMap, fullName, memorialClusterStyle) {
  const st =
    memorialClusterStyle?.[memorialId] ??
    memorialClusterStyle?.[sid(memorialId)] ??
    memorialClusterStyle?.[Number(memorialId)]
  if (st?.ringStroke) return st.ringStroke
  const L = lineageVal(lineageMap, memorialId)
  if (L === 'A') return 'rgba(95, 188, 255, 0.98)'
  if (L === 'B') return 'rgba(218, 140, 255, 0.98)'
  return neutralSurnameRingStroke(surnameOf(fullName || ''))
}

/** Разные супруги по кластеру фамилии (для пунктира / моста) */
export function isDistinctClusterPair(memorialClusterStyle, idA, idB) {
  if (!memorialClusterStyle) return null
  const sa =
    memorialClusterStyle[idA] ??
    memorialClusterStyle[sid(idA)] ??
    memorialClusterStyle[Number(idA)]
  const sb =
    memorialClusterStyle[idB] ??
    memorialClusterStyle[sid(idB)] ??
    memorialClusterStyle[Number(idB)]
  if (
    sa &&
    sb &&
    typeof sa.clusterIndex === 'number' &&
    typeof sb.clusterIndex === 'number'
  ) {
    return sa.clusterIndex !== sb.clusterIndex
  }
  return null
}

const OTHER_SURNAME_KEY = '__other__'

const CLUSTER_BORDER_PALETTE = [
  { h: 210, s: 88, l: 62 },
  { h: 285, s: 78, l: 63 },
  { h: 145, s: 72, l: 46 },
  { h: 32, s: 92, l: 56 },
  { h: 175, s: 70, l: 44 },
  { h: 42, s: 92, l: 54 },
  { h: 350, s: 80, l: 58 },
  { h: 265, s: 62, l: 64 },
  { h: 100, s: 58, l: 48 },
  { h: 18, s: 86, l: 56 },
  { h: 305, s: 75, l: 58 },
  { h: 198, s: 85, l: 52 },
]

/**
 * Одна яркая рамка на фамилию (не только топ-2): легенда + стили карточек и колец.
 */
export function buildSurnameClusterStyles(nodes) {
  const counts = {}
  for (const n of nodes) {
    const s = surnameOf(n.name)
    const key = s || OTHER_SURNAME_KEY
    counts[key] = (counts[key] || 0) + 1
  }
  const orderedKeys = Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([k]) => k)
  const keyToIdx = {}
  orderedKeys.forEach((k, i) => {
    keyToIdx[k] = i
  })
  const pick = (i) => CLUSTER_BORDER_PALETTE[i % CLUSTER_BORDER_PALETTE.length]

  const clusterLegend = orderedKeys.map((key, i) => {
    const p = pick(i)
    const border = `hsla(${p.h}, ${p.s}%, ${p.l}%, 0.92)`
    const ringStroke = `hsla(${p.h}, ${p.s}%, ${Math.min(p.l + 6, 74)}%, 0.98)`
    const pillBg = `hsla(${p.h}, ${Math.max(p.s - 35, 38)}%, 20%, 0.55)`
    return {
      key,
      border,
      ringStroke,
      pillBg,
      textColor: 'rgba(252, 248, 242, 0.95)',
    }
  })

  const memorialClusterStyle = {}
  for (const n of nodes) {
    const s = surnameOf(n.name)
    const key = s || OTHER_SURNAME_KEY
    const i = keyToIdx[key]
    const p = pick(i)
    const borderColor = `hsla(${p.h}, ${p.s}%, ${p.l}%, 0.92)`
    const ringStroke = `hsla(${p.h}, ${p.s}%, ${Math.min(p.l + 6, 74)}%, 0.98)`
    const st = {
      clusterIndex: i,
      borderColor,
      ringStroke,
      boxShadow: `inset 0 0 0 1px hsla(${p.h}, ${p.s}%, ${p.l}%, 0.52), 0 0 22px hsla(${p.h}, ${p.s}%, ${p.l}%, 0.42)`,
    }
    memorialClusterStyle[n.memorial_id] = st
    memorialClusterStyle[sid(n.memorial_id)] = st
  }

  return { clusterLegend, memorialClusterStyle, otherSurnameKey: OTHER_SURNAME_KEY }
}

/** Супруги из разных визуальных кластеров (A≠B, A≠N, N≠N с разными фамилиями …) */
export function isDistinctFamilyPair(lineageMap, idA, idB, nameA, nameB) {
  const x = lineageVal(lineageMap, idA)
  const y = lineageVal(lineageMap, idB)
  if (x !== y) return true
  if (x === 'N' && y === 'N') {
    const sa = surnameOf(nameA || '')
    const sb = surnameOf(nameB || '')
    return !!(sa && sb && sa !== sb)
  }
  return false
}

/** Линии A/B/C/D: Kelly слева, Anderson справа, 3-я/4-я фамилии — отдельные правые колонки. */
export function assignLineages(nodes) {
  const counts = {}
  for (const n of nodes) {
    const s = surnameOf(n.name)
    if (s) counts[s] = (counts[s] || 0) + 1
  }
  const keys = Object.keys(counts)
  let aSurname = ''
  let bSurname = ''
  let cSurname = ''
  let dSurname = ''
  if (keys.includes('Kelly') && keys.includes('Anderson')) {
    aSurname = 'Kelly'
    bSurname = 'Anderson'
    const third = keys
      .filter((k) => k !== 'Kelly' && k !== 'Anderson')
      .sort((k1, k2) => (counts[k2] || 0) - (counts[k1] || 0) || k1.localeCompare(k2))[0]
    cSurname = third || ''
    const fourth = keys
      .filter((k) => k !== 'Kelly' && k !== 'Anderson' && k !== cSurname)
      .sort((k1, k2) => (counts[k2] || 0) - (counts[k1] || 0) || k1.localeCompare(k2))[0]
    dSurname = fourth || ''
  } else {
    const top = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map((e) => e[0])
    aSurname = top[0] || ''
    bSurname = top[1] || ''
    cSurname = top[2] || ''
    dSurname = top[3] || ''
  }
  const lineage = {}
  for (const n of nodes) {
    const s = surnameOf(n.name)
    if (aSurname && s === aSurname) lineage[n.memorial_id] = 'A'
    else if (bSurname && s === bSurname) lineage[n.memorial_id] = 'B'
    else if (cSurname && s === cSurname) lineage[n.memorial_id] = 'C'
    else if (dSurname && s === dSurname) lineage[n.memorial_id] = 'D'
    else lineage[n.memorial_id] = 'N'
  }
  return { lineage, surnameA: aSurname, surnameB: bSurname, surnameC: cSurname, surnameD: dSurname }
}

function isSpouseType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'spouse' || u === 'partner' || u === 'ex_spouse'
}

function isSiblingEdgeType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'sibling' || u === 'half_sibling'
}

function sortSiblingIds(ids, nodeById) {
  return [...ids].sort((a, b) => {
    const sa = sid(a)
    const sb = sid(b)
    const na = nodeById.get(sa)
    const nb = nodeById.get(sb)
    const ya = na?.birth_year != null ? Number(na.birth_year) : 9999
    const yb = nb?.birth_year != null ? Number(nb.birth_year) : 9999
    if (ya !== yb) return ya - yb
    return sa.localeCompare(sb)
  })
}

function unitSortKey(memorialId, lineageMap) {
  const L = lineageMap[memorialId] || 'N'
  if (L === 'A') return 0
  if (L === 'N') return 1
  if (L === 'B') return 2
  if (L === 'C') return 3
  if (L === 'D') return 4
  return 1
}

/**
 * Пары супругов; полные сиблинги — только по 2 в юнит (несколько юнитов подряд); пары по ребру sibling/half_sibling; одиночки.
 */
function buildUnitsInGeneration(genNodes, edges, lineageMap, allNodes) {
  const ids = genNodes.map((n) => sid(n.memorial_id))
  const idSet = new Set(ids)
  const paired = new Set()
  const units = []
  const nodeById = new Map((allNodes || genNodes).map((n) => [sid(n.memorial_id), n]))

  for (const e of edges) {
    if (!isSpouseType(e.type)) continue
    const s = sid(e.source)
    const t = sid(e.target)
    if (!idSet.has(s) || !idSet.has(t)) continue
    if (paired.has(s) || paired.has(t)) continue
    paired.add(s)
    paired.add(t)
    const a = parseInt(s, 10)
    const b = parseInt(t, 10)
    const order =
      unitSortKey(a, lineageMap) !== unitSortKey(b, lineageMap)
        ? unitSortKey(a, lineageMap) < unitSortKey(b, lineageMap)
          ? [a, b]
          : [b, a]
        : a < b
          ? [a, b]
          : [b, a]
    units.push({ type: 'pair', ids: order })
  }

  const fullGroups = getFullSiblingGroupsForLayout(allNodes || genNodes, edges)
  for (const group of fullGroups) {
    const inGen = group.filter((id) => idSet.has(id) && !paired.has(id))
    if (inGen.length < 2) continue
    const ordered = sortSiblingIds(inGen, nodeById)
    for (const id of ordered) paired.add(sid(id))
    // All siblings in one unit — they must appear on the same horizontal line
    units.push({
      type: 'siblingGroup',
      ids: ordered.map((id) => parseInt(id, 10)),
    })
  }

  for (const e of edges) {
    if (!isSiblingEdgeType(e.type)) continue
    const s = sid(e.source)
    const t = sid(e.target)
    if (!idSet.has(s) || !idSet.has(t)) continue
    if (paired.has(s) || paired.has(t)) continue
    paired.add(s)
    paired.add(t)
    const order = sortSiblingIds([s, t], nodeById).map((id) => parseInt(id, 10))
    units.push({ type: 'siblingGroup', ids: order })
  }

  const singles = ids.filter((id) => !paired.has(id)).map((id) => parseInt(id, 10))
  singles.sort((a, b) => {
    const ka = unitSortKey(a, lineageMap) - unitSortKey(b, lineageMap)
    if (ka !== 0) return ka
    const na = genNodes.find((n) => n.memorial_id === a)?.name || ''
    const nb = genNodes.find((n) => n.memorial_id === b)?.name || ''
    return na.localeCompare(nb)
  })

  for (const mid of singles) {
    units.push({ type: 'single', ids: [mid] })
  }

  units.sort((u1, u2) => {
    const k1 = Math.min(...u1.ids.map((id) => unitSortKey(id, lineageMap)))
    const k2 = Math.min(...u2.ids.map((id) => unitSortKey(id, lineageMap)))
    if (k1 !== k2) return k1 - k2
    return u1.ids[0] - u2.ids[0]
  })

  return units
}

/** Ширина ряда из плоского списка id (подряд карточки). */
function rowWidthForIds(count) {
  if (count <= 0) return 0
  return count * NODE_W + Math.max(0, count - 1) * GAP_X
}

function countUnitsCards(units) {
  let n = 0
  for (const u of units) n += u.ids.length
  return n
}

/**
 * Group units within a lane segment into sub-rows.
 * Units are placed on the same sub-row when connected by:
 *   - sibling / half_sibling edges
 *   - spouse / partner / ex_spouse edges
 *   - shared parent (half-siblings from different marriages → same row, no crossing lines)
 * Returns an array of "row groups", each group being an array of units.
 */
function groupUnitsByRow(units, edgeList) {
  if (!units.length) return []
  // Map each node id → unit index
  const idToUnit = new Map()
  units.forEach((u, i) => u.ids.forEach((id) => idToUnit.set(String(id), i)))
  // Union-Find
  const par = units.map((_, i) => i)
  function find(x) { return par[x] === x ? x : (par[x] = find(par[x])) }
  function union(a, b) {
    const pa = find(a), pb = find(b)
    if (pa !== pb) par[pa] = pb
  }
  // 1) Union units connected by sibling OR spouse/ex_spouse edges
  for (const e of edgeList) {
    const et = String(e.type).toLowerCase()
    const isSib = et === 'sibling' || et === 'half_sibling'
    const isSp = et === 'spouse' || et === 'partner' || et === 'ex_spouse'
    if (!isSib && !isSp) continue
    const si = idToUnit.get(String(e.source))
    const ti = idToUnit.get(String(e.target))
    if (si === undefined || ti === undefined || si === ti) continue
    union(si, ti)
  }
  // 2) Union units that share a common parent (half-siblings / children of different marriages)
  //    Without this, Claire (of Robert+Linda) and Michael (of Robert+Patricia) end up in
  //    separate sub-rows and their connector lines cross each other.
  const parentOf = {}  // childId → Set<parentId>
  for (const e of edgeList) {
    const et = String(e.type).toLowerCase()
    let parentId, childId
    if (et === 'child' || et === 'adoptive_child' || et === 'step_child') {
      parentId = String(e.source); childId = String(e.target)
    } else if (et === 'parent' || et === 'adoptive_parent' || et === 'step_parent') {
      parentId = String(e.target); childId = String(e.source)
    } else continue
    const ci = idToUnit.get(childId)
    if (ci === undefined) continue  // child not in this segment
    if (!parentOf[parentId]) parentOf[parentId] = []
    parentOf[parentId].push(ci)
  }
  for (const childUnits of Object.values(parentOf)) {
    // All units that share this parent → same row group
    for (let i = 1; i < childUnits.length; i++) union(childUnits[0], childUnits[i])
  }
  // Collect clusters in order of first appearance
  const clusterOrder = []
  const clusterMap = new Map()
  units.forEach((u, i) => {
    const root = find(i)
    if (!clusterMap.has(root)) { clusterMap.set(root, []); clusterOrder.push(root) }
    clusterMap.get(root).push(u)
  })
  return clusterOrder.map((r) => clusterMap.get(r))
}

/**
 * Build a Set of "min|max" id pairs that are auto-detected as ex-spouses:
 * Person X has 2+ spouse connections and one of their partners died earlier
 * than another (= prior/replaced marriage). Mirrors the logic in
 * familyTreeOrthogonalConnectors.js → autoExSet.
 */
function buildAutoExSet(edgeList, allNodes) {
  const idToDead = new Map()
  const idToDeathYear = new Map()
  for (const n of allNodes || []) {
    idToDead.set(String(n.memorial_id), !!n.death_year)
    idToDeathYear.set(String(n.memorial_id), n.death_year || null)
  }
  // Collect spouse pairs
  const spousePairsArr = []
  const seen = new Set()
  for (const e of edgeList || []) {
    const et = String(e.type).toLowerCase()
    if (et !== 'spouse' && et !== 'partner' && et !== 'ex_spouse') continue
    const a = String(e.source), b = String(e.target)
    const key = a < b ? `${a}|${b}` : `${b}|${a}`
    if (seen.has(key)) continue
    seen.add(key)
    spousePairsArr.push([a, b, et])
  }
  // Count spouses per person
  const spousePartnersOf = {}
  for (const [a, b] of spousePairsArr) {
    ;(spousePartnersOf[a] = spousePartnersOf[a] || []).push(b)
    ;(spousePartnersOf[b] = spousePartnersOf[b] || []).push(a)
  }
  const autoExSet = new Set()
  for (const [personId, partners] of Object.entries(spousePartnersOf)) {
    if (partners.length < 2) continue
    const anyAlive = partners.some((p) => !idToDead.get(p))
    if (anyAlive) {
      for (const p of partners) {
        if (idToDead.get(p)) autoExSet.add(personId < p ? `${personId}|${p}` : `${p}|${personId}`)
      }
    } else {
      // All partners deceased — 💔 for those who died earliest (= prior marriage)
      const sorted = partners.slice().sort((x, y) => {
        return (idToDeathYear.get(x) || 9999) - (idToDeathYear.get(y) || 9999)
      })
      for (let i = 0; i < sorted.length - 1; i++) {
        const p = sorted[i]
        autoExSet.add(personId < p ? `${personId}|${p}` : `${p}|${personId}`)
      }
    }
  }
  // Also include explicit ex_spouse edges
  for (const [a, b, et] of spousePairsArr) {
    if (et === 'ex_spouse') autoExSet.add(a < b ? `${a}|${b}` : `${b}|${a}`)
  }
  return autoExSet
}

/**
 * Reorder units within a row group so ex-spouse singles appear BEFORE the pair
 * they're connected to. This keeps [Patricia 💔 Robert ♥ Linda] order instead of
 * [Robert ♥ Linda … Patricia] where the 💔 would be hidden behind Linda.
 */
function reorderGroupForExSpouse(group, edgeList, allNodes) {
  if (group.length < 2) return group
  const exPairs = buildAutoExSet(edgeList, allNodes)
  if (!exPairs.size) return group

  // Find a pair unit and a single unit connected via ex-spouse
  let pairIdx = -1
  let exSingleIdx = -1
  outer:
  for (let i = 0; i < group.length; i++) {
    if (group[i].type !== 'pair') continue
    for (let j = 0; j < group.length; j++) {
      if (i === j || group[j].type === 'pair') continue
      for (const pid of group[i].ids) {
        for (const sid2 of group[j].ids) {
          const key = String(pid) < String(sid2)
            ? `${pid}|${sid2}` : `${sid2}|${pid}`
          if (exPairs.has(key)) {
            pairIdx = i
            exSingleIdx = j
            break outer
          }
        }
      }
    }
  }
  if (exSingleIdx === -1) return group

  // Move ex-spouse single to just before the pair → [Patricia, Robert+Linda]
  const result = group.filter((_, i) => i !== exSingleIdx)
  const insertAt = result.indexOf(group[pairIdx])
  result.splice(insertAt, 0, group[exSingleIdx])
  return result
}

/** Width of the widest sub-row in a set of row groups */
function rowGroupsWidth(groups) {
  let maxW = 0
  for (const group of groups) {
    const n = group.reduce((s, u) => s + u.ids.length, 0)
    maxW = Math.max(maxW, rowWidthForIds(n))
  }
  return maxW
}

/**
 * Раскидать юниты по 5 полосам: A слева, центр, B справа, C и D — правые дополнительные.
 * Сохраняет порядок появления юнитов в исходном списке.
 */
function clusterUnitsIntoLanes(units, lineageMap, hasAInRow, hasBInRow, hasCInRow, hasDInRow) {
  const left = []
  const center = []
  const right = []
  const farRight = []
  const extraRight = []
  for (const u of units) {
    const Ls = u.ids.map((id) => lineageMap[id] || 'N')
    const hasA = Ls.includes('A')
    const hasB = Ls.includes('B')
    const hasC = Ls.includes('C')
    const hasD = Ls.includes('D')
    // 'N' = bridge node (connected to a stub) — always placed in center column
    const hasBridge = Ls.includes('N')
    let bucket = left
    if (hasBridge) {
      // Any unit containing a bridge node goes to center (cross-family couple column)
      bucket = center
    } else if ((hasA && hasB) || (hasA && hasC) || (hasB && hasC) || hasD && (hasA || hasB || hasC)) {
      bucket = center
    } else if (hasD && !hasA && !hasB && !hasC) bucket = extraRight
    else if (hasC && !hasA && !hasB && !hasD) bucket = farRight
    else if (hasB && !hasA) bucket = right
    else if (hasA && !hasB) bucket = left
    else {
      if (
        (hasAInRow && hasBInRow) ||
        (hasAInRow && hasCInRow) ||
        (hasAInRow && hasDInRow) ||
        (hasBInRow && hasCInRow) ||
        (hasBInRow && hasDInRow) ||
        (hasCInRow && hasDInRow)
      ) bucket = center
      else if (hasDInRow && !hasAInRow && !hasBInRow && !hasCInRow) bucket = extraRight
      else if (hasCInRow && !hasAInRow && !hasBInRow && !hasDInRow) bucket = farRight
      else if (hasBInRow && !hasAInRow) bucket = right
      else bucket = left
    }
    bucket.push(u)
  }
  return { left, center, right, farRight, extraRight }
}

/** Ширина колонки: не больше двух карточек в ряд — ширина сегмента по самой широкой линии */
function segmentWidthUnits(units) {
  if (!units.length) return 0
  // Width = widest single unit in the segment (siblings all on one row)
  let maxW = 0
  for (const u of units) maxW = Math.max(maxW, rowWidthForIds(u.ids.length))
  return maxW
}

/** То же с меткой колонки для фиксированной раскладки (A слева, B справа). */
function nonEmptyLanesTagged(left, center, right, farRight, extraRight) {
  const out = []
  if (left.length) out.push({ kind: 'left', units: left })
  if (center.length) out.push({ kind: 'center', units: center })
  if (right.length) out.push({ kind: 'right', units: right })
  if (farRight.length) out.push({ kind: 'farRight', units: farRight })
  if (extraRight.length) out.push({ kind: 'extraRight', units: extraRight })
  return out
}

/**
 * @param {boolean} [singleFamilyMode=false]  When true: ignore lane separation (no LINEAGE_LANE_GAP).
 *   All units are placed in one centred column. Use when only one primary family is visible.
 * @returns {{ positions, canvas, lineage, surnameA, surnameB, orderedIds, minGen, maxGen, genBands, labelAreaX, labelAreaW }}
 */
export function buildGenerationLayout(graphData, singleFamilyMode = false) {
  const nodesIn = graphData?.nodes || []
  const edgesStripped = stripSiblingConflictingParentEdges(graphData?.edges || [], nodesIn)
  const graphForRefine = graphData ? { ...graphData, edges: edgesStripped } : graphData
  const refined =
    graphForRefine?.nodes?.length && graphForRefine.root_id != null
      ? refineFullTreeGenerations(graphForRefine)
      : graphForRefine
  const rawNodes = refined?.nodes || []
  const edges = refined?.edges || []
  const layoutDepth = rawNodes.length ? computeLayoutDepthOldestTop(rawNodes, edges) : {}

  // In singleFamilyMode, stub nodes from other families may land at wrong depths
  // (e.g. born earlier than visible-family members, placed in an ancestor row).
  // Snap each stub to the average generation of its directly-connected visible neighbors.
  if (singleFamilyMode) {
    const visibleGenIds = new Set(rawNodes.filter((n) => !n._stub).map((n) => sid(n.memorial_id)))
    for (const n of rawNodes) {
      if (!n._stub) continue
      const id = sid(n.memorial_id)
      const neighborGens = []
      for (const e of edges) {
        const s = sid(e.source)
        const t = sid(e.target)
        if (s === id && visibleGenIds.has(t) && layoutDepth[t] !== undefined) neighborGens.push(layoutDepth[t])
        if (t === id && visibleGenIds.has(s) && layoutDepth[s] !== undefined) neighborGens.push(layoutDepth[s])
      }
      if (neighborGens.length) {
        layoutDepth[id] = Math.round(neighborGens.reduce((a, b) => a + b, 0) / neighborGens.length)
      }
    }
  }

  const nodesAfterDepth = rawNodes.map((n) => {
    const id = sid(n.memorial_id)
    const g = layoutDepth[id]
    return g !== undefined ? { ...n, generation: g } : n
  })
  const nodes = finalizeSiblingGenerations(nodesAfterDepth, edges)
  if (!nodes.length) {
    return {
      positions: {},
      canvas: { width: 400, height: 300 },
      lineage: {},
      surnameA: '',
      surnameB: '',
      orderedIds: [],
      minGen: 0,
      maxGen: 0,
      laneGapBands: [],
      clusterLegend: [],
      memorialClusterStyle: {},
      otherSurnameKey: OTHER_SURNAME_KEY,
    }
  }

  const { lineage, surnameA, surnameB } = assignLineages(nodes)
  const { clusterLegend, memorialClusterStyle, otherSurnameKey } = buildSurnameClusterStyles(nodes)
  const byGen = {}
  let minGen = Infinity
  let maxGen = -Infinity
  for (const n of nodes) {
    const g = normalizeGenerationValue(n.generation)
    minGen = Math.min(minGen, g)
    maxGen = Math.max(maxGen, g)
    if (!byGen[g]) byGen[g] = []
    byGen[g].push({ ...n, generation: g })
  }

  // In singleFamilyMode:
  //   - visible nodes NOT connected to stubs → 'A' (left column, pure family)
  //   - visible nodes directly connected to stubs → 'N' (center column, bridge couple)
  //   - stub nodes → 'B' (right column)
  //
  // This gives the "bridge couple in the middle" layout:
  //   [Pure Kelly] | [Kelly ♥ Anderson-born] | [Anderson stubs]
  const stubIdSet = singleFamilyMode
    ? new Set(nodes.filter((n) => n._stub).map((n) => String(n.memorial_id)))
    : new Set()

  let effectiveLineage
  if (singleFamilyMode) {
    // Start: non-stub → 'A', stub → 'B'
    effectiveLineage = Object.fromEntries(
      Object.keys(lineage).map((k) => [k, stubIdSet.has(k) ? 'B' : 'A'])
    )
    // Promote to 'N' any non-stub node that has a direct edge to a stub
    for (const k of Object.keys(effectiveLineage)) {
      if (effectiveLineage[k] !== 'A') continue
      for (const e of edges) {
        const s = String(e.source)
        const t = String(e.target)
        if ((s === k && effectiveLineage[t] === 'B') || (t === k && effectiveLineage[s] === 'B')) {
          effectiveLineage[k] = 'N'
          break
        }
      }
    }
    // Propagate 'N' to descendants — BUT only when ALL known parents are N.
    // This prevents children of mixed couples (one N parent + one A parent, e.g. first marriage)
    // from being pulled into the bridge center column.
    let npChanged = true
    while (npChanged) {
      npChanged = false
      const childParentCounts = {}
      for (const e of edges) {
        const et = String(e.type).toLowerCase()
        let parentId, childId
        if (et === 'child' || et === 'adoptive_child' || et === 'step_child') {
          parentId = String(e.source); childId = String(e.target)
        } else if (et === 'parent' || et === 'adoptive_parent' || et === 'step_parent') {
          parentId = String(e.target); childId = String(e.source)
        } else continue
        if (!effectiveLineage[parentId] || !effectiveLineage[childId]) continue
        if (!childParentCounts[childId]) childParentCounts[childId] = { total: 0, nCount: 0 }
        childParentCounts[childId].total++
        if (effectiveLineage[parentId] === 'N') childParentCounts[childId].nCount++
      }
      for (const [childId, counts] of Object.entries(childParentCounts)) {
        if (
          effectiveLineage[childId] === 'A' &&
          counts.total > 0 &&
          counts.nCount === counts.total  // ALL parents must be N
        ) {
          effectiveLineage[childId] = 'N'
          npChanged = true
        }
      }
    }
  } else {
    effectiveLineage = lineage
  }

  const rowLanes = {}
  let maxLeftW = 0
  let maxCenterW = 0
  let maxRightW = 0
  let maxFarRightW = 0
  let maxExtraRightW = 0
  let hasAnyLeft = false
  let hasAnyCenter = false
  let hasAnyRight = false
  let hasAnyFarRight = false
  let hasAnyExtraRight = false
  for (let g = minGen; g <= maxGen; g++) {
    const rowNodes = byGen[g] || []
    const units = buildUnitsInGeneration(rowNodes, edges, effectiveLineage, nodes)
    const hasAInRow = rowNodes.some((n) => effectiveLineage[n.memorial_id] === 'A')
    const hasBInRow = rowNodes.some((n) => effectiveLineage[n.memorial_id] === 'B')
    const hasCInRow = !singleFamilyMode && rowNodes.some((n) => lineage[n.memorial_id] === 'C')
    const hasDInRow = !singleFamilyMode && rowNodes.some((n) => lineage[n.memorial_id] === 'D')
    const { left, center, right, farRight, extraRight } = clusterUnitsIntoLanes(
      units,
      effectiveLineage,
      hasAInRow,
      hasBInRow,
      hasCInRow,
      hasDInRow
    )
    rowLanes[g] = { left, center, right, farRight, extraRight }
    if (left.length) hasAnyLeft = true
    if (center.length) hasAnyCenter = true
    if (right.length) hasAnyRight = true
    if (farRight.length) hasAnyFarRight = true
    if (extraRight.length) hasAnyExtraRight = true
    maxLeftW = Math.max(maxLeftW, rowGroupsWidth(groupUnitsByRow(left, edges)))
    maxCenterW = Math.max(maxCenterW, rowGroupsWidth(groupUnitsByRow(center, edges)))
    maxRightW = Math.max(maxRightW, rowGroupsWidth(groupUnitsByRow(right, edges)))
    maxFarRightW = Math.max(maxFarRightW, rowGroupsWidth(groupUnitsByRow(farRight, edges)))
    maxExtraRightW = Math.max(maxExtraRightW, rowGroupsWidth(groupUnitsByRow(extraRight, edges)))
  }

  // singleFamilyMode: small gap — stubs just to the right of main family column
  const laneGap = singleFamilyMode ? 100 : LINEAGE_LANE_GAP

  /** Фиксированные колонки: без центрирования ряда — иначе строки только Kelly и только Anderson накладываются по X. */
  const columnLayout = []
  let xCursor = PAD + LABEL_W
  if (hasAnyLeft) {
    columnLayout.push({ kind: 'left', start: xCursor, maxW: maxLeftW })
    xCursor += maxLeftW
    if (hasAnyCenter || hasAnyRight) xCursor += laneGap
  }
  if (hasAnyCenter) {
    columnLayout.push({ kind: 'center', start: xCursor, maxW: maxCenterW })
    xCursor += maxCenterW
    if (hasAnyRight) xCursor += laneGap
  }
  if (hasAnyRight) {
    columnLayout.push({ kind: 'right', start: xCursor, maxW: maxRightW })
    xCursor += maxRightW
    if (hasAnyFarRight) xCursor += laneGap
  }
  if (hasAnyFarRight) {
    columnLayout.push({ kind: 'farRight', start: xCursor, maxW: maxFarRightW })
    xCursor += maxFarRightW
    if (hasAnyExtraRight) xCursor += laneGap
  }
  if (hasAnyExtraRight) {
    columnLayout.push({ kind: 'extraRight', start: xCursor, maxW: maxExtraRightW })
    xCursor += maxExtraRightW
  }

  const canvasW = Math.max(720, xCursor + PAD)

  const genBandTop = {}
  const genBandHeight = {}
  let yAcc = PAD
  for (let g = minGen; g <= maxGen; g++) {
    const { left, center, right, farRight, extraRight } = rowLanes[g]
    const laneGroups = [left, center, right, farRight, extraRight]
      .filter((arr) => arr.length > 0)
      .map((arr) => groupUnitsByRow(arr, edges))
    const maxLines = laneGroups.length
      ? Math.max(1, ...laneGroups.map((gs) => gs.length))
      : 1
    const h = maxLines * NODE_H + Math.max(0, maxLines - 1) * SUB_ROW_GAP
    genBandTop[g] = yAcc
    genBandHeight[g] = h
    yAcc += h
    if (g < maxGen) yAcc += INTER_GEN_GAP
  }
  const canvasH = yAcc + PAD

  // Generation band metadata for labels
  const genBands = {}
  for (let g = minGen; g <= maxGen; g++) {
    const genNodes = byGen[g] || []
    const years = genNodes
      .map((n) => n.birth_year)
      .filter((y) => y != null && Number.isFinite(Number(y)))
      .map(Number)
    const minYear = years.length ? Math.min(...years) : null
    const decade = minYear != null ? Math.floor(minYear / 10) * 10 + 's' : null
    genBands[g] = {
      top: genBandTop[g],
      height: genBandHeight[g],
      decade,
      minYear,
      genIndex: g - minGen + 1, // 1-based label
    }
  }

  const positions = {}
  const laneGapBands = []
  for (let i = 0; i < columnLayout.length - 1; i++) {
    const gapX = columnLayout[i].start + columnLayout[i].maxW
    for (let g = minGen; g <= maxGen; g++) {
      const top = genBandTop[g]
      const bandH = genBandHeight[g]
      laneGapBands.push({
        x: gapX,
        y: top + 4,
        width: laneGap,
        height: Math.max(8, bandH - 8),
      })
    }
  }

  function x0ForLine(kind, col, lineCardCount) {
    const lineW = rowWidthForIds(lineCardCount)
    if (!col) return PAD + LABEL_W
    if (kind === 'left') return col.start
    if (kind === 'center') return col.start + (col.maxW - lineW) / 2
    return col.start + col.maxW - lineW
  }

  for (let g = minGen; g <= maxGen; g++) {
    const { left, center, right, farRight, extraRight } = rowLanes[g]
    const segments = nonEmptyLanesTagged(left, center, right, farRight, extraRight)
    const baseY = genBandTop[g]
    for (const seg of segments) {
      const col = columnLayout.find((c) => c.kind === seg.kind)
      // Group sibling units onto the same sub-row
      const groups = groupUnitsByRow(seg.units, edges)
      let subY = baseY
      for (const group of groups) {
        // All units in this group share the same Y (siblings side-by-side)
        // Reorder so ex-spouse singles appear before the pair they connect to:
        //   [Patricia 💔 Robert ♥ Linda] instead of [Robert ♥ Linda … Patricia]
        const orderedGroup = reorderGroupForExSpouse(group, edges, nodes)
        const rowIds = orderedGroup.flatMap((u) => u.ids)
        const x0 = x0ForLine(seg.kind, col, rowIds.length)
        rowIds.forEach((mid, j) => {
          const id = sid(mid)
          const x = x0 + j * (NODE_W + GAP_X)
          positions[id] = {
            x,
            y: subY,
            cx: x + NODE_W / 2,
            cy: subY + NODE_H / 2,
          }
        })
        subY += NODE_H + SUB_ROW_GAP
      }
    }
  }

  return {
    positions,
    canvas: { width: canvasW, height: canvasH },
    lineage,
    surnameA,
    surnameB,
    clusterLegend,
    memorialClusterStyle,
    otherSurnameKey,
    nodeSize: { w: NODE_W, h: NODE_H },
    orderedIds: nodes.map((n) => sid(n.memorial_id)),
    minGen,
    maxGen,
    laneGapBands,
    genBands,
    labelAreaX: PAD,
    labelAreaW: LABEL_W,
  }
}

export function isCrossFamilySpouseEdge(e, lineageMap, nodes, memorialClusterStyle) {
  if (!isSpouseType(e.type)) return false
  const byCluster = isDistinctClusterPair(memorialClusterStyle, e.source, e.target)
  if (byCluster !== null) return byCluster
  const nodeById = new Map()
  if (nodes) {
    for (const n of nodes) nodeById.set(n.memorial_id, n.name)
  }
  return isDistinctFamilyPair(
    lineageMap,
    e.source,
    e.target,
    nodeById.get(e.source),
    nodeById.get(e.target)
  )
}
