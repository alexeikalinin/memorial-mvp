/**
 * Ортогональные линии для режима «поколения»: супруги — общая горизонталь,
 * от середины — ствол вниз и разветвление к детям (без «паутины» от каждого родителя к каждому ребёнку).
 *
 * Финализация: дедуп одинаковой геометрии; слияние коллинеарных отрезков на одной оси
 * (перекрытие/касание по Y или X), чтобы не оставалось лишних наложений от прежних проходов.
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

/** Допуск для сравнения координат и слияния интервалов (px). */
const COORD_EPS = 1.15

function normalizedSegmentKey(ln) {
  const x1 = Math.round(ln.x1 * 10) / 10
  const y1 = Math.round(ln.y1 * 10) / 10
  const x2 = Math.round(ln.x2 * 10) / 10
  const y2 = Math.round(ln.y2 * 10) / 10
  const p1 = `${x1},${y1}`
  const p2 = `${x2},${y2}`
  return p1 < p2 ? `${p1}|${p2}` : `${p2}|${p1}`
}

/** Один отрезок на геометрию (без учёта stroke — убирает полные дубли от прошлых правок). */
function dedupeGeometryOnly(lines) {
  const seen = new Set()
  const out = []
  for (const ln of lines) {
    const k = normalizedSegmentKey(ln)
    if (seen.has(k)) continue
    seen.add(k)
    out.push(ln)
  }
  return out
}

function pickStrongerLine(a, b) {
  const wa = a.strokeWidth ?? 1.5
  const wb = b.strokeWidth ?? 1.5
  if (wb > wa + 0.05) return b
  if (wa > wb + 0.05) return a
  if (a.strokeDasharray && !b.strokeDasharray) return b
  if (b.strokeDasharray && !a.strokeDasharray) return a
  return a
}

/**
 * Вертикали на одном X (бакет 0.1px): пересекающиеся или касающиеся по Y — один отрезок.
 */
function mergeVerticalCollinear(lines) {
  const items = []
  for (const ln of lines) {
    const dx = Math.abs(ln.x1 - ln.x2)
    const dy = Math.abs(ln.y1 - ln.y2)
    if (dx >= COORD_EPS || dy < COORD_EPS) continue
    const x = (ln.x1 + ln.x2) / 2
    items.push({
      xb: Math.round(x * 10) / 10,
      yLo: Math.min(ln.y1, ln.y2),
      yHi: Math.max(ln.y1, ln.y2),
      ln,
    })
  }
  if (!items.length) return lines

  const byX = new Map()
  for (const it of items) {
    if (!byX.has(it.xb)) byX.set(it.xb, [])
    byX.get(it.xb).push(it)
  }

  const merged = []
  for (const [, group] of byX) {
    group.sort((a, b) => a.yLo - b.yLo)
    let cur = { yLo: group[0].yLo, yHi: group[0].yHi, ln: group[0].ln, xb: group[0].xb }
    for (let i = 1; i < group.length; i++) {
      const iv = group[i]
      if (iv.yLo <= cur.yHi + COORD_EPS) {
        cur.yHi = Math.max(cur.yHi, iv.yHi)
        cur.ln = pickStrongerLine(cur.ln, iv.ln)
      } else {
        merged.push({
          ...cur.ln,
          x1: cur.xb,
          y1: cur.yLo,
          x2: cur.xb,
          y2: cur.yHi,
        })
        cur = { yLo: iv.yLo, yHi: iv.yHi, ln: iv.ln, xb: iv.xb }
      }
    }
    merged.push({
      ...cur.ln,
      x1: cur.xb,
      y1: cur.yLo,
      x2: cur.xb,
      y2: cur.yHi,
    })
  }

  const vertKeys = new Set(items.map((it) => normalizedSegmentKey(it.ln)))
  const rest = lines.filter((ln) => !vertKeys.has(normalizedSegmentKey(ln)))
  return [...merged, ...rest]
}

/**
 * Горизонтали на одном Y: пересечение по X — один отрезок.
 */
