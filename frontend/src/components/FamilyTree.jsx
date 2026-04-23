import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import { familyAPI, memorialsAPI } from '../api/client'
import ApiMediaImage from './ApiMediaImage'
import calcTree from 'relatives-tree'
import {
  buildGenerationLayout,
  buildSurnameClusterStyles,
  isCrossFamilySpouseEdge,
  neutralSurnameRingStroke,
  surnameOf,
} from '../utils/familyTreeGenerationLayout.js'
import {
  buildOrthogonalConnectors,
  getSpouseMarriageMarkers,
} from '../utils/familyTreeOrthogonalConnectors.js'
import { filterGraphToScope, getFamilyOfNode, FAMILY_CONFIG } from '../utils/familyTreeScope.js'
import './FamilyTree.css'

// ── Grid constants ─────────────────────────────────────────────────
// CELL_W / CELL_H are passed to calcTree as the grid unit size.
// Each node is positioned at: left * HW, top * HH
const CELL_W = 180   // grid cell width  (px)
const CELL_H = 230   // grid cell height (px)
const HW = CELL_W / 2
const HH = CELL_H / 2

// Visual card size (must be ≤ CELL dimensions to avoid overlap)
const NODE_W = 110
const NODE_H = 160

// Centering offset: card is placed at center of cell
const OFF_X = (HW - NODE_W / 2)
const OFF_Y = (HH - NODE_H / 2)

const MIN_SCALE = 0.05
const MAX_SCALE = 3
const VIEW_PAD = 24
/** Показывать иконку брака между супругами при достаточном приближении */
const MIN_SCALE_MARRIAGE_RINGS = 0.82

/** Дробный CSS scale() растягивает текст по субпикселям — округляем масштаб. */
function snapTreeScale(s) {
  const clamped = Math.min(MAX_SCALE, Math.max(MIN_SCALE, s))
  return Math.round(clamped * 1000) / 1000
}

function fitInnerInViewport(canvasEl, innerW, innerH) {
  const cw = canvasEl.offsetWidth
  const ch = canvasEl.offsetHeight
  if (!cw || !ch || !innerW || !innerH) return null
  const sx = (cw - 2 * VIEW_PAD) / innerW
  const sy = (ch - 2 * VIEW_PAD) / innerH
  const scale = snapTreeScale(Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.min(sx, sy))))
  const cx = innerW / 2
  const cy = innerH / 2
  return { x: cw / 2 - cx * scale, y: ch / 2 - cy * scale, scale }
}

/**
 * Fit the viewport to the actual bounding box of rendered nodes.
 * More accurate than fitInnerInViewport when the canvas has top/side padding.
 */
function fitNodesBoundingBox(canvasEl, positions, nodeSize, pad) {
  const _pad = pad ?? VIEW_PAD
  const cw = canvasEl.offsetWidth
  const ch = canvasEl.offsetHeight
  if (!cw || !ch || !positions || !Object.keys(positions).length) return null
  const nw = nodeSize?.w ?? 90
  const nh = nodeSize?.h ?? 148
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const pos of Object.values(positions)) {
    const x = pos.x != null ? pos.x : (pos.cx - nw / 2)
    const y = pos.y != null ? pos.y : (pos.cy - nh / 2)
    if (x < minX) minX = x
    if (y < minY) minY = y
    if (x + nw > maxX) maxX = x + nw
    if (y + nh > maxY) maxY = y + nh
  }
  if (minX === Infinity) return null
  const contentW = maxX - minX
  const contentH = maxY - minY
  const sx = (cw - 2 * _pad) / contentW
  const sy = (ch - 2 * _pad) / contentH
  const scale = snapTreeScale(Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.min(sx, sy))))
  const cx = (minX + maxX) / 2
  const cy = (minY + maxY) / 2
  return { x: cw / 2 - cx * scale, y: ch / 2 - cy * scale, scale }
}

function centerRootInViewport(canvasEl, rootNode) {
  const cw = canvasEl.offsetWidth
  const ch = canvasEl.offsetHeight
  if (!rootNode || !cw) return null
  const rootX = rootNode.left * HW + OFF_X + NODE_W / 2
  const rootY = rootNode.top * HH + OFF_Y + NODE_H / 2
  return { x: cw / 2 - rootX, y: ch / 2 - rootY, scale: 1 }
}

// ── Helpers ────────────────────────────────────────────────────────
const sid = (id) => String(id)

function getInitials(name) {
  if (!name) return '?'
  return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
}

