/** Reuse manual placement only for the same complete graph and safe geometry. */
export function resolveTreePositions(layout, overrides = {}) {
  const base = layout?.positions || {}
  const ids = Object.keys(base)
  if (!ids.length || !Object.keys(overrides).length) return base
  // Adding/removing people changes the space needed by the automatic layout.
  if (ids.length !== Object.keys(overrides).length || ids.some(id => !overrides[id])) return base
  const { w = 90, h = 148 } = layout.nodeSize || {}
  const merged = {}
  for (const id of ids) {
    const { x, y } = overrides[id]
    if (!Number.isFinite(x) || !Number.isFinite(y)) return base
    merged[id] = { ...base[id], x, y, cx: x + w / 2, cy: y + h / 2 }
  }
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      const a = merged[ids[i]], b = merged[ids[j]]
      if (Math.abs(a.x - b.x) < w + 20 && Math.abs(a.y - b.y) < h + 12) return base
      // Preserve generation membership even for legacy saved positions.
      if (base[ids[i]].y === base[ids[j]].y && Math.abs(a.y - b.y) > 1) return base
    }
  }
  return merged
}
