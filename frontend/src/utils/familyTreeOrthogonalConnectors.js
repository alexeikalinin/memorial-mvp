/**
 * Ортогональные линии для режима «поколения»: супруги — общая горизонталь,
 * от середины — ствол вниз и разветвление к детям (без «паутины» от каждого родителя к каждому ребёнку).
 */

import {
  isDistinctFamilyPair,
  lineageRingStroke,
  isDistinctClusterPair,
  ROW_H,
} from './familyTreeGenerationLayout.js'
import {
  getFullSiblingGroupsForLayout,
  stripSiblingConflictingParentEdges,
} from './familyTreeGenerations.js'

const sid = (id) => String(id)

function isSpouseType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'spouse' || u === 'partner' || u === 'ex_spouse'
}

function isSiblingType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'sibling' || u === 'half_sibling'
}

/** Ключи пар a|b (a<b) для рёбер брат/сестра — между ними не показываем брак и кольца. */
function siblingPairKeySet(edges, idSet) {
  const keys = new Set()
  for (const e of edges || []) {
    if (!isSiblingType(e.type)) continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!idSet.has(a) || !idSet.has(b)) continue
    keys.add(a < b ? `${a}|${b}` : `${b}|${a}`)
  }
  return keys
}

/** Пары с одинаковыми двумя родителями — без колец и без отдельной горизонтали между карточками (как на эскизе). */
function fullSiblingPairKeySet(nodes, edges, idSet) {
  const keys = new Set()
  if (!nodes?.length) return keys
  for (const group of getFullSiblingGroupsForLayout(nodes, edges)) {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        const a = group[i]
        const b = group[j]
        if (!idSet.has(a) || !idSet.has(b)) continue
        keys.add(a < b ? `${a}|${b}` : `${b}|${a}`)
      }
    }
  }
  return keys
}

function isParentEdgeType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'parent' || u === 'adoptive_parent' || u === 'step_parent'
}

function isChildEdgeType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'child' || u === 'adoptive_child' || u === 'step_child'
}

/** Нормализованные рёбра parent → child (по одному направлению). */
export function normalizeParentChildEdges(edges, idSet) {
  const out = []
  const seen = new Set()
  for (const e of edges) {
    const src = sid(e.source)
    const tgt = sid(e.target)
    if (!idSet.has(src) || !idSet.has(tgt)) continue
    const typ = String(e.type || '').toLowerCase()
    let parent
    let child
    if (isParentEdgeType(typ)) {
      parent = src
      child = tgt
    } else if (isChildEdgeType(typ)) {
      parent = tgt
      child = src
    } else continue
    const dedupe = `${parent}|${child}`
    if (seen.has(dedupe)) continue
    seen.add(dedupe)
    out.push({ parent, child })
  }
  return out
}

/**
 * Пары супругов для линий брака (spouse / partner / ex_spouse).
 * Пары, между которыми есть sibling/half_sibling или общие два родителя, отбрасываются — кольца только у супругов.
 */
function spousePairsFromEdges(edges, idSet, nodes) {
  const noRing = new Set([
    ...siblingPairKeySet(edges, idSet),
    ...fullSiblingPairKeySet(nodes, edges, idSet),
  ])
  const pairs = []
  const seen = new Set()
  for (const e of edges || []) {
    if (!isSpouseType(e.type)) continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!idSet.has(a) || !idSet.has(b)) continue
    const key = a < b ? `${a}|${b}` : `${b}|${a}`
    if (noRing.has(key)) continue
    if (seen.has(key)) continue
    seen.add(key)
    pairs.push([a, b])
  }
  return pairs
}

function buildChildrenMap(parentEdges) {
  const childrenOf = {}
  for (const { parent, child } of parentEdges) {
    if (!childrenOf[parent]) childrenOf[parent] = new Set()
    childrenOf[parent].add(child)
  }
  return childrenOf
}

