/**
 * Раскладка полного графа по горизонтальным «этажам» поколений + эвристика двух линий (фамилии).
 * Использует поля generation / edges из GET /family/memorials/:id/full-tree
 */

const sid = (id) => String(id)

const NODE_W = 118
const NODE_H = 132
const GAP_X = 36
/** Разрыв между «полосами» линии A / центр (пересечение) / линия B */
const LINEAGE_LANE_GAP = 152
const ROW_H = 176
const PAD = 48
const LABEL_W = 120

function surnameOf(name) {
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

/** Две самые частые фамилии → линия A и B, остальные N */
export function assignLineages(nodes) {
  const counts = {}
  for (const n of nodes) {
    const s = surnameOf(n.name)
    if (s) counts[s] = (counts[s] || 0) + 1
  }
  const top = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map((e) => e[0])
  const [aSurname, bSurname] = [top[0] || '', top[1] || '']
  const lineage = {}
  for (const n of nodes) {
    const s = surnameOf(n.name)
    if (aSurname && s === aSurname) lineage[n.memorial_id] = 'A'
    else if (bSurname && s === bSurname) lineage[n.memorial_id] = 'B'
    else lineage[n.memorial_id] = 'N'
  }
  return { lineage, surnameA: aSurname, surnameB: bSurname }
}

function isSpouseType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'spouse' || u === 'partner' || u === 'ex_spouse'
}

function unitSortKey(memorialId, lineageMap) {
  const L = lineageMap[memorialId] || 'N'
  if (L === 'A') return 0
  if (L === 'N') return 1
  if (L === 'B') return 2
  return 1
}

/**
 * Пары супругов + одиночки в одном поколении (порядок A → N → B внутри «полосы»).
 */
function buildUnitsInGeneration(genNodes, edges, lineageMap) {
  const ids = genNodes.map((n) => sid(n.memorial_id))
  const idSet = new Set(ids)
  const paired = new Set()
  const units = []

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
 * Раскидать юниты по трём полосам: левая линия (A), центр (пересечение A+B и нейтральные между линиями), правая (B).
 * Сохраняет порядок появления юнитов в исходном списке.
 */
function clusterUnitsIntoLanes(units, lineageMap, hasAInRow, hasBInRow) {
  const left = []
  const center = []
  const right = []
  for (const u of units) {
    const Ls = u.ids.map((id) => lineageMap[id] || 'N')
    const hasA = Ls.includes('A')
    const hasB = Ls.includes('B')
    let bucket = left
    if (hasA && hasB) bucket = center
    else if (hasB && !hasA) bucket = right
    else if (hasA && !hasB) bucket = left
    else {
      if (hasAInRow && hasBInRow) bucket = center
      else if (hasBInRow && !hasAInRow) bucket = right
      else bucket = left
    }
    bucket.push(u)
  }
  return { left, center, right }
}

function segmentWidthUnits(units) {
  let n = 0
  for (const u of units) n += u.ids.length
  return rowWidthForIds(n)
}

/** Непустые полосы слева направо: [A…], [центр], [B…] */
function nonEmptyLanes(left, center, right) {
  const out = []
  if (left.length) out.push(left)
  if (center.length) out.push(center)
  if (right.length) out.push(right)
  return out
}

function rowWidthFromLanes(left, center, right) {
  const lanes = nonEmptyLanes(left, center, right)
  if (!lanes.length) return 0
  let w = 0
  for (let i = 0; i < lanes.length; i++) {
    if (i > 0) w += LINEAGE_LANE_GAP
    w += segmentWidthUnits(lanes[i])
  }
  return w
}

/**
 * @returns {{ positions: Record<string, {x,y,cx,cy}>, canvas: {width,height}, lineage, surnameA, surnameB, orderedIds: string[], minGen, maxGen }}
 */
export function buildGenerationLayout(graphData) {
  const nodes = graphData?.nodes || []
  const edges = graphData?.edges || []
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
    }
  }

  const { lineage, surnameA, surnameB } = assignLineages(nodes)
  const byGen = {}
  let minGen = Infinity
  let maxGen = -Infinity
  for (const n of nodes) {
    const g = n.generation
    minGen = Math.min(minGen, g)
    maxGen = Math.max(maxGen, g)
    if (!byGen[g]) byGen[g] = []
    byGen[g].push(n)
  }

  const rowLanes = {}
  let maxRowWidth = 0
  for (let g = minGen; g <= maxGen; g++) {
    const rowNodes = byGen[g] || []
    const units = buildUnitsInGeneration(rowNodes, edges, lineage)
    const hasAInRow = rowNodes.some((n) => lineage[n.memorial_id] === 'A')
    const hasBInRow = rowNodes.some((n) => lineage[n.memorial_id] === 'B')
    const { left, center, right } = clusterUnitsIntoLanes(units, lineage, hasAInRow, hasBInRow)
    rowLanes[g] = { left, center, right }
    maxRowWidth = Math.max(maxRowWidth, rowWidthFromLanes(left, center, right))
  }

  const canvasW = Math.max(720, PAD * 2 + LABEL_W + maxRowWidth)
  const numRows = maxGen - minGen + 1
  const canvasH = PAD * 2 + numRows * ROW_H

  const positions = {}
  /** Полупрозрачные полосы между кластерами A | центр | B (для читаемости) */
  const laneGapBands = []
  for (let g = minGen; g <= maxGen; g++) {
    const { left, center, right } = rowLanes[g]
    const lanes = nonEmptyLanes(left, center, right)
    const rowW = rowWidthFromLanes(left, center, right)
    const startX = PAD + LABEL_W + (canvasW - PAD * 2 - LABEL_W - rowW) / 2
    const y = PAD + (g - minGen) * ROW_H
    let x = startX
    for (let li = 0; li < lanes.length; li++) {
      if (li > 0) {
        laneGapBands.push({
          x,
          y: y + 4,
          width: LINEAGE_LANE_GAP,
          height: ROW_H - 8,
        })
        x += LINEAGE_LANE_GAP
      }
      const laneUnits = lanes[li]
      const idsInLane = []
      for (const u of laneUnits) idsInLane.push(...u.ids)
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

  return {
    positions,
    canvas: { width: canvasW, height: canvasH },
    lineage,
    surnameA,
    surnameB,
    nodeSize: { w: NODE_W, h: NODE_H },
    orderedIds: nodes.map((n) => sid(n.memorial_id)),
    minGen,
    maxGen,
    laneGapBands,
  }
}

export function isCrossFamilySpouseEdge(e, lineageMap) {
  if (!isSpouseType(e.type)) return false
  const a = lineageMap[e.source]
  const b = lineageMap[e.target]
  if (!a || !b) return false
  if (a === 'N' || b === 'N') return false
  return a !== b
}
