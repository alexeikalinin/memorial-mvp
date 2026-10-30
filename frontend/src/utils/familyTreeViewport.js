// Layout zoom rerenders glyphs at their displayed size rather than enlarging a
// GPU texture captured at an earlier fit-to-tree scale. Old browsers keep 2D scale.
export function treeViewportStyle({x, y, scale}, layoutZoom, pixelRatio = 1) {
  const dpr = Number.isFinite(pixelRatio) && pixelRatio > 0 ? pixelRatio : 1
  const tx = Math.round(x * dpr) / dpr, ty = Math.round(y * dpr) / dpr
  return layoutZoom
    ? {left:tx / scale, top:ty / scale, zoom:scale, transform:'none', transformOrigin:'0 0'}
    : {left:0, top:0, transform:`translate(${tx}px, ${ty}px) scale(${scale})`, transformOrigin:'0 0'}
}
