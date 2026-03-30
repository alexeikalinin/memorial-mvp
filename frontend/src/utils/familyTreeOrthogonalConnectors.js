/**
 * Ортогональные линии для режима «поколения»: супруги — общая горизонталь,
 * от середины — ствол вниз и разветвление к детям (без «паутины» от каждого родителя к каждому ребёнку).
 */

const sid = (id) => String(id)

function isSpouseType(t) {
  const u = String(t || '').toLowerCase()
  return u === 'spouse' || u === 'partner' || u === 'ex_spouse'
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

function spousePairsFromEdges(edges, idSet) {
  const pairs = []
  const seen = new Set()
  for (const e of edges) {
    if (!isSpouseType(e.type)) continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!idSet.has(a) || !idSet.has(b)) continue
    const key = a < b ? `${a}|${b}` : `${b}|${a}`
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
 * Ствол — из середины зазора (mx). Если карточки наезжают — линия схлопывается в точку mx.
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
  return { yBar, x1: mx, x2: mx, mx }
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

function lineageVal(lineageMap, id) {
  if (!lineageMap) return 'N'
  return lineageMap[id] ?? lineageMap[Number(id)] ?? 'N'
}

function isCrossLineage(lineageMap, a, b) {
  const x = lineageVal(lineageMap, a)
  const y = lineageVal(lineageMap, b)
  if (x === 'N' || y === 'N') return false
  return x !== y
}

/**
 * @param {object} params
 * @param {Array} params.edges — raw graph edges
 * @param {Record<string, {x,y,cx,cy}>} params.positions
 * @param {{ w: number, h: number }} params.nodeSize
 * @param {Record<string, string>|undefined} params.lineage — для золотого акцента межсемейных браков
 * @returns {{ lines: Array<{key:string,x1:number,y1:number,x2:number,y2:number,stroke?:string,strokeWidth?:number,strokeDasharray?:string}> }}
 */
export function buildOrthogonalConnectors({ edges, positions, nodeSize, lineageMap }) {
  const idSet = new Set(Object.keys(positions))
  const nw = nodeSize?.w ?? 118
  const nh = nodeSize?.h ?? 132

  const parentEdges = normalizeParentChildEdges(edges, idSet)
  const childrenOf = buildChildrenMap(parentEdges)
  const spousePairs = spousePairsFromEdges(edges, idSet)

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
    const cross = isCrossLineage(lineageMap, a, b)
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
    const yFork = (ySpouse + minChildY) / 2

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
      addLine(xMin, yFork, xMax, yFork, { stroke: 'rgba(196,168,130,0.52)', strokeWidth: 1.5 })
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
    const yMid = (y0 + y1) / 2

    if (Math.abs(x0 - x1) < 3) {
      addLine(x0, y0, x1, y1, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
    } else {
      addLine(x0, y0, x0, yMid, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
      addLine(x0, yMid, x1, yMid, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
      addLine(x1, yMid, x1, y1, { stroke: 'rgba(196,168,130,0.45)', strokeWidth: 1.35 })
    }
  }

  // ── 4) Братья / сёстры — тонкая горизонталь (тот же ряд)
  for (const e of edges) {
    const typ = String(e.type || '').toLowerCase()
    if (typ !== 'sibling' && typ !== 'half_sibling') continue
    const a = sid(e.source)
    const b = sid(e.target)
    if (!idSet.has(a) || !idSet.has(b)) continue
    const pa = positions[a]
    const pb = positions[b]
    if (!pa || !pb) continue
    const ySib = Math.max(pa.y, pb.y) + nh * 0.35
    const { x1, x2 } = horizontalInGap(pa, pb, nw)
    addLine(x1, ySib, x2, ySib, {
      stroke: 'rgba(196,168,130,0.3)',
      strokeWidth: 1,
      strokeDasharray: '4 4',
    })
  }

  return { lines }
}
