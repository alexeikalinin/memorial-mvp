import { useState, useEffect, useRef, useCallback } from 'react'
import { familyAPI } from '../api/client'
import ApiMediaImage from './ApiMediaImage'
import './FamilyNetwork.css'

const COLS = 3          // max clusters per row in the grid
const ISLAND_W = 260    // island card width  (px, logical)
const ISLAND_H = 220    // island card height (px, logical)
const GAP_X = 120       // horizontal gap between islands
const GAP_Y = 100       // vertical gap between islands

function FamilyNetwork({ memorialId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeBridge, setActiveBridge] = useState(null)  // bridge object or null
  const svgRef = useRef(null)

  useEffect(() => {
    setLoading(true)
    familyAPI.getNetworkClusters(memorialId)
      .then(r => setData(r.data))
      .catch(() => setError('Failed to load network'))
      .finally(() => setLoading(false))
  }, [memorialId])

  // Map cluster_id → grid position {col, row}
  const gridPos = useCallback((clusters) => {
    const pos = {}
    clusters.forEach((cl, idx) => {
      pos[cl.cluster_id] = { col: idx % COLS, row: Math.floor(idx / COLS) }
    })
    return pos
  }, [])

  // Island centre in SVG coordinates
  const islandCenter = (pos) => ({
    x: pos.col * (ISLAND_W + GAP_X) + ISLAND_W / 2,
    y: pos.row * (ISLAND_H + GAP_Y) + ISLAND_H / 2,
  })

  if (loading) return <div className="fn-loading">Loading network…</div>
  if (error)   return <div className="fn-error">{error}</div>
  if (!data || data.clusters.length === 0) return <div className="fn-empty">No family network data</div>

  const { clusters, bridges, focal_cluster_id } = data
  const pos = gridPos(clusters)

  const rows = Math.ceil(clusters.length / COLS)
  const svgW = Math.min(clusters.length, COLS) * (ISLAND_W + GAP_X) - GAP_X + 40
  const svgH = rows * (ISLAND_H + GAP_Y) - GAP_Y + 40

  return (
    <div className="fn-root">
      <p className="fn-subtitle">
        {clusters.length} family {clusters.length === 1 ? 'cluster' : 'clusters'} ·{' '}
        {bridges.length} cross-family {bridges.length === 1 ? 'connection' : 'connections'}
      </p>

      <div className="fn-canvas-wrap">
        {/* SVG layer — bridge lines only */}
        <svg
          ref={svgRef}
          className="fn-svg"
          viewBox={`0 0 ${svgW} ${svgH}`}
          style={{ width: svgW, height: svgH }}
        >
          <defs>
            {clusters.map(cl => (
              <marker
                key={cl.cluster_id}
                id={`arrow-${cl.cluster_id}`}
                markerWidth="8" markerHeight="8"
                refX="6" refY="3"
                orient="auto"
              >
                <path d="M0,0 L0,6 L8,3 z" fill={cl.color} />
              </marker>
            ))}
          </defs>

          {bridges.map((br, i) => {
            const pa = pos[br.source_cluster_id]
            const pb = pos[br.target_cluster_id]
            if (!pa || !pb) return null
            const ca = islandCenter(pa)
            const cb = islandCenter(pb)
            const mx = (ca.x + cb.x) / 2
            const my = (ca.y + cb.y) / 2
            const dx = cb.x - ca.x
            const dy = cb.y - ca.y
            const len = Math.sqrt(dx * dx + dy * dy) || 1
            // perpendicular control point (gentle arc)
            const cpx = mx - (dy / len) * 40
            const cpy = my + (dx / len) * 40
            const isActive = activeBridge === br
            const clA = clusters.find(c => c.cluster_id === br.source_cluster_id)
            return (
              <g key={i} onClick={() => setActiveBridge(isActive ? null : br)} className="fn-bridge-g">
                {/* invisible thick hit area */}
                <path
                  d={`M${ca.x},${ca.y} Q${cpx},${cpy} ${cb.x},${cb.y}`}
                  fill="none" stroke="transparent" strokeWidth={16}
                  style={{ cursor: 'pointer' }}
                />
                <path
                  d={`M${ca.x},${ca.y} Q${cpx},${cpy} ${cb.x},${cb.y}`}
                  fill="none"
                  stroke={isActive ? '#f0a040' : (clA?.color || '#888')}
                  strokeWidth={isActive ? 3 : 2}
                  strokeDasharray={isActive ? '' : '8 5'}
                  opacity={isActive ? 1 : 0.65}
                  style={{ cursor: 'pointer', transition: 'stroke 0.2s, stroke-width 0.2s' }}
                />
                {/* label at midpoint */}
                <text
                  x={cpx} y={cpy - 10}
                  textAnchor="middle"
                  className="fn-bridge-label"
                  fill={isActive ? '#f0a040' : '#bbb'}
                  fontSize="10"
                >
                  {br.label.length > 36 ? br.label.slice(0, 35) + '…' : br.label}
                </text>
              </g>
            )
          })}
        </svg>

        {/* HTML island cards positioned over the SVG */}
        <div className="fn-islands" style={{ width: svgW, height: svgH }}>
          {clusters.map(cl => {
            const p = pos[cl.cluster_id]
            const isFocal = cl.cluster_id === focal_cluster_id
            const top  = p.row * (ISLAND_H + GAP_Y)
            const left = p.col * (ISLAND_W + GAP_X)
            const preview = cl.members.slice(0, 6)
            return (
              <div
                key={cl.cluster_id}
                className={`fn-island ${isFocal ? 'fn-island--focal' : ''}`}
                style={{
                  top, left,
                  width: ISLAND_W,
                  height: ISLAND_H,
                  borderColor: cl.color,
                  boxShadow: isFocal ? `0 0 0 2px ${cl.color}44, 0 4px 20px ${cl.color}33` : undefined,
                }}
              >
                <div className="fn-island-header" style={{ background: cl.color + '22' }}>
                  <span className="fn-island-dot" style={{ background: cl.color }} />
                  <span className="fn-island-label">{cl.label}</span>
                  <span className="fn-island-count">{cl.members.length}</span>
                </div>
                <div className="fn-island-avatars">
                  {preview.map(m => (
                    <div key={m.memorial_id} className={`fn-avatar-wrap ${m.is_alive ? 'fn-avatar--alive' : ''}`} title={m.name}>
                      {m.cover_photo_id ? (
                        <ApiMediaImage
                          mediaId={m.cover_photo_id}
                          alt={m.name}
                          className="fn-avatar-img"
                          thumbnail="small"
                        />
                      ) : (
                        <div className="fn-avatar-placeholder" style={{ background: cl.color + '44' }}>
                          {m.name.charAt(0)}
                        </div>
                      )}
                      {m.is_alive && <span className="fn-alive-dot" title="Living" />}
                    </div>
                  ))}
                  {cl.members.length > 6 && (
                    <div className="fn-avatar-more">+{cl.members.length - 6}</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Active bridge detail panel */}
      {activeBridge && (
        <div className="fn-bridge-detail">
          <button className="fn-bridge-close" onClick={() => setActiveBridge(null)}>✕</button>
          <div className="fn-bridge-detail-people">
            <span className="fn-bd-name">{activeBridge.source_name}</span>
            <span className="fn-bd-arrow">⟷</span>
            <span className="fn-bd-name">{activeBridge.target_name}</span>
          </div>
          <p className="fn-bd-label">{activeBridge.label}</p>
        </div>
      )}

      {/* Legend */}
      <div className="fn-legend">
        {clusters.map(cl => (
          <span key={cl.cluster_id} className="fn-legend-item">
            <span className="fn-legend-dot" style={{ background: cl.color }} />
            {cl.label}
          </span>
        ))}
      </div>
    </div>
  )
}

export default FamilyNetwork
