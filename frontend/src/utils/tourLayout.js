const clamp = (value, min, max) => Math.min(Math.max(value, min), Math.max(min, max))

/** Viewport coordinates, measured after scrolling; never position outside the viewport. */
export function tourTooltipPosition(rect, viewport, size) {
  const margin = 16
  const gap = 22
  const width = Math.min(size.width, viewport.width - margin * 2)
  const height = Math.min(size.height, viewport.height - margin * 2)
  if (!rect) return { left: (viewport.width - width) / 2, top: (viewport.height - height) / 2 }
  const centered = clamp(rect.left + rect.width / 2 - width / 2, margin, viewport.width - margin - width)
  const candidates = [
    { left: centered, top: rect.bottom + gap },
    { left: centered, top: rect.top - gap - height },
    { left: rect.right + gap, top: clamp(rect.top, margin, viewport.height - margin - height) },
    { left: rect.left - gap - width, top: clamp(rect.top, margin, viewport.height - margin - height) },
  ]
  const fitting = candidates.find(p => p.left >= margin && p.left + width <= viewport.width - margin && p.top >= margin && p.top + height <= viewport.height - margin)
  if (fitting) return fitting
  // On very short screens, use the side with more room and keep navigation reachable.
  return { left: centered, top: clamp(rect.top > viewport.height / 2 ? rect.top - gap - height : rect.bottom + gap, margin, viewport.height - margin - height) }
}

export function tourPointerPosition(rect, pointerRect = rect) {
  return { x: pointerRect.left + pointerRect.width / 2, y: pointerRect.top + pointerRect.height / 2 }
}