/**
 * Горизонталь брака только в зазоре между карточками: от правого края левой к левому краю правой.
 * Ствол — из середины зазора (mx). Если по X нет зазора — не схлопывать в точку: отрезок между центрами (иначе пропадает половина связи и кольца «висят»).
 */
function marriageBarInGap(pa, pb, nw, nh) {
  const yBar = Math.max(pa.y, pb.y) + nh * 0.82
  const left = pa.x <= pb.x ? pa : pb
  const right = pa.x <= pb.x ? pb : pa
  const xRightOfLeft = left.x + nw
  const xLeftOfRight = right.x
  if (xRightOfLeft < xLeftOfRight - 0.5) {
    const mx = (xRightOfLeft + xLeftOfRight) / 2
    return { yBar, x1: xRightOfLeft, x2: xLeftOfRight, mx }
  }
  const mx = (pa.cx + pb.cx) / 2
  const half = Math.max(10, Math.abs(pa.cx - pb.cx) / 2 + 4)
  return { yBar, x1: mx - half, x2: mx + half, mx }
}

/** Горизонталь в зазоре между двумя карточками (сиблинги и т.п.) */
function horizontalInGap(pa, pb, nw) {
  const left = pa.x <= pb.x ? pa : pb
  const right = pa.x <= pb.x ? pb : pa
  const x1 = left.x + nw
  const x2 = right.x
  if (x1 < x2 - 0.5) return { x1, x2, mx: (x1 + x2) / 2 }
  const mx = (pa.cx + pb.cx) / 2
  return { x1: mx, x2: mx, mx }
}

/**
 * @param {object} params
 * @param {Array} params.edges — raw graph edges
 * @param {Record<string, {x,y,cx,cy}>} params.positions
 * @param {{ w: number, h: number }} params.nodeSize
 * @param {Record<string, string>|undefined} params.lineage — A/B/N кластеры фамилий
 * @param {Array<{ memorial_id:number, name:string }>|undefined} params.nodes — для межсемейных браков A+N и колец
 * @param {Record<number|string, { clusterIndex:number }>|undefined} params.memorialClusterStyle
 * @returns {{ lines: Array<{key:string,x1:number,y1:number,x2:number,y2:number,stroke?:string,strokeWidth?:number,strokeDasharray?:string}> }}
 */