function mergeHorizontalCollinear(lines) {
  const items = []
  for (const ln of lines) {
    const dx = Math.abs(ln.x1 - ln.x2)
    const dy = Math.abs(ln.y1 - ln.y2)
    if (dy >= COORD_EPS || dx < COORD_EPS) continue
    const y = (ln.y1 + ln.y2) / 2
    items.push({
      yb: Math.round(y * 10) / 10,
      xLo: Math.min(ln.x1, ln.x2),
      xHi: Math.max(ln.x1, ln.x2),
      ln,
    })
  }
  if (!items.length) return lines

  const byY = new Map()
  for (const it of items) {
    if (!byY.has(it.yb)) byY.set(it.yb, [])
    byY.get(it.yb).push(it)
  }

  const merged = []
  for (const [, group] of byY) {
    group.sort((a, b) => a.xLo - b.xLo)
    let cur = { xLo: group[0].xLo, xHi: group[0].xHi, ln: group[0].ln, yb: group[0].yb }
    for (let i = 1; i < group.length; i++) {
      const iv = group[i]
      if (iv.xLo <= cur.xHi + COORD_EPS) {
        cur.xHi = Math.max(cur.xHi, iv.xHi)
        cur.ln = pickStrongerLine(cur.ln, iv.ln)
      } else {
        merged.push({
          ...cur.ln,
          x1: cur.xLo,
          y1: cur.yb,
          x2: cur.xHi,
          y2: cur.yb,
        })
        cur = { xLo: iv.xLo, xHi: iv.xHi, ln: iv.ln, yb: iv.yb }
      }
    }
    merged.push({
      ...cur.ln,
      x1: cur.xLo,
      y1: cur.yb,
      x2: cur.xHi,
      y2: cur.yb,
    })
  }

  const horizKeys = new Set(items.map((it) => normalizedSegmentKey(it.ln)))
  const rest = lines.filter((ln) => !horizKeys.has(normalizedSegmentKey(ln)))
  return [...merged, ...rest]
}

function mergeParallelAxisAligned(lines) {
  let out = dedupeGeometryOnly(lines)
  out = mergeVerticalCollinear(out)
  out = dedupeGeometryOnly(out)
  out = mergeHorizontalCollinear(out)
  out = dedupeGeometryOnly(out)
  return out
}

function finalizeConnectorLines(lines) {
  const out = mergeParallelAxisAligned(lines)
  return out.map((ln, i) => ({ ...ln, key: `ol-${i}` }))
}

/** Дубли рёбер из API (одинаковый source, target, type) — одна логическая связь. */
function dedupeEdgesByEndpointPair(edges) {
  if (!edges?.length) return []
  const seen = new Set()
  const out = []
  for (const e of edges) {
    const src = sid(e.source)
    const tgt = sid(e.target)
    const t = String(e.type || '').toLowerCase()
    const k = `${src}|${tgt}|${t}`
    if (seen.has(k)) continue
    seen.add(k)
    out.push(e)
  }
  return out
}

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

