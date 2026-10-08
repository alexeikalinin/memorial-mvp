import test from 'node:test'
import assert from 'node:assert/strict'
import { tourTooltipPosition, tourPointerPosition } from '../src/utils/tourLayout.js'
const size = { width: 340, height: 240 }
const rect = (left, top, width = 130, height = 40) => ({ left, top, width, height, right: left + width, bottom: top + height })
test('tooltip fits narrow mobile, desktop and short viewports at every edge', () => {
 for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 800 }, { width: 320, height: 380 }]) {
  for (const r of [rect(0, 20), rect(viewport.width - 140, 30), rect(20, viewport.height - 50), rect(20, -30), null]) {
   const p = tourTooltipPosition(r, viewport, size)
   assert.ok(p.left >= 16 && p.top >= 16)
   assert.ok(p.left + Math.min(size.width, viewport.width - 32) <= viewport.width - 16)
   assert.ok(p.top + size.height <= viewport.height - 16)
  }
 }
})
test('places tooltip below, or above when the target is near the bottom', () => {
 assert.equal(tourTooltipPosition(rect(300, 100), { width: 1000, height: 800 }, size).top, 162)
 assert.equal(tourTooltipPosition(rect(300, 700), { width: 1000, height: 800 }, size).top, 438)
})
test('cursor points to the checkbox rather than the center of its full label', () => {
 assert.deepEqual(tourPointerPosition(rect(500, 300, 180), rect(500, 310, 14, 14)), { x: 507, y: 317 })
})