function surnameTokens(name) {
  if (!name || typeof name !== 'string') return []
  return name
    .replace(/\(.*?\)/g, '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
}

function previousSurname(name) {
  const tokens = surnameTokens(name)
  if (tokens.length < 2) return ''
  const prev = tokens[tokens.length - 2]
  return /^[A-Za-zА-Яа-яёЁ\-']+$/.test(prev) ? prev : ''
}

/** Цвет рамки кластера по фамилии (любой мемориал с этой последней/единственной фамилией в графе). */
function borderColorForSurname(nodes, memorialClusterStyle, surname) {
  if (!surname || !nodes?.length || !memorialClusterStyle) return null
  for (const n of nodes) {
    if (surnameOf(n.name) === surname) {
      const st =
        memorialClusterStyle[n.memorial_id] ??
        memorialClusterStyle[sid(n.memorial_id)]
      if (st?.borderColor) return st.borderColor
    }
  }
  return null
}

/**
 * Двухцветная рамка 50/50 (девичья фамилия | фамилия в браке), без border-image — стабильно в Chrome/Safari.
 * Сторона цвета привязана к положению веток (см. oldOnRight ниже по графу).
 */
function buildSplitGenCardBorder({ leftColor, rightColor, clusterStyle, isBridge }) {
  const CARD_BG = 'rgba(20, 20, 28, 0.92)'
  const bw = 3
  let boxShadow = clusterStyle?.boxShadow
  if (isBridge && clusterStyle?.boxShadow) {
    boxShadow = `${clusterStyle.boxShadow}, 0 0 0 2px rgba(220, 175, 95, 0.72), 0 0 22px rgba(220, 175, 95, 0.26)`
  } else if (isBridge) {
    boxShadow = `0 0 0 2px rgba(220, 175, 95, 0.72), 0 0 22px rgba(220, 175, 95, 0.26)`
  }
  return {
    border: `${bw}px solid transparent`,
    borderRadius: 8,
    background: `linear-gradient(${CARD_BG}, ${CARD_BG}) padding-box, linear-gradient(to right, ${leftColor} 0%, ${leftColor} 50%, ${rightColor} 50%, ${rightColor} 100%) border-box`,
    backgroundOrigin: 'border-box',
    backgroundClip: 'padding-box, border-box',
    boxShadow,
  }
}

function _edgeTypeLower(t) {
  return String(t || '').toLowerCase()
}

function isSpouseLikeGraphEdge(t) {
  const u = _edgeTypeLower(t)
  return u === 'spouse' || u === 'partner' || u === 'ex_spouse'
}

/**
 * В дереве есть «своя» линия девичьей фамилии: ребро не супружеское к мемориалу,
 * у которого последняя фамилия = maidenSurname (родитель, ребёнок, брат/сестра и т.д.).
 * Только тогда — рамка 50/50 девичья|мужа. Иначе одна рамка по последней фамилии (семья мужа).
 */
function hasMaidenFamilyLinkInGraph(graph, memorialId, maidenSurname) {
  if (!maidenSurname || !graph?.edges?.length) return false
  const sidId = sid(memorialId)
  for (const e of graph.edges) {
    if (isSpouseLikeGraphEdge(e.type)) continue
    if (_edgeTypeLower(e.type) === 'custom') continue
    const s = sid(e.source)
    const t = sid(e.target)
    if (s !== sidId && t !== sidId) continue
    const other = s === sidId ? t : s
    const node = graph.nodes.find((x) => sid(x.memorial_id) === other)
    if (!node) continue
    if (surnameOf(node.name) === maidenSurname) return true
  }
  return false
}

// Convert backend graph (nodes + edges) → relatives-tree format
function toLibNodes(graphNodes, graphEdges) {
  const idSet = new Set(graphNodes.map(n => sid(n.memorial_id)))
  const parentsOf  = {}
  const childrenOf = {}
  const siblingsOf = {}
  const spousesOf  = {}

  for (const id of idSet) {
    parentsOf[id]  = new Set()
    childrenOf[id] = new Set()
    siblingsOf[id] = new Set()
    spousesOf[id]  = new Set()
  }

  for (const e of graphEdges) {
    const src = sid(e.source), tgt = sid(e.target)
    if (!idSet.has(src) || !idSet.has(tgt)) continue
    // API: PARENT / adoptive_parent / step_parent — memorial_id=ребёнок, related=родитель (ребро child→parent).
    // API: CHILD / adoptive_child / step_child — memorial_id=родитель, related=ребёнок (ребро parent→child).
    if (e.type === 'parent' || e.type === 'adoptive_parent' || e.type === 'step_parent') {
      parentsOf[src].add(tgt)
      childrenOf[tgt].add(src)
    } else if (e.type === 'child' || e.type === 'adoptive_child' || e.type === 'step_child') {
      parentsOf[tgt].add(src)
      childrenOf[src].add(tgt)
    // sibling-like types → siblings slot
    } else if (e.type === 'sibling' || e.type === 'half_sibling') {
      siblingsOf[src].add(tgt)
      siblingsOf[tgt].add(src)
    // spouse-like types → spouses slot
    } else if (e.type === 'spouse' || e.type === 'partner' || e.type === 'ex_spouse') {
      spousesOf[src].add(tgt)
      spousesOf[tgt].add(src)
    }
    // custom → не отображается в дереве, только в списке связей
  }

  return graphNodes.map(n => {
    const id = sid(n.memorial_id)
    return {
      id,
      gender: n.gender === 'female' ? 'female' : 'male',
      parents:  [...parentsOf[id]].map(i => ({ id: i, type: 'blood' })),
      children: [...childrenOf[id]].map(i => ({ id: i, type: 'blood' })),
      siblings: [...siblingsOf[id]].map(i => ({ id: i, type: 'blood' })),
      spouses:  [...spousesOf[id]].map(i => ({ id: i, type: 'married' })),
    }
  })
}

// BFS relationship labels relative to root
// NOTE: edge types arrive uppercase from the API ('PARENT','CHILD','SPOUSE').
// We normalise to lowercase before lookup.
const LABEL_KEYS = {
  'parent':                 'rel_parent',
  'child':                  'rel_child',
  'spouse':                 'rel_spouse',
  'ex_spouse':              'rel_ex_spouse',
  'partner':                'rel_spouse',
  'sibling':                'rel_sibling',
  'half_sibling':           'rel_sibling',
  'parent,parent':          'rel_grandparent',
  'child,child':            'rel_grandchild',
  'parent,sibling':         'rel_aunt_uncle',
  'sibling,child':          'rel_niece_nephew',
  'spouse,parent':          'rel_parent_in_law',
  'parent,spouse':          'rel_stepparent',
  'child,spouse':           'rel_child_in_law',
  'spouse,child':           'rel_stepchild',
  'ex_spouse,child':        'rel_stepchild',
  'ex_spouse,parent':       'rel_parent_in_law',
  'parent,parent,parent':   'rel_great_grandparent',
  'child,child,child':      'rel_great_grandchild',
  'parent,parent,sibling':  'rel_great_aunt_uncle',
  'parent,sibling,child':   'rel_cousin',
}

/**
 * Generation-difference fallback label when BFS path doesn't match a key.
 * Uses the `generation` field on nodes and root's generation as reference.
 */
function genDiffLabel(nodeId, rootGeneration, nodeMap, t) {
  const n = nodeMap[nodeId]
  if (!n || n.generation == null || rootGeneration == null) return null
  const diff = Math.round(n.generation - rootGeneration)
  if (diff === -1) return t('family.rel_parent')
  if (diff === -2) return t('family.rel_grandparent')
  if (diff === -3) return t('family.rel_great_grandparent')
  if (diff === -4) return t('family.rel_great_great_grandparent') || t('family.rel_great_grandparent')
  if (diff === 1) return t('family.rel_child')
  if (diff === 2) return t('family.rel_grandchild')
  if (diff === 3) return t('family.rel_great_grandchild')
  return null
}

function buildRelLabels(nodes, edges, rootId, t) {
  const nodeMap = {}
  for (const n of nodes) nodeMap[sid(n.memorial_id)] = n
  const rootNode = nodeMap[sid(rootId)]
  const rootGen = rootNode?.generation ?? null

  const adj = {}
  for (const e of edges) {
    const s = sid(e.source), tg = sid(e.target)
    if (!adj[s]) adj[s] = []
    // Normalise to lowercase so LABEL_KEYS matches regardless of DB case
    adj[s].push({ n: tg, type: String(e.type || '').toLowerCase() })
  }
  const visited = { [sid(rootId)]: [] }
  const queue = [sid(rootId)]
  const labels = {}
  while (queue.length) {
    const cur = queue.shift()
    for (const { n, type } of (adj[cur] || [])) {
      if (n in visited) continue
      const path = [...visited[cur], type]
      visited[n] = path
      const key = LABEL_KEYS[path.join(',')]
      if (key) {
        labels[n] = t(`family.${key}`)
      } else {
        // Fallback: derive from generation difference
        const genLabel = genDiffLabel(n, rootGen, nodeMap, t)
        if (genLabel) labels[n] = genLabel
      }
      queue.push(n)
    }
  }
  return labels
}

// ── Node Card ──────────────────────────────────────────────────────
function NodeCard({ extNode, nodeMap, isRoot, relLabel, clusterStyle, onClick }) {
  const memorial = nodeMap[extNode.id]

  const x = extNode.left * HW + OFF_X
  const y = extNode.top  * HH + OFF_Y

  if (extNode.placeholder || !memorial) {
    // Placeholder: unknown family member
    return (
      <div
        className="ft-node ft-node--placeholder"
        style={{ position: 'absolute', left: x, top: y, width: NODE_W, height: NODE_H }}
      >
        <div className="ft-node-avatar-wrap">
          <div className="ft-node-avatar">
            <span className="ft-node-initials">?</span>
          </div>
        </div>
        <div className="ft-node-info">
          <div className="ft-node-name ft-node-name--unknown">Unknown</div>
        </div>
      </div>
    )
  }

  const isDeceased = !!memorial.death_year

  const clusterBorder = clusterStyle
    ? { borderLeft: `4px solid ${clusterStyle.borderColor}` }
    : {}

  return (
    <div
      className={[
        'ft-node',
        clusterStyle ? 'ft-node--pedigree-accent' : '',
        isRoot ? 'ft-node--root' : '',
        isDeceased ? 'ft-node--deceased' : 'ft-node--living',
      ].filter(Boolean).join(' ')}
      style={{ position: 'absolute', left: x, top: y, width: NODE_W, height: NODE_H, ...clusterBorder }}
      onClick={() => onClick(memorial.memorial_id)}
      title={[memorial.name, relLabel && !isRoot ? relLabel : null].filter(Boolean).join(' — ')}
    >
      <div className="ft-node-avatar-wrap">
        {isDeceased && (
          <span className="ft-node-candle-badge" title="Deceased" aria-hidden="true">
            🕯
          </span>
        )}
        <div className="ft-node-avatar">
          {memorial.cover_photo_id ? (
            <ApiMediaImage
              mediaId={memorial.cover_photo_id}
              thumbnail={null}
              alt={memorial.name}
              className="ft-node-img ft-node-img--hidpi"
              onError={e => { e.target.style.display = 'none' }}
            />
          ) : (
            <span className="ft-node-initials">{getInitials(memorial.name)}</span>
          )}
        </div>
        {isRoot && <div className="ft-node-root-ring" />}
      </div>
      <div className="ft-node-info">
        <div className="ft-node-name">{memorial.name}</div>
        {(memorial.birth_year || memorial.death_year) && (
          <div className="ft-node-years">
            {memorial.birth_year || '?'}{memorial.death_year ? ` — ${memorial.death_year}` : ''}
          </div>
        )}
        {relLabel && !isRoot && (
          <div className="ft-node-rel-label">{relLabel}</div>
        )}
      </div>
    </div>
  )
}

/** GOT-style circle node: round avatar + name + years below, no heavy card box */
function GenTreeNodeCard({
  memorial,
  left,
  top,
  nodeW,
  nodeH,
  isRoot,
  isBridge,
  clusterStyle,
  relLabel,
  onClick,
  editMode,
  onNodeDragStart,
  onPortDragStart,
}) {
  const isDeceased = !!memorial.death_year
  const ringColor = clusterStyle?.borderColor || (isDeceased ? 'rgba(180,150,100,0.7)' : 'rgba(100,180,255,0.7)')
  const ringWidth = isRoot ? 3 : 2
  const avatarSize = nodeW - 10  // circle fits within node width with small margin
  const avatarOffset = (nodeW - avatarSize) / 2

  const boxShadow = isBridge
    ? `0 0 0 ${ringWidth}px ${ringColor}, 0 0 0 4px rgba(220,175,95,0.5), 0 0 18px rgba(220,175,95,0.3)`
    : isRoot
      ? `0 0 0 ${ringWidth}px ${ringColor}, 0 0 0 5px rgba(255,255,255,0.15), 0 0 20px ${ringColor}`
      : `0 0 0 ${ringWidth}px ${ringColor}`

  return (
    <div
      className={[
        'ft-node ft-node--circle',
        isRoot ? 'ft-node--root' : '',
        isBridge ? 'ft-node--bridge' : '',
        isDeceased ? 'ft-node--deceased' : 'ft-node--living',
        editMode ? 'ft-node--edit' : '',
      ].filter(Boolean).join(' ')}
      data-memorial-id={memorial.memorial_id}
      style={{ position: 'absolute', left, top, width: nodeW, height: nodeH, cursor: editMode ? 'grab' : undefined }}
      onClick={editMode ? undefined : () => onClick(memorial.memorial_id)}
      onMouseDown={editMode ? (e) => { e.stopPropagation(); onNodeDragStart(memorial.memorial_id, e) } : undefined}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && !editMode && onClick(memorial.memorial_id)}
      title={[memorial.name, relLabel && !isRoot ? relLabel : null].filter(Boolean).join(' — ')}
    >
      {/* Port handles for drawing connections in edit mode */}
      {editMode && (
        <div className="ft-node-ports" onClick={e => e.stopPropagation()}>
          {['top', 'right', 'bottom', 'left'].map(side => (
            <div
              key={side}
              className={`ft-node-port ft-node-port--${side}`}
              onMouseDown={(e) => { e.stopPropagation(); e.preventDefault(); onPortDragStart(memorial.memorial_id) }}
            />
          ))}
        </div>
      )}
      {/* Circle avatar — deceased: dimmed; living: full brightness */}
      {/* top: 4 so the box-shadow ring (2px) doesn't get clipped by parent overflow:hidden */}
      <div
        className={`ft-circle-avatar${isDeceased ? ' ft-circle-avatar--deceased' : ''}`}
        style={{
          width: avatarSize,
          height: avatarSize,
          left: avatarOffset,
          top: 4,
          boxShadow,
        }}
      >
        {memorial.cover_photo_id ? (
          <ApiMediaImage
            mediaId={memorial.cover_photo_id}
            thumbnail={null}
            alt={memorial.name}
            className="ft-circle-img"
          />
        ) : (
          <span className="ft-circle-initials">{getInitials(memorial.name)}</span>
        )}
        {isRoot && <div className="ft-circle-root-pulse" />}
      </div>

      {/* Candle — outside avatar so it's not clipped by overflow:hidden */}
      {isDeceased && (
        <span
          className="ft-circle-candle"
          style={{ left: avatarOffset + avatarSize - 20, top: avatarSize - 16 }}
          aria-hidden="true"
        >🕯</span>
      )}

      {/* Text below circle */}
      <div className="ft-circle-info" style={{ top: avatarSize + 8 }}>
        <div className="ft-circle-name">{memorial.name}</div>
        {(memorial.birth_year || memorial.death_year) && (
          <div className="ft-circle-years">
            {memorial.birth_year || '?'}{memorial.death_year ? `–${memorial.death_year}` : ''}
          </div>
        )}
        {relLabel && !isRoot && (
          <div className="ft-circle-rel">{relLabel}</div>
        )}
      </div>
    </div>
  )
}

// ── Connected-families mini card ───────────────────────────────────
function ConnectedFamilyCard({ member, bridgeLabel, onClick }) {
  const isDeceased = !!member.death_year
  return (
    <div
      className={`ft-cf-card ${isDeceased ? 'ft-cf-card--deceased' : ''}`}
      onClick={() => onClick(member.memorial_id)}
      title={bridgeLabel}
    >
      <div className="ft-cf-avatar">
        {member.cover_photo_id ? (
          <ApiMediaImage mediaId={member.cover_photo_id} thumbnail={null} alt={member.name} className="ft-cf-img" />
        ) : (
          <span className="ft-cf-initials">{member.name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()}</span>
        )}
      </div>
      <div className="ft-cf-name">{member.name.split(' ')[0]}</div>
      {(member.birth_year || member.death_year) && (
        <div className="ft-cf-years">{member.birth_year || '?'}{member.death_year ? `–${member.death_year}` : ''}</div>
      )}
    </div>
  )
}

// ── Stub Node Card (locked family member) — GOT-style circle ──────
function StubNodeCard({ memorial, left, top, nodeW, nodeH, onUnlock }) {
  const { t } = useLanguage()
  const familyColor = FAMILY_CONFIG[memorial._family]?.color || 'rgba(200,169,126,0.6)'
  const avatarSize = nodeW - 10
  const avatarOffset = (nodeW - avatarSize) / 2
  return (
    <div
      className="ft-node ft-node--circle ft-node--stub"
      style={{
        position: 'absolute',
        left,
        top,
        width: nodeW,
        height: nodeH,
        '--stub-color': familyColor,
      }}
      title={`${memorial.name} — ${memorial._family} Family`}
      onClick={onUnlock}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onUnlock()}
    >
      <div
        className="ft-circle-avatar ft-circle-avatar--stub"
        style={{
          width: avatarSize,
          height: avatarSize,
          left: avatarOffset,
          top: 4,
          boxShadow: `0 0 0 2px ${familyColor}`,
        }}
      >
        <span className="ft-stub-lock" aria-hidden="true">🔒</span>
      </div>
      <div className="ft-circle-info" style={{ top: avatarSize + 8 }}>
        <div className="ft-circle-name ft-circle-name--stub">
          {memorial.name.split(' ')[0]}
        </div>
        <div className="ft-stub-family-tag">{memorial._family}</div>
        <button
          className="ft-stub-unlock-btn"
          onClick={(e) => { e.stopPropagation(); onUnlock() }}
          title={t('family.stub_show_family_title') || `Show ${memorial._family} family`}
        >
          {t('family.stub_show') || 'Show'}
        </button>
      </div>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────────
export default function FamilyTree({ memorialId, canEdit = false }) {
  const navigate  = useNavigate()
  const { t }     = useLanguage()
  const canvasRef = useRef(null)

  const [graphData,    setGraphData]    = useState(null)
  const [relationships, setRelationships] = useState([])
  const [loading,      setLoading]      = useState(true)

  const [showAddForm,        setShowAddForm]        = useState(false)
  const [formData,           setFormData]           = useState({ related_memorial_id: '', relationship_type: 'parent', custom_label: '', notes: '' })
  const [availableMemorials, setAvailableMemorials] = useState([])
  const availableLoaded = useRef(false)
  const [submitting, setSubmitting] = useState(false)

  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  /** generations = ряды поколений + две линии (демо); pedigree = relatives-tree */
  const [layoutMode, setLayoutMode] = useState('generations')
  /** Какие семьи сейчас видны в дереве (по фамилии). Стартуем с Kelly. */
  const [visibleFamilies, setVisibleFamilies] = useState(['Kelly'])
  const [treeFullscreen, setTreeFullscreen] = useState(false)
  const familyTreeRootRef = useRef(null)
  const dragRef  = useRef(null)
  const pinchRef = useRef(null)

  // ── Edit mode state ────────────────────────────────────────────────
  const [editMode, setEditMode] = useState(false)
  // nodeOverrides: позиции узлов, заданные пользователем вручную {memId: {x, y}}
  const [nodeOverrides, _setNodeOverrides] = useState({})
  // Ref для актуального значения без closure-staleness в обработчиках мыши
  const nodeOverridesRef = useRef({})
  const setNodeOverrides = useCallback((updater) => {
    if (typeof updater === 'function') {
      _setNodeOverrides(prev => {
        const next = updater(prev)
        nodeOverridesRef.current = next
        return next
      })
    } else {
      nodeOverridesRef.current = updater
      _setNodeOverrides(updater)
    }
  }, [])

  const nodeDragRef = useRef(null)  // {nodeId, startScreenX, startScreenY, origX, origY}
  // Snap lines shown during node drag: [{axis:'x'|'y', value, extent:[min,max]}]
  const [snapLines, setSnapLines] = useState([])
  const saveTimerRef = useRef(null)
  const [drawingEdge, setDrawingEdge] = useState(null)  // {fromId, curX, curY}
  const [pendingEdge, setPendingEdge] = useState(null)  // {fromId, toId}
  const [pendingEdgeForm, setPendingEdgeForm] = useState({ relationship_type: 'parent', custom_label: '', notes: '' })

  // ── Data loading ───────────────────────────────────────────────
  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const [fullRes, relsRes, memRes] = await Promise.all([
        familyAPI.getFullTree(memorialId, 6),
        familyAPI.getRelationships(memorialId),
        memorialsAPI.get(memorialId).catch(() => null),
      ])
      setGraphData(fullRes.data)
      setRelationships(Array.isArray(relsRes.data) ? relsRes.data : [])
      // Загрузка сохранённых позиций узлов из БД
      const layout = memRes?.data?.tree_layout_json
      if (layout?.nodePositions && typeof layout.nodePositions === 'object') {
        setNodeOverrides(layout.nodePositions)
      }
    } catch (err) {
      console.error('Error loading family tree:', err)
    } finally {
      setLoading(false)
    }
  }, [memorialId, setNodeOverrides])

  useEffect(() => { loadData() }, [loadData])

  /** Граф, отфильтрованный по visibleFamilies. Чужие узлы на границе — stubs. */
  const displayGraph = useMemo(() => {
    if (!graphData?.nodes?.length) return null
    return filterGraphToScope(graphData, visibleFamilies)
  }, [graphData, visibleFamilies])

  // ── Derived data ───────────────────────────────────────────────
  // Map id → memorial object for fast lookup
  const nodeMap = useMemo(() => {
    if (!displayGraph?.nodes) return {}
    return Object.fromEntries(displayGraph.nodes.map(n => [sid(n.memorial_id), n]))
  }, [displayGraph])

  const clusterTheme = useMemo(
    () => buildSurnameClusterStyles(displayGraph?.nodes || []),
    [displayGraph?.nodes]
  )

  const rootDisplayName = useMemo(() => {
    if (!displayGraph?.nodes || displayGraph.root_id == null) return ''
    const n = displayGraph.nodes.find((x) => x.memorial_id === displayGraph.root_id)
    return n?.name || ''
  }, [displayGraph])

  // relatives-tree layout
  const treeData = useMemo(() => {
    if (!displayGraph?.nodes?.length) return null
    try {
      const libNodes = toLibNodes(displayGraph.nodes, displayGraph.edges)
      return calcTree(libNodes, {
        rootId: sid(displayGraph.root_id),
        placeholders: true,
      })
    } catch (e) {
      console.error('calcTree error', e)
      return null
    }
  }, [displayGraph])

  // Relationship labels (BFS from root)
  const relLabels = useMemo(() => {
    if (!displayGraph) return {}
    return buildRelLabels(displayGraph.nodes, displayGraph.edges, displayGraph.root_id, t)
  }, [displayGraph, t])

  // singleFamilyMode: одна семья видна полностью — центрируем всё в одну колонку
  const singleFamilyMode = visibleFamilies.length === 1

  const genLayout = useMemo(() => {
    if (!displayGraph?.nodes?.length) return null
    try {
      return buildGenerationLayout(displayGraph, singleFamilyMode)
    } catch (e) {
      console.error('buildGenerationLayout', e)
      return null
    }
  }, [displayGraph, singleFamilyMode])

  // Позиции узлов: авто-layout + ручные корректировки пользователя
  const effectivePositions = useMemo(() => {
    if (!genLayout?.positions) return {}
    if (!Object.keys(nodeOverrides).length) return genLayout.positions
    const nw = genLayout.nodeSize?.w ?? 90
    const nh = genLayout.nodeSize?.h ?? 148
    const merged = { ...genLayout.positions }
    for (const [id, ov] of Object.entries(nodeOverrides)) {
      if (merged[id]) {
        merged[id] = {
          ...merged[id],
          x: ov.x,
          y: ov.y,
          cx: ov.x + nw / 2,
          cy: ov.y + nh / 2,
        }
      }
    }
    return merged
  }, [genLayout, nodeOverrides])

  // Refs для использования в mousemove без stale-closure
  const effectivePositionsRef = useRef(null)
  useEffect(() => { effectivePositionsRef.current = effectivePositions }, [effectivePositions])
  const genLayoutRef = useRef(null)
  useEffect(() => { genLayoutRef.current = genLayout }, [genLayout])

  const bridgeNodeIds = useMemo(() => {
    if (!displayGraph?.edges || !genLayout?.lineage) return new Set()
    const s = new Set()
    for (const e of displayGraph.edges) {
      if (
        isCrossFamilySpouseEdge(
          e,
          genLayout.lineage,
          displayGraph.nodes,
          genLayout.memorialClusterStyle
        )
      ) {
        s.add(sid(e.source))
        s.add(sid(e.target))
      }
    }
    return s
  }, [displayGraph, genLayout])

  const orthoConnectorLines = useMemo(() => {
    if (layoutMode !== 'generations' || !effectivePositions || !displayGraph?.edges) return []
    return buildOrthogonalConnectors({
      edges: displayGraph.edges,
      positions: effectivePositions,
      nodeSize: genLayout?.nodeSize,
      lineageMap: genLayout?.lineage,
      nodes: displayGraph.nodes,
      memorialClusterStyle: genLayout?.memorialClusterStyle,
    }).lines
  }, [layoutMode, effectivePositions, genLayout, displayGraph?.edges, displayGraph?.nodes])

  const spouseMarriageMarkers = useMemo(() => {
    if (layoutMode !== 'generations' || !effectivePositions || !displayGraph?.edges) return []
    return getSpouseMarriageMarkers({
      edges: displayGraph.edges,
      positions: effectivePositions,
      nodeSize: genLayout?.nodeSize,
      lineageMap: genLayout?.lineage,
      nodes: displayGraph.nodes,
      memorialClusterStyle: genLayout?.memorialClusterStyle,
    })
  }, [layoutMode, effectivePositions, genLayout, displayGraph?.edges, displayGraph?.nodes])

  useEffect(() => {
    const onFs = () => {
      const el = familyTreeRootRef.current
      setTreeFullscreen(!!el && document.fullscreenElement === el)
    }
    document.addEventListener('fullscreenchange', onFs)
    return () => document.removeEventListener('fullscreenchange', onFs)
  }, [])

  const toggleTreeFullscreen = useCallback(async () => {
    const el = familyTreeRootRef.current
    if (!el) return
    try {
      if (!document.fullscreenElement) await el.requestFullscreen()
      else await document.exitFullscreen()
    } catch (err) {
      console.warn('Fullscreen:', err)
    }
  }, [])

  // Re-fit tree when entering/exiting fullscreen — use bounding-box fit for accuracy
  useEffect(() => {
    if (!canvasRef.current) return
    const tid = setTimeout(() => {
      if (!canvasRef.current) return
      if (layoutMode === 'generations' && genLayout) {
        const next = fitNodesBoundingBox(canvasRef.current, effectivePositionsRef.current, genLayout.nodeSize)
          ?? fitInnerInViewport(canvasRef.current, genLayout.canvas.width, genLayout.canvas.height)
        if (next) setTransform(next)
      } else if (treeData) {
        const innerW = treeData.canvas.width * HW
        const innerH = treeData.canvas.height * HH
        const next = fitInnerInViewport(canvasRef.current, innerW, innerH)
        if (next) setTransform(next)
      }
    }, 350)
    return () => clearTimeout(tid)
  }, [treeFullscreen, layoutMode, genLayout, treeData])

  // (connectedFamilies panel removed — replaced by stub nodes + unlock buttons)

  // Canvas pixel size
  const canvasW = useMemo(() => {
    if (layoutMode === 'generations' && genLayout) return genLayout.canvas.width
    return treeData ? treeData.canvas.width * HW : 800
  }, [layoutMode, genLayout, treeData])

  const canvasH = useMemo(() => {
    if (layoutMode === 'generations' && genLayout) return genLayout.canvas.height
    return treeData ? treeData.canvas.height * HH : 400
  }, [layoutMode, genLayout, treeData])

  // Initial view: fit whole tree to actual node bounding box
  // NOTE: effectivePositions intentionally NOT in deps — changes on every drag.
  useEffect(() => {
    if (!canvasRef.current || !displayGraph?.root_id) return
    if (layoutMode === 'generations' && genLayout) {
      const next = fitNodesBoundingBox(canvasRef.current, effectivePositionsRef.current, genLayout.nodeSize)
        ?? fitInnerInViewport(canvasRef.current, genLayout.canvas.width, genLayout.canvas.height)
      if (next) setTransform(next)
      return
    }
    if (!treeData) return
    const innerW = treeData.canvas.width * HW
    const innerH = treeData.canvas.height * HH
    const next = fitInnerInViewport(canvasRef.current, innerW, innerH)
    if (next) setTransform(next)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layoutMode, genLayout, treeData, displayGraph?.root_id, memorialId])

  const fitWholeTree = useCallback(() => {
    if (!canvasRef.current) return
    if (layoutMode === 'generations' && genLayout) {
      const next = fitNodesBoundingBox(canvasRef.current, effectivePositionsRef.current, genLayout.nodeSize)
        ?? fitInnerInViewport(canvasRef.current, genLayout.canvas.width, genLayout.canvas.height)
      if (next) setTransform(next)
      return
    }
    if (!displayGraph || !treeData) return
    const innerW = treeData.canvas.width * HW
    const innerH = treeData.canvas.height * HH
    const next = fitInnerInViewport(canvasRef.current, innerW, innerH)
    if (next) setTransform(next)
  }, [layoutMode, genLayout, displayGraph, treeData])

  const centerOnThisPerson = useCallback(() => {
    if (!displayGraph?.root_id || !canvasRef.current) return
    if (layoutMode === 'generations' && effectivePositions) {
      const p = effectivePositions[sid(displayGraph.root_id)]
      if (!p) return
      const el = canvasRef.current
      const cw = el.offsetWidth
      const ch = el.offsetHeight
      setTransform({ x: cw / 2 - p.cx, y: ch / 2 - p.cy, scale: 1 })
      return
    }
    if (!treeData) return
    const rootNode = treeData.nodes.find(n => n.id === sid(displayGraph.root_id))
    const next = centerRootInViewport(canvasRef.current, rootNode)
    if (next) setTransform(next)
  }, [layoutMode, effectivePositions, displayGraph?.root_id, treeData])

  // ── Edit mode: layout save + drag + draw ───────────────────────
  const saveLayout = useCallback((overrides) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(async () => {
      try {
        await memorialsAPI.update(memorialId, {
          tree_layout_json: { nodePositions: overrides, version: 1 }
        })
      } catch (err) {
        console.error('Failed to save tree layout:', err)
      }
    }, 400)
  }, [memorialId])

  // Flush pending save on unmount (prevents losing positions when navigating away quickly)
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
        const overrides = nodeOverridesRef.current
        if (Object.keys(overrides).length > 0) {
          memorialsAPI.update(memorialId, {
            tree_layout_json: { nodePositions: overrides, version: 1 }
          }).catch(() => {})
        }
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [memorialId])

  const handleNodeDragStart = useCallback((memId, e) => {
    if (drawingEdge) return  // не начинать drag узла во время рисования связи
    e.preventDefault()
    const pos = effectivePositions[String(memId)]
    if (!pos) return
    nodeDragRef.current = {
      nodeId: String(memId),
      startScreenX: e.clientX,
      startScreenY: e.clientY,
      origX: pos.x,
      origY: pos.y,
    }
  }, [effectivePositions, drawingEdge])

  const handlePortDragStart = useCallback((memId) => {
    const pos = effectivePositions[String(memId)]
    if (!pos) return
    setDrawingEdge({
      fromId: String(memId),
      curX: pos.cx,
      curY: pos.cy,
    })
  }, [effectivePositions])

  const handleCreatePendingEdge = async () => {
    if (!pendingEdge) return
    setSubmitting(true)
    try {
      await familyAPI.createRelationship(pendingEdge.fromId, {
        related_memorial_id: parseInt(pendingEdge.toId),
        relationship_type: pendingEdgeForm.relationship_type,
        custom_label: pendingEdgeForm.custom_label || undefined,
        notes: pendingEdgeForm.notes || undefined,
      })
      setPendingEdge(null)
      setPendingEdgeForm({ relationship_type: 'parent', custom_label: '', notes: '' })
      await loadData()
    } catch (err) {
      alert(err.response?.data?.detail || t('family.add_error'))
    } finally {
      setSubmitting(false)
    }
  }

  // ── Pan / zoom ─────────────────────────────────────────────────
  useEffect(() => {
    const el = canvasRef.current
    if (!el) return
    const onWheel = (e) => {
      e.preventDefault()
      const rect = el.getBoundingClientRect()
      const px = e.clientX - rect.left
      const py = e.clientY - rect.top
      const delta = e.deltaY > 0 ? -0.1 : 0.1
      setTransform(prev => {
        const next = snapTreeScale(prev.scale + delta * prev.scale)
        const ratio = next / prev.scale
        return { x: px - ratio * (px - prev.x), y: py - ratio * (py - prev.y), scale: next }
      })
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [loading])

  const onMouseDown = useCallback((e) => {
    if (e.target.closest('.ft-node')) return
    dragRef.current = { startX: e.clientX, startY: e.clientY, startTX: transform.x, startTY: transform.y }
    e.currentTarget.style.cursor = 'grabbing'
  }, [transform])

  const SNAP_THRESHOLD = 8  // px in canvas coordinates

  const onMouseMove = useCallback((e) => {
    // Drag узла в edit mode
    if (nodeDragRef.current) {
      const { nodeId, startScreenX, startScreenY, origX, origY } = nodeDragRef.current
      const dx = (e.clientX - startScreenX) / transform.scale
      const dy = (e.clientY - startScreenY) / transform.scale
      let rawX = origX + dx
      let rawY = origY + dy

      // Snap lines: compare center of dragged node with other nodes' centers
      const curPositions = nodeOverridesRef.current
      const allPositions = effectivePositionsRef.current
      if (allPositions) {
        const nw = genLayoutRef.current?.nodeSize?.w ?? 90
        const nh = genLayoutRef.current?.nodeSize?.h ?? 148
        const dragCX = rawX + nw / 2
        const dragCY = rawY + nh / 2
        const lines = []
        let snapX = null, snapY = null

        for (const [id, pos] of Object.entries(allPositions)) {
          if (id === nodeId) continue
          const ox = pos.cx ?? (pos.x + nw / 2)
          const oy = pos.cy ?? (pos.y + nh / 2)

          // Horizontal snap (same Y center)
          if (Math.abs(dragCY - oy) < SNAP_THRESHOLD / transform.scale) {
            if (snapY === null || Math.abs(dragCY - oy) < Math.abs(dragCY - snapY)) snapY = oy
          }
          // Vertical snap (same X center)
          if (Math.abs(dragCX - ox) < SNAP_THRESHOLD / transform.scale) {
            if (snapX === null || Math.abs(dragCX - ox) < Math.abs(dragCX - snapX)) snapX = ox
          }
        }

        if (snapY !== null) {
          rawY = snapY - nh / 2
          lines.push({ axis: 'y', value: snapY })
        }
        if (snapX !== null) {
          rawX = snapX - nw / 2
          lines.push({ axis: 'x', value: snapX })
        }
        setSnapLines(lines)
      }

      setNodeOverrides(prev => ({
        ...prev,
        [nodeId]: { x: rawX, y: rawY }
      }))
      return
    }
    // Рисование связи
    if (drawingEdge) {
      const rect = canvasRef.current?.getBoundingClientRect()
      if (!rect) return
      setDrawingEdge(prev => ({
        ...prev,
        curX: (e.clientX - rect.left - transform.x) / transform.scale,
        curY: (e.clientY - rect.top  - transform.y) / transform.scale,
      }))
      return
    }
    // Pan
    if (!dragRef.current) return
    const { startTX, startTY, startX, startY } = dragRef.current
    setTransform(prev => ({ ...prev, x: startTX + e.clientX - startX, y: startTY + e.clientY - startY }))
  }, [transform, drawingEdge, setNodeOverrides])

  const onMouseUp = useCallback((e) => {
    // Drag узла: сохраняем финальные позиции
    if (nodeDragRef.current) {
      nodeDragRef.current = null
      setSnapLines([])
      saveLayout(nodeOverridesRef.current)
      e.currentTarget.style.cursor = editMode ? 'default' : 'grab'
      return
    }
    // Рисование связи: проверяем, не отпущена ли мышь над узлом
    if (drawingEdge) {
      const nodeEl = e.target.closest('[data-memorial-id]')
      if (nodeEl) {
        const toId = nodeEl.getAttribute('data-memorial-id')
        if (toId && toId !== drawingEdge.fromId) {
          setPendingEdge({ fromId: drawingEdge.fromId, toId })
          setPendingEdgeForm({ relationship_type: 'parent', custom_label: '', notes: '' })
        }
      }
      setDrawingEdge(null)
      return
    }
    // Pan end
    dragRef.current = null
    e.currentTarget.style.cursor = 'grab'
  }, [drawingEdge, editMode, saveLayout])

  const onTouchStart = useCallback((e) => {
    if (e.touches.length === 1) {
      const t0 = e.touches[0]
      dragRef.current = { startX: t0.clientX, startY: t0.clientY, startTX: transform.x, startTY: transform.y }
    } else if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX
      const dy = e.touches[0].clientY - e.touches[1].clientY
      pinchRef.current = {
        dist: Math.hypot(dx, dy), scale: transform.scale,
        tx: transform.x, ty: transform.y,
        cx: (e.touches[0].clientX + e.touches[1].clientX) / 2,
        cy: (e.touches[0].clientY + e.touches[1].clientY) / 2,
      }
      dragRef.current = null
    }
  }, [transform])

  const onTouchMove = useCallback((e) => {
    e.preventDefault()
    if (e.touches.length === 1 && dragRef.current) {
      const t0 = e.touches[0]
      const { startTX, startTY, startX, startY } = dragRef.current
      setTransform(prev => ({ ...prev, x: startTX + t0.clientX - startX, y: startTY + t0.clientY - startY }))
    } else if (e.touches.length === 2 && pinchRef.current) {
      const dx = e.touches[0].clientX - e.touches[1].clientX
      const dy = e.touches[0].clientY - e.touches[1].clientY
      const ratio = Math.hypot(dx, dy) / pinchRef.current.dist
      const next = snapTreeScale(pinchRef.current.scale * ratio)
      const sr = next / pinchRef.current.scale
      const rect = canvasRef.current.getBoundingClientRect()
      const px = pinchRef.current.cx - rect.left
      const py = pinchRef.current.cy - rect.top
      setTransform({ x: px - sr * (px - pinchRef.current.tx), y: py - sr * (py - pinchRef.current.ty), scale: next })
    }
  }, [])

  const onTouchEnd = useCallback(() => { dragRef.current = null; pinchRef.current = null }, [])

  // ── Form handlers ──────────────────────────────────────────────
  const loadAvailableMemorials = async () => {
    if (availableLoaded.current) return
    try {
      const res = await memorialsAPI.list()
      setAvailableMemorials((Array.isArray(res.data) ? res.data : []).filter(m => m.id !== parseInt(memorialId)))
      availableLoaded.current = true
    } catch (err) { console.error(err) }
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await familyAPI.createRelationship(memorialId, formData)
      setFormData({ related_memorial_id: '', relationship_type: 'parent', custom_label: '', notes: '' })
      setShowAddForm(false)
      availableLoaded.current = false
      await loadData()
    } catch (err) {
      alert(err.response?.data?.detail || t('family.add_error'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (relId) => {
    if (!confirm(t('family.delete_confirm'))) return
    try { await familyAPI.deleteRelationship(relId); await loadData() }
    catch (err) { alert(err.response?.data?.detail || t('family.error')) }
  }

  // ── Render ─────────────────────────────────────────────────────
  if (loading) return <div className="loading">{t('family.loading')}</div>

  const showGenerations = !!genLayout
  const showPedigree = false
  const hasTree = !!displayGraph?.nodes?.length && showGenerations

  return (
    <div
      ref={familyTreeRootRef}
      className={`family-tree${treeFullscreen ? ' family-tree--fullscreen' : ''}`}
    >
      {/* Header */}
      <div className="tree-header">
        <h2>{t('family.title')}</h2>
        <div className="tree-header-actions">
          {graphData?.nodes?.length > 0 && (
            <span className="tree-layout-label">{t('family.layout_generations')}</span>
          )}
          {hasTree && (
            <span className="tree-node-count">
              {t('family.people_count')(displayGraph.nodes.length)}
            </span>
          )}
        </div>
      </div>
      {/* Unlock bar — скрыт в generation-mode (multi-family layout ещё не поддерживается) */}
      {!showGenerations && displayGraph?._lockedFamilies?.length > 0 && (
        <div className="ft-unlock-bar">
          <span className="ft-unlock-bar__hint">
            {t('family.unlock_hint') || 'Connected families:'}
          </span>
          {displayGraph._lockedFamilies.map(fam => (
            <button
              key={fam}
              className="ft-unlock-btn"
              style={{ '--family-color': FAMILY_CONFIG[fam]?.color || '#c8a97e' }}
              onClick={() => setVisibleFamilies(prev => [...prev, fam])}
            >
              + {fam} Family
            </button>
          ))}
        </div>
      )}
      {showGenerations && genLayout && (
        <>
          <div className="ft-gen-legend" aria-hidden={false}>
            {(genLayout.clusterLegend || []).map((c) => (
              <span
                key={c.key}
                className="ft-leg ft-leg--cluster"
                style={{
                  borderColor: c.border,
                  background: c.pillBg,
                  color: c.textColor,
                }}
              >
                {c.key === genLayout.otherSurnameKey ? t('family.cluster_other') : c.key}
              </span>
            ))}
            <span className="ft-leg ft-leg--gold">∞ {t('family.legend_cross_family_short')}</span>
          </div>
          <p className="tree-controls-hint ft-gen-hint">{t('family.gen_legend_hint')}</p>
          <details className="ft-gen-help">
            <summary className="ft-gen-help-summary">{t('family.gen_legend_expand')}</summary>
            <div className="ft-gen-help-body">
              <p>{t('family.gen_legend_help_borders')}</p>
              <p>{t('family.gen_legend_help_lines')}</p>
              <p>
                {t('family.gen_legend_help_labels', {
                  rootName: rootDisplayName || t('family.gen_legend_root_fallback'),
                })}
              </p>
              <p>{t('family.gen_legend_help_generation')}</p>
            </div>
          </details>
        </>
      )}
      {hasTree && layoutMode === 'pedigree' && (
        <p className="tree-controls-hint">{t('family.tree_controls')}</p>
      )}

      {/* Add form (editor/owner only) */}
      {canEdit && showAddForm && (
        <form onSubmit={handleAdd} className="relationship-form">
          <div className="form-group">
            <label>{t('family.form_memorial')}</label>
            {availableMemorials.length > 0 ? (
              <select
                value={formData.related_memorial_id}
                onChange={e => setFormData({ ...formData, related_memorial_id: parseInt(e.target.value) })}
                required
              >
                <option value="">{t('family.form_select_placeholder')}</option>
                {availableMemorials.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            ) : (
              <input
                type="number"
                value={formData.related_memorial_id}
                onChange={e => setFormData({ ...formData, related_memorial_id: parseInt(e.target.value) })}
                required placeholder={t('family.form_id_placeholder')}
              />
            )}
          </div>
          <div className="form-group">
            <label>{t('family.form_type')}</label>
            <select
              value={formData.relationship_type}
              onChange={e => setFormData({ ...formData, relationship_type: e.target.value, custom_label: '' })}
              required
            >
              <optgroup label={t('family.group_parent_child')}>
                <option value="parent">{t('family.type_parent_desc')}</option>
                <option value="child">{t('family.type_child_desc')}</option>
                <option value="adoptive_parent">{t('family.type_adoptive_parent_desc')}</option>
                <option value="adoptive_child">{t('family.type_adoptive_child_desc')}</option>
                <option value="step_parent">{t('family.type_step_parent_desc')}</option>
                <option value="step_child">{t('family.type_step_child_desc')}</option>
              </optgroup>
              <optgroup label={t('family.group_partner')}>
                <option value="spouse">{t('family.type_spouse_desc')}</option>
                <option value="partner">{t('family.type_partner_desc')}</option>
                <option value="ex_spouse">{t('family.type_ex_spouse_desc')}</option>
              </optgroup>
              <optgroup label={t('family.group_sibling')}>
                <option value="sibling">{t('family.type_sibling_desc')}</option>
                <option value="half_sibling">{t('family.type_half_sibling_desc')}</option>
              </optgroup>
              <optgroup label={t('family.group_other')}>
                <option value="custom">{t('family.type_custom_desc')}</option>
              </optgroup>
            </select>
          </div>
          {formData.relationship_type === 'custom' && (
            <div className="form-group">
              <label>{t('family.form_custom_label')} *</label>
              <input
                type="text"
                value={formData.custom_label}
                onChange={e => setFormData({ ...formData, custom_label: e.target.value })}
                required
                maxLength={100}
                placeholder={t('family.form_custom_label_placeholder')}
              />
            </div>
          )}
          <div className="form-group">
            <label>{t('family.form_notes')}</label>
            <textarea
              value={formData.notes}
              onChange={e => setFormData({ ...formData, notes: e.target.value })}
              rows="2" placeholder={t('family.form_notes_placeholder')}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? t('common.saving') : t('family.add_submit')}
          </button>
        </form>
      )}

      {/* Pending edge modal — создание связи через визуальное рисование */}
      {pendingEdge && (
        <div className="ft-pending-edge-overlay" onClick={() => setPendingEdge(null)}>
          <div className="ft-pending-edge-modal" onClick={e => e.stopPropagation()}>
            <div className="ft-pending-edge-header">
              <h4>{t('family.connect_title') || 'Connect memorials'}</h4>
              <button className="ft-pending-edge-close" onClick={() => setPendingEdge(null)}>✕</button>
            </div>
            <div className="form-group">
              <label>{t('family.form_type')}</label>
              <select
                value={pendingEdgeForm.relationship_type}
                onChange={e => setPendingEdgeForm(f => ({ ...f, relationship_type: e.target.value, custom_label: '' }))}
              >
                <optgroup label={t('family.group_parent_child')}>
                  <option value="parent">{t('family.type_parent_desc')}</option>
                  <option value="child">{t('family.type_child_desc')}</option>
                  <option value="adoptive_parent">{t('family.type_adoptive_parent_desc')}</option>
                  <option value="adoptive_child">{t('family.type_adoptive_child_desc')}</option>
                  <option value="step_parent">{t('family.type_step_parent_desc')}</option>
                  <option value="step_child">{t('family.type_step_child_desc')}</option>
                </optgroup>
                <optgroup label={t('family.group_partner')}>
                  <option value="spouse">{t('family.type_spouse_desc')}</option>
                  <option value="partner">{t('family.type_partner_desc')}</option>
                  <option value="ex_spouse">{t('family.type_ex_spouse_desc')}</option>
                </optgroup>
                <optgroup label={t('family.group_sibling')}>
                  <option value="sibling">{t('family.type_sibling_desc')}</option>
                  <option value="half_sibling">{t('family.type_half_sibling_desc')}</option>
                </optgroup>
                <optgroup label={t('family.group_other')}>
                  <option value="custom">{t('family.type_custom_desc')}</option>
                </optgroup>
              </select>
            </div>
            {pendingEdgeForm.relationship_type === 'custom' && (
              <div className="form-group">
                <label>{t('family.form_custom_label')} *</label>
                <input
                  type="text"
                  value={pendingEdgeForm.custom_label}
                  onChange={e => setPendingEdgeForm(f => ({ ...f, custom_label: e.target.value }))}
                  required
                  maxLength={100}
                  placeholder={t('family.form_custom_label_placeholder')}
                />
              </div>
            )}
            <div className="ft-pending-edge-actions">
              <button className="btn btn-primary" onClick={handleCreatePendingEdge} disabled={submitting}>
                {submitting ? t('common.saving') : t('family.add_submit')}
              </button>
              <button className="btn" onClick={() => setPendingEdge(null)}>
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!hasTree && (
        <div className="ft-empty">
          <div className="ft-empty-title">{t('family.empty_title')}</div>
          <div className="ft-empty-hint">{t('family.empty_hint')}</div>
        </div>
      )}

      {/* Tree canvas */}
      {hasTree && (
        <div className="ft-canvas-wrap">
        <div
          className="tree-canvas"
          ref={canvasRef}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          <div
            className="tree-canvas-inner"
            style={{
              width: canvasW,
              height: canvasH,
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale}) translateZ(0)`,
              transformOrigin: '0 0',
            }}
          >
            {/* Connectors — library gives us axis-aligned segments as [x1,y1,x2,y2] grid coords */}
            {layoutMode === 'generations' && genLayout ? (
              <>
                <svg
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: canvasW,
                    height: canvasH,
                    pointerEvents: 'none',
                    overflow: 'visible',
                  }}
                >
                  {/* Generation row labels */}
                  {genLayout.genBands && Object.entries(genLayout.genBands).map(([g, band]) => {
                    const labelX = (genLayout.labelAreaX || 0) + (genLayout.labelAreaW || 120) - 8
                    const midY = band.top + band.height / 2
                    return (
                      <g key={`gen-label-${g}`} className="ft-gen-row-label">
                        {/* Horizontal divider line */}
                        {Number(g) > 0 && (
                          <line
                            x1={genLayout.labelAreaX || 0}
                            y1={band.top - (36 / 2)}
                            x2={canvasW}
                            y2={band.top - (36 / 2)}
                            stroke="rgba(255,255,255,0.06)"
                            strokeWidth={1}
                          />
                        )}
                        {/* Gen number pill */}
                        <rect
                          x={labelX - 28}
                          y={midY - 18}
                          width={36}
                          height={20}
                          rx={4}
                          fill="rgba(255,255,255,0.05)"
                          stroke="rgba(255,255,255,0.1)"
                          strokeWidth={1}
                        />
                        <text
                          x={labelX - 10}
                          y={midY - 3}
                          textAnchor="middle"
                          fill="rgba(255,255,255,0.45)"
                          fontSize={10}
                          fontFamily="Inter, sans-serif"
                          fontWeight="600"
                          letterSpacing="0.04em"
                        >
                          {`G${band.genIndex}`}
                        </text>
                        {/* Decade label */}
                        {band.decade && (
                          <text
                            x={labelX - 10}
                            y={midY + 12}
                            textAnchor="middle"
                            fill="rgba(255,255,255,0.25)"
                            fontSize={9}
                            fontFamily="Inter, sans-serif"
                          >
                            {band.decade}
                          </text>
                        )}
                      </g>
                    )
                  })}
                  {/* laneGapBands removed — caused stray pixel artifacts at low opacity */}
                  {orthoConnectorLines.map((ln) => (
                    <line
                      key={ln.key}
                      x1={ln.x1}
                      y1={ln.y1}
                      x2={ln.x2}
                      y2={ln.y2}
                      stroke={ln.stroke}
                      strokeWidth={ln.strokeWidth}
                      strokeDasharray={ln.strokeDasharray}
                      strokeLinecap="round"
                    />
                  ))}
                  {spouseMarriageMarkers.map((m) => (
                    <g key={m.key} className="ft-marriage-marker">
                      <title>
                        {m.pairTitle
                          ? `${m.pairTitle} — ${m.isExSpouse ? t('family.ex_spouse') || 'Ex-spouse' : t('family.marriage_rings_title')}`
                          : t('family.marriage_rings_title')}
                      </title>
                      {/* Pill background */}
                      <rect
                        x={m.mx - 14}
                        y={m.y - 11}
                        width={28}
                        height={22}
                        rx={11}
                        fill="rgba(15,12,8,0.92)"
                        stroke={m.isExSpouse ? 'rgba(180,80,80,0.8)' : m.leftRingStroke}
                        strokeWidth={1.5}
                        strokeDasharray={m.isExSpouse ? '3 2' : undefined}
                      />
                      {/* ♥ or 💔 */}
                      <text
                        x={m.mx}
                        y={m.y + 6}
                        textAnchor="middle"
                        fontSize={m.isExSpouse ? 12 : 14}
                        fill={m.isExSpouse ? 'rgba(180,80,80,0.9)' : m.leftRingStroke}
                        fontFamily="serif"
                      >
                        {m.isExSpouse ? '💔' : '♥'}
                      </text>
                    </g>
                  ))}
                  {/* Snap lines — shown during node drag in edit mode */}
                  {editMode && snapLines.map((ln, i) => (
                    ln.axis === 'y' ? (
                      <line
                        key={`snap-${i}`}
                        x1={0} y1={ln.value} x2={canvasW} y2={ln.value}
                        stroke="rgba(99,210,255,0.7)"
                        strokeWidth={1.5 / transform.scale}
                        strokeDasharray={`${6 / transform.scale} ${4 / transform.scale}`}
                        pointerEvents="none"
                      />
                    ) : (
                      <line
                        key={`snap-${i}`}
                        x1={ln.value} y1={0} x2={ln.value} y2={canvasH}
                        stroke="rgba(99,210,255,0.7)"
                        strokeWidth={1.5 / transform.scale}
                        strokeDasharray={`${6 / transform.scale} ${4 / transform.scale}`}
                        pointerEvents="none"
                      />
                    )
                  ))}
                </svg>
                {displayGraph.nodes.map((n) => {
                  const id = sid(n.memorial_id)
                  const pos = effectivePositions[id]
                  if (!pos) return null
                  const { w: nw, h: nh } = genLayout.nodeSize

                  // Stub node: locked family member → render simplified locked card
                  if (n._stub) {
                    return (
                      <StubNodeCard
                        key={id}
                        memorial={n}
                        left={pos.x}
                        top={pos.y}
                        nodeW={nw}
                        nodeH={nh}
                        onUnlock={() => setVisibleFamilies(prev =>
                          prev.includes(n._family) ? prev : [...prev, n._family]
                        )}
                      />
                    )
                  }

                  return (
                    <GenTreeNodeCard
                      key={id}
                      memorial={n}
                      left={pos.x}
                      top={pos.y}
                      nodeW={nw}
                      nodeH={nh}
                      isRoot={n.memorial_id === displayGraph.root_id}
                      isBridge={bridgeNodeIds.has(id)}
                      clusterStyle={
                        genLayout.memorialClusterStyle?.[n.memorial_id] ??
                        genLayout.memorialClusterStyle?.[id]
                      }
                      relLabel={relLabels[id]}
                      onClick={(mid) => navigate(`/memorials/${mid}`)}
                      editMode={editMode}
                      onNodeDragStart={handleNodeDragStart}
                      onPortDragStart={handlePortDragStart}
                    />
                  )
                })}
                {/* Drawing edge overlay */}
                {drawingEdge && effectivePositions[drawingEdge.fromId] && (
                  <svg
                    style={{ position: 'absolute', top: 0, left: 0, width: canvasW, height: canvasH, pointerEvents: 'none', overflow: 'visible' }}
                  >
                    <line
                      x1={effectivePositions[drawingEdge.fromId].cx}
                      y1={effectivePositions[drawingEdge.fromId].cy}
                      x2={drawingEdge.curX}
                      y2={drawingEdge.curY}
                      stroke="rgba(200,170,100,0.9)"
                      strokeWidth={2}
                      strokeDasharray="8 4"
                      strokeLinecap="round"
                    />
                    <circle cx={drawingEdge.curX} cy={drawingEdge.curY} r={5} fill="rgba(200,170,100,0.9)" />
                  </svg>
                )}
              </>
            ) : (
              <>
                <svg
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: canvasW,
                    height: canvasH,
                    pointerEvents: 'none',
                    overflow: 'visible',
                  }}
                >
                  {treeData.connectors.map(([x1, y1, x2, y2], i) => (
                    <line
                      key={i}
                      x1={x1 * HW}
                      y1={y1 * HH}
                      x2={x2 * HW}
                      y2={y2 * HH}
                      stroke="rgba(196,168,130,0.65)"
                      strokeWidth="1.5"
                    />
                  ))}
                </svg>
                {treeData.nodes.map((extNode) => {
                  const mid = Number(extNode.id)
                  const csty =
                    clusterTheme.memorialClusterStyle?.[mid] ??
                    clusterTheme.memorialClusterStyle?.[extNode.id]
                  return (
                    <NodeCard
                      key={extNode.id}
                      extNode={extNode}
                      nodeMap={nodeMap}
                      isRoot={extNode.id === sid(displayGraph.root_id)}
                      relLabel={relLabels[extNode.id]}
                      clusterStyle={csty}
                      onClick={(id) => navigate(`/memorials/${id}`)}
                    />
                  )
                })}
              </>
            )}
          </div>
        </div>

        {/* Fullscreen toggle — top-right corner, like video player */}
        <button
          type="button"
          className="ft-canvas-fullscreen"
          onClick={toggleTreeFullscreen}
          data-tooltip={treeFullscreen ? t('family.exit_fullscreen') : t('family.fullscreen')}
        >
          {treeFullscreen ? (
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 3v3a2 2 0 0 1-2 2H3"/><path d="M21 8h-3a2 2 0 0 1-2-2V3"/><path d="M3 16h3a2 2 0 0 1 2 2v3"/><path d="M16 21v-3a2 2 0 0 1 2-2h3"/>
            </svg>
          ) : (
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/>
            </svg>
          )}
        </button>

        {/* Bottom-left: Edit + Add relation (editor/owner only) */}
        {canEdit && (
          <div className="ft-canvas-actions">
            {layoutMode === 'generations' && (
              <button
                type="button"
                className={`ft-canvas-action-btn${editMode ? ' ft-canvas-action-btn--active' : ''}`}
                onClick={() => {
                  const next = !editMode
                  setEditMode(next)
                  setShowAddForm(false)
                  // Save immediately when exiting edit mode
                  if (!next) saveLayout(nodeOverridesRef.current)
                }}
                data-tooltip={editMode ? (t('family.edit_mode_exit') || 'Save and exit edit mode') : 'Drag cards to rearrange the tree'}
              >
                {editMode ? '✓' : '✎'}
                <span className="ft-canvas-action-label">
                  {editMode ? (t('family.edit_mode_exit') || 'Done') : (t('family.edit_mode') || 'Edit')}
                </span>
              </button>
            )}
            {!editMode && (
              <button
                type="button"
                className="ft-canvas-action-btn ft-canvas-action-btn--primary"
                onClick={() => { setShowAddForm(!showAddForm); if (!showAddForm) loadAvailableMemorials() }}
                data-tooltip={showAddForm ? t('common.cancel') : 'Add a family member to the tree'}
              >
                {showAddForm ? '✕' : '+'}
                <span className="ft-canvas-action-label">
                  {showAddForm ? t('common.cancel') : t('family.add_relation')}
                </span>
              </button>
            )}
          </div>
        )}

        {/* Nav controls — bottom-right, always visible during zoom */}
        <div className="ft-canvas-nav">
          <button
            type="button"
            className="ft-canvas-nav-btn"
            onClick={fitWholeTree}
            data-tooltip={t('family.fit_whole_tree')}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3h6v6H3z"/><path d="M15 3h6v6h-6z"/><path d="M3 15h6v6H3z"/><path d="M15 15h6v6h-6z"/>
            </svg>
          </button>
          <button
            type="button"
            className="ft-canvas-nav-btn"
            onClick={centerOnThisPerson}
            data-tooltip={t('family.center_on_person')}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
            </svg>
          </button>
        </div>
        </div>
      )}


      {/* Relations list */}
      {relationships.length > 0 && (
        <div className="relations-list">
          <h3>{t('family.relations_title')}</h3>
          {relationships.map(rel => (
            <div key={rel.id} className="relation-item">
              <span>
                {rel.related_memorial_name} —{' '}
                {rel.relationship_type === 'custom' && rel.custom_label
                  ? rel.custom_label
                  : t(`family.${rel.relationship_type}`)}
              </span>
              {canEdit && (
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(rel.id)}>
                  {t('family.delete')}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