/**
 * Нормализованные рёбра parent → child (по одному направлению).
 *
 * Семантика API (family.py):
 *   PARENT edge: source = memorial_id = ребёнок, target = related = родитель
 *   CHILD  edge: source = memorial_id = родитель, target = related = ребёнок
 */
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
      // PARENT: source=ребёнок, target=родитель
      parent = tgt
      child = src
    } else if (isChildEdgeType(typ)) {
      // CHILD: source=родитель, target=ребёнок
      parent = src
      child = tgt
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
    pairs.push([a, b, String(e.type).toLowerCase()])
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
 * Marriage bar Y = bottom of avatar circle.
 * Avatar height = nw - 10 (square circle: width equals height = NODE_W - 10 = 80px).
 * Placing the bar here keeps it ABOVE the text area (text starts at avatarH + 4)
 * so the horizontal marriage line doesn't overlap with names.
 */
function marriageBarY(nodeY, nw) {
  const avatarH = nw - 10  // avatar is square: width = height
  // +4 for the top offset applied to the avatar div (prevents ring clipping by overflow:hidden)
  return nodeY + 4 + avatarH - 2
}

/**
 * Горизонталь брака только в зазоре между карточками: от правого края левой к левому краю правой.
 * Ствол — из середины зазора (mx). Если по X нет зазора — не схлопывать в точку: отрезок между центрами.
 *
 * Если у супругов разный y (разные подстроки/колонки), раньше y брался только у нижней карточки — линия «висела».
 * Теперь: общая горизонталь на средней высоте между «уровнями» брака на каждой карточке + короткие вертикали к ней.
 */
function marriageBarInGap(pa, pb, nw, nh) {
  const left = pa.x <= pb.x ? pa : pb
  const right = pa.x <= pb.x ? pb : pa
  const yMarL = marriageBarY(left.y, nw)
  const yMarR = marriageBarY(right.y, nw)
  const yMid = (yMarL + yMarR) / 2
  const xRightOfLeft = left.x + nw
  const xLeftOfRight = right.x
  const touch = 1.2
  const stubs = []
  const pushStub = (x, y0, y1) => {
    if (Math.abs(y0 - y1) > 0.5) stubs.push({ x1: x, y1: y0, x2: x, y2: y1 })
  }
  if (xRightOfLeft < xLeftOfRight - 0.5) {
    const xl = xRightOfLeft - touch
    const xr = xLeftOfRight + touch
    const mx = (xRightOfLeft + xLeftOfRight) / 2
    pushStub(xl, yMarL, yMid)
    pushStub(xr, yMarR, yMid)
    return {
      yBar: yMid,
      x1: xl,
      x2: xr,
      mx,
      stubs,
    }
  }
  const mx = (pa.cx + pb.cx) / 2
  const half = Math.max(10, Math.abs(pa.cx - pb.cx) / 2 + 4)
  return { yBar: yMid, x1: mx - half, x2: mx + half, mx, stubs: [] }
}

/** Горизонталь в зазоре между двумя карточками (сиблинги и т.п.) */
function horizontalInGap(pa, pb, nw) {
  const left = pa.x <= pb.x ? pa : pb
  const right = pa.x <= pb.x ? pb : pa
  const x1 = left.x + nw
  const x2 = right.x
  const touch = 1.2
  if (x1 < x2 - 0.5) return { x1: x1 - touch, x2: x2 + touch, mx: (x1 + x2) / 2 }
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
  const nh = nodeSize?.h ?? 160

  const layoutEdges = dedupeEdgesByEndpointPair(
    stripSiblingConflictingParentEdges(edges || [], nodes || [])
  )

  const idToName = new Map()
  for (const n of nodes || []) idToName.set(String(n.memorial_id), n.name)

  const parentEdges = normalizeParentChildEdges(layoutEdges, idSet)
  const childrenOf = buildChildrenMap(parentEdges)
  const spousePairs = spousePairsFromEdges(layoutEdges, idSet, nodes)
  const fullSibKeys = fullSiblingPairKeySet(nodes, layoutEdges, idSet)

  // autoExSet: pairs that should visually represent a prior/ended marriage (💔 or reddish line)
  const _idToDead = new Map()
  const _idToDeathYear = new Map()
  for (const n of nodes || []) {
    _idToDead.set(String(n.memorial_id), !!n.death_year)
    _idToDeathYear.set(String(n.memorial_id), n.death_year || null)
  }
  const _spousePartnersOf = {}
  for (const [a, b] of spousePairs) {
    ;(_spousePartnersOf[a] = _spousePartnersOf[a] || []).push(b)
    ;(_spousePartnersOf[b] = _spousePartnersOf[b] || []).push(a)
  }
  const autoExSet = new Set()
  for (const [personId, partners] of Object.entries(_spousePartnersOf)) {
    if (partners.length < 2) continue
    const anyAlive = partners.some((p) => !_idToDead.get(p))
    if (anyAlive) {
      for (const p of partners) {
        if (_idToDead.get(p)) autoExSet.add(personId < p ? `${personId}|${p}` : `${p}|${personId}`)
      }
    } else {
      const sorted = partners.slice().sort((x, y) =>
        (_idToDeathYear.get(x) || 9999) - (_idToDeathYear.get(y) || 9999)
      )
      for (let i = 0; i < sorted.length - 1; i++) {
        const p = sorted[i]
        autoExSet.add(personId < p ? `${personId}|${p}` : `${p}|${personId}`)
      }
    }
  }
  for (const [a, b, et] of spousePairs) {
    if (et === 'ex_spouse') autoExSet.add(a < b ? `${a}|${b}` : `${b}|${a}`)
  }

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
    const { yBar, x1, x2, stubs = [] } = marriageBarInGap(pa, pb, nw, nh)
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
    const strokeOpts = {
      stroke: cross ? 'rgba(200, 175, 120, 0.95)' : 'rgba(196,168,130,0.78)',
      strokeWidth: cross ? 2.6 : 2,
      strokeDasharray: cross ? '7 5' : undefined,
    }
    for (const s of stubs) {
      addLine(s.x1, s.y1, s.x2, s.y2, strokeOpts)
    }
    addLine(x1, yBar, x2, yBar, strokeOpts)
  }

  // ── 2) Пары родителей — общий ствол к общим детям
  // ex-spouse pairs get a slightly reddish line so lines from different marriages are visually distinct
  for (const [p1, p2, edgeTypePair] of spousePairs) {
    const set1 = childrenOf[p1]
    const set2 = childrenOf[p2]
    if (!set1 || !set2) continue
    const shared = [...set1].filter((c) => set2.has(c))
    if (!shared.length) continue

    const pos1 = positions[p1]
    const pos2 = positions[p2]
    if (!pos1 || !pos2) continue

    const { yBar: ySpouse, mx } = marriageBarInGap(pos1, pos2, nw, nh)

    // Visually distinguish ex-spouse connector lines (reddish/muted) from current marriage (golden)
    const pairKey = p1 < p2 ? `${p1}|${p2}` : `${p2}|${p1}`
    const isPairExSpouse = edgeTypePair === 'ex_spouse' || autoExSet.has(pairKey)
    const lineColor = isPairExSpouse
      ? 'rgba(180,110,100,0.70)'   // warm reddish for ex-spouse lineage
      : 'rgba(196,168,130,0.75)'   // golden for current marriage
    const lineW = 1.8

    const childPts = shared
      .map((c) => positions[c])
      .filter(Boolean)
      .sort((a, b) => a.cx - b.cx)

    if (!childPts.length) continue

    const minChildY = Math.min(...childPts.map((p) => p.y))
    const parentBottom = Math.max(bottomY(p1), bottomY(p2))
    const gapParentsToChildren = minChildY - parentBottom
    const forkMargin = Math.min(
      24,
      Math.max(10, gapParentsToChildren > 4 ? gapParentsToChildren * 0.38 : (ROW_H - nh) * 0.42)
    )
    const yForkCandidate = minChildY - forkMargin
    const yFork =
      yForkCandidate > ySpouse + 2
        ? yForkCandidate
        : (ySpouse + minChildY) / 2

    shared.forEach((c) => coveredPc.add(`${p1}|${c}`))
    shared.forEach((c) => coveredPc.add(`${p2}|${c}`))

    // trunk down from marriage bar midpoint
    addLine(mx, ySpouse, mx, yFork, { stroke: lineColor, strokeWidth: lineW })

    if (childPts.length === 1) {
      const ch = childPts[0]
      if (Math.abs(mx - ch.cx) > 2) {
        addLine(mx, yFork, ch.cx, yFork, { stroke: lineColor, strokeWidth: lineW })
      }
      addLine(ch.cx, yFork, ch.cx, ch.y, { stroke: lineColor, strokeWidth: lineW })
    } else {
      const xMin = childPts[0].cx
      const xMax = childPts[childPts.length - 1].cx
      const xMinExt = Math.min(xMin, mx)
      const xMaxExt = Math.max(xMax, mx)
      addLine(xMinExt, yFork, xMaxExt, yFork, { stroke: lineColor, strokeWidth: lineW })
      for (const ch of childPts) {
        addLine(ch.cx, yFork, ch.cx, ch.y, { stroke: lineColor, strokeWidth: lineW - 0.2 })
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
    const verticalGap = y1 - y0
    // Горизонталь не по середине всего вертикального интервала: иначе линия проходит через
    // промежуточные ряды поколений и пересекает чужие карточки (другая колонка / семья).
    const gapBelowParent = Math.min(
      14,
      Math.max(3, verticalGap > 2 ? verticalGap * 0.14 : (ROW_H - nh) * 0.12)
    )
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

  return { lines: finalizeConnectorLines(lines) }
}

/**
 * Центры «брачной» линии между супругами — для иконки колец (режим поколений).
 * @returns {Array<{ key: string, mx: number, y: number, pairTitle: string, cross: boolean, leftRingStroke: string, rightRingStroke: string }>}
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
  const nh = nodeSize?.h ?? 160
  const layoutEdges = dedupeEdgesByEndpointPair(
    stripSiblingConflictingParentEdges(edges || [], nodes || [])
  )
  const idToName = new Map()
  const idToDead = new Map()
  for (const n of nodes || []) {
    idToName.set(String(n.memorial_id), n.name)
    idToDead.set(String(n.memorial_id), !!n.death_year)
  }
  const spousePairs = spousePairsFromEdges(layoutEdges, idSet, nodes)

  // Build auto-💔 set: pairs where we should show a broken heart even if edge type is 'spouse'.
  // Rule: if person X has 2+ spouses, show 💔 for their "previous" partner:
  //   - If one partner is alive and others are deceased → 💔 for the deceased ones
  //   - If all partners are deceased → 💔 for the one who died EARLIEST (= prior marriage)
  const idToDeathYear = new Map()
  for (const n of nodes || []) idToDeathYear.set(String(n.memorial_id), n.death_year || null)
  const spousePartnersOf = {}  // id → [partner ids]
  for (const [a, b] of spousePairs) {
    ;(spousePartnersOf[a] = spousePartnersOf[a] || []).push(b)
    ;(spousePartnersOf[b] = spousePartnersOf[b] || []).push(a)
  }
  const autoExSet = new Set()  // "min|max" keys for pairs that get 💔
  for (const [personId, partners] of Object.entries(spousePartnersOf)) {
    if (partners.length < 2) continue
    const anyAlive = partners.some((p) => !idToDead.get(p))
    if (anyAlive) {
      // Show 💔 for all deceased partners (the living one is the current spouse)
      for (const p of partners) {
        if (idToDead.get(p)) autoExSet.add(personId < p ? `${personId}|${p}` : `${p}|${personId}`)
      }
    } else {
      // All partners are deceased — show 💔 for all but the one who died LATEST (last marriage)
      const sorted = partners.slice().sort((x, y) => {
        const dx = idToDeathYear.get(x) || 9999
        const dy = idToDeathYear.get(y) || 9999
        return dx - dy  // earliest death first
      })
      for (let i = 0; i < sorted.length - 1; i++) {
        const p = sorted[i]
        autoExSet.add(personId < p ? `${personId}|${p}` : `${p}|${personId}`)
      }
    }
  }

  const markers = []
  for (const [a, b, edgeType] of spousePairs) {
    const pa = positions[a]
    const pb = positions[b]
    if (!pa || !pb) continue
    const horizDist = Math.abs((pa.x + nw / 2) - (pb.x + nw / 2))
    const isExSpouseEdge = edgeType === 'ex_spouse'
    const pairKey = a < b ? `${a}|${b}` : `${b}|${a}`
    const isExSpouse = isExSpouseEdge || autoExSet.has(pairKey)
    // ex_spouse: always show 💔 regardless of distance; regular: only when close
    if (!isExSpouse && horizDist > 3 * (nw + 40)) continue
    if (!isExSpouse && horizDist > 3 * (nw + 40)) continue
    const { yBar, mx } = marriageBarInGap(pa, pb, nw, nh)
    const leftPid = pa.x <= pb.x ? a : b
    const rightPid = pa.x <= pb.x ? b : a
    const na = idToName.get(String(a)) || a
    const nb = idToName.get(String(b)) || b
    markers.push({
      key: `mar-${a}-${b}`,
      mx,
      y: yBar,
      isExSpouse,
      pairTitle: `${na} ↔ ${nb}`,
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