export function buildOrthogonalConnectors({
  edges,
  positions,
  nodeSize,
  lineageMap,
  nodes,
  memorialClusterStyle,
}) {
  const idSet = new Set(Object.keys(positions))
  const nw = nodeSize?.w ?? 118
  const nh = nodeSize?.h ?? 132

  const layoutEdges = stripSiblingConflictingParentEdges(edges || [], nodes || [])

  const idToName = new Map()
  for (const n of nodes || []) idToName.set(String(n.memorial_id), n.name)

  const parentEdges = normalizeParentChildEdges(layoutEdges, idSet)
  const childrenOf = buildChildrenMap(parentEdges)
  const spousePairs = spousePairsFromEdges(layoutEdges, idSet, nodes)
  const fullSibKeys = fullSiblingPairKeySet(nodes, layoutEdges, idSet)

  /** Пары (parent, child), уже нарисованные совместным блоком */
  const coveredPc = new Set()

  const lines = []
  let lineKey = 0
  const addLine = (x1, y1, x2, y2, opts = {}) => {
    if (Math.abs(x1 - x2) < 0.5 && Math.abs(y1 - y2) < 0.5) return
    lines.push({
      key: `ol-${lineKey++}`,
      x1,
      y1,
      x2,
      y2,
      stroke: opts.stroke ?? 'rgba(196,168,130,0.55)',
      strokeWidth: opts.strokeWidth ?? 1.5,
      strokeDasharray: opts.strokeDasharray,
    })
  }

  const bottomY = (pid) => {
    const p = positions[pid]
    if (!p) return 0
    return p.y + nh
  }

  const topY = (pid) => {
    const p = positions[pid]
    if (!p) return 0
    return p.y
  }

  const cx = (pid) => positions[pid]?.cx ?? 0

  // ── 1) Горизонталь между супругами — только в зазоре между карточками (не через центры)
  for (const [a, b] of spousePairs) {
    const pa = positions[a]
    const pb = positions[b]
    if (!pa || !pb) continue
    const { yBar, x1, x2 } = marriageBarInGap(pa, pb, nw, nh)
    const crossCluster = isDistinctClusterPair(memorialClusterStyle, a, b)
    const cross =
      crossCluster !== null
        ? crossCluster
        : isDistinctFamilyPair(
            lineageMap,
            a,
            b,
            idToName.get(String(a)),
            idToName.get(String(b))
          )
    addLine(x1, yBar, x2, yBar, {
      stroke: cross ? 'rgba(200, 175, 120, 0.95)' : 'rgba(196,168,130,0.78)',
      strokeWidth: cross ? 2.6 : 2,
      strokeDasharray: cross ? '7 5' : undefined,
    })
  }

  // ── 2) Пары родителей — общий ствол к общим детям
  for (const [p1, p2] of spousePairs) {
    const set1 = childrenOf[p1]
    const set2 = childrenOf[p2]
    if (!set1 || !set2) continue
    const shared = [...set1].filter((c) => set2.has(c))
    if (!shared.length) continue

    const pos1 = positions[p1]
    const pos2 = positions[p2]
    if (!pos1 || !pos2) continue

    const { yBar: ySpouse, mx } = marriageBarInGap(pos1, pos2, nw, nh)

    const childPts = shared
      .map((c) => positions[c])
      .filter(Boolean)
      .sort((a, b) => a.cx - b.cx)

    if (!childPts.length) continue

    const minChildY = Math.min(...childPts.map((p) => p.y))
    // Горизонталь вилки по середине (брак↔дети) часто попадает в ряд чужой колонки (Rose и т.д.).
    // Ставим y вилки в зазор сразу над верхом детского ряда — как в §3 для parent→child.
    // Вертикаль вилка→ребёнок ≈ forkMargin px; чуть больше — линия читается лучше (не «прилипает» к карточке).
    const forkMargin = Math.min(20, Math.max(12, (ROW_H - nh) * 0.42))
    const yForkCandidate = minChildY - forkMargin
    const yFork =
      yForkCandidate > ySpouse + 2
        ? yForkCandidate
        : (ySpouse + minChildY) / 2

    shared.forEach((c) => coveredPc.add(`${p1}|${c}`))
    shared.forEach((c) => coveredPc.add(`${p2}|${c}`))

    // ствол вниз от середины «брачной» линии
    addLine(mx, ySpouse, mx, yFork, { stroke: 'rgba(196,168,130,0.52)', strokeWidth: 1.5 })

    if (childPts.length === 1) {
      const ch = childPts[0]
      const yTop = ch.y
      if (Math.abs(mx - ch.cx) > 2) {
        addLine(mx, yFork, ch.cx, yFork, { stroke: 'rgba(196,168,130,0.52)', strokeWidth: 1.5 })
      }
      addLine(ch.cx, yFork, ch.cx, yTop, { stroke: 'rgba(196,168,130,0.52)', strokeWidth: 1.5 })
    } else {
      const xMin = childPts[0].cx
      const xMax = childPts[childPts.length - 1].cx
      // Ствол спускается по mx между супругами; вилка по детям [xMin,xMax] может не включать mx
      // (дети в другой колонке / смещены) — тогда вертикаль не встречает горизонталь.
      const xMinExt = Math.min(xMin, mx)
      const xMaxExt = Math.max(xMax, mx)
      addLine(xMinExt, yFork, xMaxExt, yFork, { stroke: 'rgba(196,168,130,0.52)', strokeWidth: 1.5 })
      for (const ch of childPts) {
        addLine(ch.cx, yFork, ch.cx, ch.y, { stroke: 'rgba(196,168,130,0.48)', strokeWidth: 1.4 })
      }
    }
  }

  // ── 3) Оставшиеся parent → child (один родитель в данных, пасынок и т.д.)
  for (const { parent, child } of parentEdges) {
    const key = `${parent}|${child}`
    if (coveredPc.has(key)) continue
    const pp = positions[parent]
    const pc = positions[child]
    if (!pp || !pc) continue

    const y0 = bottomY(parent)
    const y1 = topY(child)
    const x0 = cx(parent)
    const x1 = cx(child)
    // Горизонталь не по середине всего вертикального интервала: иначе линия проходит через
    // промежуточные ряды поколений и пересекает чужие карточки (другая колонка / семья).
    const gapBelowParent = Math.min(8, Math.max(3, (ROW_H - nh) * 0.12))
    const yH =
      y1 > y0 + gapBelowParent ? Math.min(y0 + gapBelowParent, y1 - 0.5) : (y0 + y1) / 2

    if (Math.abs(x0 - x1) < 3) {
      addLine(x0, y0, x1, y1, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
    } else {
      addLine(x0, y0, x0, yH, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
      addLine(x0, yH, x1, yH, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
      addLine(x1, yH, x1, y1, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
    }
  }

  // ── 4) half_sibling и т.п. — тонкая горизонталь; полные сиблинги только через вилку от родителей (без линии между карточками, как на референсе)
  for (const e of layoutEdges) {
    const typ = String(e.type || '').toLowerCase()
    if (typ !== 'sibling' && typ !== 'half_sibling') continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!idSet.has(a) || !idSet.has(b)) continue
    const pairKey = a < b ? `${a}|${b}` : `${b}|${a}`
    if (fullSibKeys.has(pairKey)) continue
    const pa = positions[a]
    const pb = positions[b]
    if (!pa || !pb) continue
    const ySib = Math.max(pa.y, pb.y) + nh * 0.35
    const { x1, x2 } = horizontalInGap(pa, pb, nw)
    addLine(x1, ySib, x2, ySib, {
      stroke: 'rgba(196,168,130,0.55)',
      strokeWidth: 2.2,
      strokeDasharray: '8 5',
    })
  }

  return { lines }
}

/**
 * Центры «брачной» линии между супругами — для иконки колец (режим поколений).
 * @returns {Array<{ key: string, mx: number, y: number, cross: boolean, leftRingStroke: string, rightRingStroke: string }>}
 */
export function getSpouseMarriageMarkers({
  edges,
  positions,
  nodeSize,
  lineageMap,
  nodes,
  memorialClusterStyle,
}) {
  const idSet = new Set(Object.keys(positions))
  const nw = nodeSize?.w ?? 118
  const nh = nodeSize?.h ?? 132
  const layoutEdges = stripSiblingConflictingParentEdges(edges || [], nodes || [])
  const idToName = new Map()
  for (const n of nodes || []) idToName.set(String(n.memorial_id), n.name)
  const spousePairs = spousePairsFromEdges(layoutEdges, idSet, nodes)
  const markers = []
  for (const [a, b] of spousePairs) {
    const pa = positions[a]
    const pb = positions[b]
    if (!pa || !pb) continue
    const { yBar, mx } = marriageBarInGap(pa, pb, nw, nh)
    const leftPid = pa.x <= pb.x ? a : b
    const rightPid = pa.x <= pb.x ? b : a
    markers.push({
      key: `mar-${a}-${b}`,
      mx,
      y: yBar,
      cross: (() => {
        const cx = isDistinctClusterPair(memorialClusterStyle, a, b)
        if (cx !== null) return cx
        return isDistinctFamilyPair(
          lineageMap,
          a,
          b,
          idToName.get(String(a)),
          idToName.get(String(b))
        )
      })(),
      leftRingStroke: lineageRingStroke(
        leftPid,
        lineageMap,
        idToName.get(String(leftPid)),
        memorialClusterStyle
      ),
      rightRingStroke: lineageRingStroke(
        rightPid,
        lineageMap,
        idToName.get(String(rightPid)),
        memorialClusterStyle
      ),
    })
  }
  return markers
}
