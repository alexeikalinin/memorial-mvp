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

const NODE_W = 118
const NODE_H = 132
const GAP_X = 48
/** Разрыв между «полосами» линии A / центр (пересечение) / линия B — больше = семьи визуально дальше */
const LINEAGE_LANE_GAP = 288
export const ROW_H = 176
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
 * Пары супругов, группы полных сиблингов (один ряд), пары по ребру sibling/half_sibling, одиночки.
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
    let bucket = left
    if ((hasA && hasB) || (hasA && hasC) || (hasB && hasC) || hasD && (hasA || hasB || hasC)) bucket = center
    else if (hasD && !hasA && !hasB && !hasC) bucket = extraRight
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

function segmentWidthUnits(units) {
  let n = 0
  for (const u of units) n += u.ids.length
  return rowWidthForIds(n)
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
 * @returns {{ positions: Record<string, {x,y,cx,cy}>, canvas: {width,height}, lineage, surnameA, surnameB, orderedIds: string[], minGen, maxGen }}
 */
export function buildGenerationLayout(graphData) {
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
    const units = buildUnitsInGeneration(rowNodes, edges, lineage, nodes)
    const hasAInRow = rowNodes.some((n) => lineage[n.memorial_id] === 'A')
    const hasBInRow = rowNodes.some((n) => lineage[n.memorial_id] === 'B')
    const hasCInRow = rowNodes.some((n) => lineage[n.memorial_id] === 'C')
    const hasDInRow = rowNodes.some((n) => lineage[n.memorial_id] === 'D')
    const { left, center, right, farRight, extraRight } = clusterUnitsIntoLanes(
      units,
      lineage,
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
    maxLeftW = Math.max(maxLeftW, segmentWidthUnits(left))
    maxCenterW = Math.max(maxCenterW, segmentWidthUnits(center))
    maxRightW = Math.max(maxRightW, segmentWidthUnits(right))
    maxFarRightW = Math.max(maxFarRightW, segmentWidthUnits(farRight))
    maxExtraRightW = Math.max(maxExtraRightW, segmentWidthUnits(extraRight))
  }

  /** Фиксированные колонки: без центрирования ряда — иначе строки только Kelly и только Anderson накладываются по X. */
  const columnLayout = []
  let xCursor = PAD + LABEL_W
  if (hasAnyLeft) {
    columnLayout.push({ kind: 'left', start: xCursor, maxW: maxLeftW })
    xCursor += maxLeftW
    if (hasAnyCenter || hasAnyRight) xCursor += LINEAGE_LANE_GAP
  }
  if (hasAnyCenter) {
    columnLayout.push({ kind: 'center', start: xCursor, maxW: maxCenterW })
    xCursor += maxCenterW
    if (hasAnyRight) xCursor += LINEAGE_LANE_GAP
  }
  if (hasAnyRight) {
    columnLayout.push({ kind: 'right', start: xCursor, maxW: maxRightW })
    xCursor += maxRightW
    if (hasAnyFarRight) xCursor += LINEAGE_LANE_GAP
  }
  if (hasAnyFarRight) {
    columnLayout.push({ kind: 'farRight', start: xCursor, maxW: maxFarRightW })
    xCursor += maxFarRightW
    if (hasAnyExtraRight) xCursor += LINEAGE_LANE_GAP
  }
  if (hasAnyExtraRight) {
    columnLayout.push({ kind: 'extraRight', start: xCursor, maxW: maxExtraRightW })
    xCursor += maxExtraRightW
  }

  const canvasW = Math.max(720, xCursor + PAD)
  const numRows = maxGen - minGen + 1
  const canvasH = PAD * 2 + numRows * ROW_H

  const positions = {}
  const laneGapBands = []
  for (let i = 0; i < columnLayout.length - 1; i++) {
    const gapX = columnLayout[i].start + columnLayout[i].maxW
    for (let g = minGen; g <= maxGen; g++) {
      const y = PAD + (g - minGen) * ROW_H
      laneGapBands.push({
        x: gapX,
        y: y + 4,
        width: LINEAGE_LANE_GAP,
        height: ROW_H - 8,
      })
    }
  }

  function startXForSegment(kind, units) {
    const col = columnLayout.find((c) => c.kind === kind)
    if (!col) return PAD + LABEL_W
    const segW = segmentWidthUnits(units)
    if (kind === 'left') return col.start
    if (kind === 'center') return col.start + (col.maxW - segW) / 2
    return col.start + col.maxW - segW
  }

  for (let g = minGen; g <= maxGen; g++) {
    const { left, center, right, farRight, extraRight } = rowLanes[g]
    const segments = nonEmptyLanesTagged(left, center, right, farRight, extraRight)
    const y = PAD + (g - minGen) * ROW_H
    for (const seg of segments) {
      let x = startXForSegment(seg.kind, seg.units)
      const idsInLane = []
      for (const u of seg.units) idsInLane.push(...u.ids)
      for (let j = 0; j < idsInLane.length; j++) {
        const mid = idsInLane[j]
        const id = sid(mid)
        positions[id] = {
          x,
          y,
          cx: x + NODE_W / 2,
          cy: y + NODE_H / 2,
        }
        if (j < idsInLane.length - 1) x += NODE_W + GAP_X
        else x += NODE_W
      }
    }
  }

  const genToMinY = {}
  for (const n of nodes) {
    const id = sid(n.memorial_id)
    const p = positions[id]
    if (!p) continue
    const g = normalizeGenerationValue(n.generation)
    if (genToMinY[g] === undefined || p.y < genToMinY[g]) genToMinY[g] = p.y
  }
  for (const n of nodes) {
    const id = sid(n.memorial_id)
    const p = positions[id]
    if (!p) continue
    const g = normalizeGenerationValue(n.generation)
    const y = genToMinY[g]
    if (y !== undefined) {
      p.y = y
      p.cy = y + NODE_H / 2
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
