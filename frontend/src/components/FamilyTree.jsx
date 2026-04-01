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
import {
  filterGraphToKellyFamily,
  filterGraphToKellyAndAndersonFamily,
  filterGraphToThreeFamilies,
  filterGraphToFourFamilies,
  FAMILY_TREE_SCOPE,
} from '../utils/familyTreeKellyFilter.js'
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

function fitInnerInViewport(canvasEl, innerW, innerH) {
  const cw = canvasEl.offsetWidth
  const ch = canvasEl.offsetHeight
  if (!cw || !ch || !innerW || !innerH) return null
  const sx = (cw - 2 * VIEW_PAD) / innerW
  const sy = (ch - 2 * VIEW_PAD) / innerH
  const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.min(sx, sy)))
  const cx = innerW / 2
  const cy = innerH / 2
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
    // parent-like types → parent/child slots
    if (e.type === 'parent' || e.type === 'adoptive_parent' || e.type === 'step_parent') {
      childrenOf[src].add(tgt)
      parentsOf[tgt].add(src)
    } else if (e.type === 'child' || e.type === 'adoptive_child' || e.type === 'step_child') {
      parentsOf[src].add(tgt)
      childrenOf[tgt].add(src)
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
const LABEL_KEYS = {
  'parent':                 'rel_parent',
  'child':                  'rel_child',
  'spouse':                 'rel_spouse',
  'sibling':                'rel_sibling',
  'parent,parent':          'rel_grandparent',
  'child,child':            'rel_grandchild',
  'parent,sibling':         'rel_aunt_uncle',
  'sibling,child':          'rel_niece_nephew',
  'spouse,parent':          'rel_parent_in_law',
  'parent,spouse':          'rel_stepparent',
  'child,spouse':           'rel_child_in_law',
  'spouse,child':           'rel_stepchild',
  'parent,parent,parent':   'rel_great_grandparent',
  'child,child,child':      'rel_great_grandchild',
  'parent,parent,sibling':  'rel_great_aunt_uncle',
  'parent,sibling,child':   'rel_cousin',
}

function buildRelLabels(nodes, edges, rootId, t) {
  const adj = {}
  for (const e of edges) {
    const s = sid(e.source), tg = sid(e.target)
    if (!adj[s]) adj[s] = []
    adj[s].push({ n: tg, type: e.type })
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
      if (key) labels[n] = t(`family.${key}`)
      else if (path.length >= 3) labels[n] = t('family.rel_distant_prefix')
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
              thumbnail="large"
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

/** Карточка в режиме «поколения»: яркая рамка по кластеру фамилии + золото у перекрёстного брака */
function GenTreeNodeCard({
  memorial,
  left,
  top,
  nodeW,
  nodeH,
  isRoot,
  lineage,
  isBridge,
  clusterStyle,
  splitBorderStyle,
  relLabel,
  onClick,
}) {
  const isDeceased = !!memorial.death_year
  const cls = ['ft-node', 'ft-node--gen']
  if (isRoot) cls.push('ft-node--root')
  if (isBridge) cls.push('ft-node--bridge')
  if (!clusterStyle) {
    if (lineage === 'A') cls.push('ft-node--line-a')
    else if (lineage === 'B') cls.push('ft-node--line-b')
    else cls.push('ft-node--line-n')
  } else cls.push('ft-node--gen-cluster')
  if (isDeceased) cls.push('ft-node--deceased')
  else cls.push('ft-node--living')
  if (splitBorderStyle) cls.push('ft-node--gen-split')

  const clusterBox = clusterStyle
    ? {
        borderWidth: 3,
        borderStyle: 'solid',
        borderColor: clusterStyle.borderColor,
        boxShadow: isBridge
          ? `${clusterStyle.boxShadow}, 0 0 0 2px rgba(220, 175, 95, 0.72), 0 0 22px rgba(220, 175, 95, 0.26)`
          : clusterStyle.boxShadow,
      }
    : {}
  const visualBox = splitBorderStyle ? splitBorderStyle : clusterBox

  return (
    <div
      className={cls.filter(Boolean).join(' ')}
      style={{ position: 'absolute', left, top, width: nodeW, height: nodeH, ...visualBox }}
      onClick={() => onClick(memorial.memorial_id)}
      title={[memorial.name, relLabel && !isRoot ? relLabel : null].filter(Boolean).join(' — ')}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick(memorial.memorial_id)}
    >
      <div className="ft-node-avatar-wrap">
        {isDeceased && (
          <span className="ft-node-candle-badge ft-node-candle-badge--gen" title="Deceased" aria-hidden="true">
            🕯
          </span>
        )}
        <div className="ft-node-avatar">
          {memorial.cover_photo_id ? (
            <ApiMediaImage
              mediaId={memorial.cover_photo_id}
              thumbnail="large"
              alt={memorial.name}
              className="ft-node-img ft-node-img--hidpi"
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
          <ApiMediaImage mediaId={member.cover_photo_id} thumbnail="small" alt={member.name} className="ft-cf-img" />
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

// ── Main Component ─────────────────────────────────────────────────
export default function FamilyTree({ memorialId }) {
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
  const [treeFullscreen, setTreeFullscreen] = useState(false)
  const familyTreeRootRef = useRef(null)
  const dragRef  = useRef(null)
  const pinchRef = useRef(null)

  // ── Data loading ───────────────────────────────────────────────
  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const [fullRes, relsRes] = await Promise.all([
        familyAPI.getFullTree(memorialId, 6),
        familyAPI.getRelationships(memorialId),
      ])
      setGraphData(fullRes.data)
      setRelationships(Array.isArray(relsRes.data) ? relsRes.data : [])
    } catch (err) {
      console.error('Error loading family tree:', err)
    } finally {
      setLoading(false)
    }
  }, [memorialId])

  useEffect(() => { loadData() }, [loadData])

  /** Полный ответ API; для дерева — после фильтра по `FAMILY_TREE_SCOPE`. */
  const displayGraph = useMemo(() => {
    if (!graphData?.nodes?.length) return null
    if (FAMILY_TREE_SCOPE === 'full') return graphData
    if (FAMILY_TREE_SCOPE === 'kelly') return filterGraphToKellyFamily(graphData)
    if (FAMILY_TREE_SCOPE === 'kelly_anderson_third') return filterGraphToThreeFamilies(graphData)
    if (FAMILY_TREE_SCOPE === 'kelly_anderson_four') return filterGraphToFourFamilies(graphData)
    return filterGraphToKellyAndAndersonFamily(graphData)
  }, [graphData])

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

  const genLayout = useMemo(() => {
    if (!displayGraph?.nodes?.length) return null
    try {
      return buildGenerationLayout(displayGraph)
    } catch (e) {
      console.error('buildGenerationLayout', e)
      return null
    }
  }, [displayGraph])

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
    if (layoutMode !== 'generations' || !genLayout?.positions || !displayGraph?.edges) return []
    return buildOrthogonalConnectors({
      edges: displayGraph.edges,
      positions: genLayout.positions,
      nodeSize: genLayout.nodeSize,
      lineageMap: genLayout.lineage,
      nodes: displayGraph.nodes,
      memorialClusterStyle: genLayout.memorialClusterStyle,
    }).lines
  }, [layoutMode, genLayout, displayGraph?.edges, displayGraph?.nodes])

  const spouseMarriageMarkers = useMemo(() => {
    if (layoutMode !== 'generations' || !genLayout?.positions || !displayGraph?.edges) return []
    return getSpouseMarriageMarkers({
      edges: displayGraph.edges,
      positions: genLayout.positions,
      nodeSize: genLayout.nodeSize,
      lineageMap: genLayout.lineage,
      nodes: displayGraph.nodes,
      memorialClusterStyle: genLayout.memorialClusterStyle,
    })
  }, [layoutMode, genLayout, displayGraph?.edges, displayGraph?.nodes])

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

  // Connected families: nodes present in full-tree but NOT placed by relatives-tree
  // (i.e., reachable only via custom edges from the structural family cluster)
  const connectedFamilies = useMemo(() => {
    if (FAMILY_TREE_SCOPE !== 'full') return []
    if (!graphData || !treeData) return []
    const treeIds = new Set(treeData.nodes.filter(n => !n.placeholder).map(n => n.id))
    const nodeMap2 = Object.fromEntries(graphData.nodes.map(n => [String(n.memorial_id), n]))

    // Custom edges from the graph
    const customEdges = graphData.edges.filter(e => e.type === 'custom' || e.type === 'CUSTOM')
    if (!customEdges.length) return []

    // Orphan nodes: in graphData but not placed in the structural tree
    const orphanIds = new Set(
      graphData.nodes.map(n => String(n.memorial_id)).filter(id => !treeIds.has(id))
    )
    if (!orphanIds.size) return []

    // Structural adjacency among orphans (to group them into family clusters)
    const STRUCTURAL = new Set(['parent','child','spouse','sibling','partner','ex_spouse',
                                'adoptive_parent','adoptive_child','step_parent','step_child','half_sibling',
                                'PARENT','CHILD','SPOUSE','SIBLING','PARTNER'])
    const orphanAdj = {}
    for (const id of orphanIds) orphanAdj[id] = []
    for (const e of graphData.edges) {
      const s = String(e.source), tg = String(e.target)
      if (orphanIds.has(s) && orphanIds.has(tg) && STRUCTURAL.has(e.type)) {
        if (!orphanAdj[s]) orphanAdj[s] = []
        if (!orphanAdj[tg]) orphanAdj[tg] = []
        orphanAdj[s].push(tg)
        orphanAdj[tg].push(s)
      }
    }

    // BFS → connected components among orphans
    const seen = new Set()
    const clusters = []
    for (const start of orphanIds) {
      if (seen.has(start)) continue
      const clusterIds = []
      const q = [start]
      seen.add(start)
      while (q.length) {
        const cur = q.shift()
        clusterIds.push(cur)
        for (const nb of orphanAdj[cur] || []) {
          if (!seen.has(nb)) { seen.add(nb); q.push(nb) }
        }
      }

      // Find bridge custom edges connecting this cluster to the structural tree
      const bridges = customEdges.filter(e => {
        const s = String(e.source), tg = String(e.target)
        return (clusterIds.includes(s) && treeIds.has(tg)) ||
               (clusterIds.includes(tg) && treeIds.has(s))
      })

      // Derive cluster name from last words (surnames) of member names
      const surnameCounts = {}
      for (const id of clusterIds) {
        const m = nodeMap2[id]
        if (!m) continue
        const words = m.name.replace(/\(.*?\)/g, '').trim().split(/\s+/).filter(w => /^[A-Za-zА-Яа-яёЁ]+$/.test(w))
        const sn = words[words.length - 1]
        if (sn) surnameCounts[sn] = (surnameCounts[sn] || 0) + 1
      }
      const topSurnames = Object.entries(surnameCounts).sort((a,b) => b[1]-a[1]).slice(0,2).map(e => e[0])
      const clusterName = topSurnames.join(' & ') + ' Family'

      // Sort: bridge nodes first (the people with direct connections)
      const bridgeNodeIds = new Set(
        bridges.flatMap(e => [String(e.source), String(e.target)]).filter(id => clusterIds.includes(id))
      )
      const sortedIds = [...bridgeNodeIds, ...clusterIds.filter(id => !bridgeNodeIds.has(id))]

      // Collect unique bridge labels
      const bridgeLabels = [...new Set(bridges.map(e => e.label).filter(Boolean))]

      clusters.push({
        clusterName,
        members: sortedIds.map(id => nodeMap2[id]).filter(Boolean),
        bridgeLabels,
        bridgeCount: bridges.length,
      })
    }
    return clusters
  }, [graphData, treeData])

  // Canvas pixel size
  const canvasW = useMemo(() => {
    if (layoutMode === 'generations' && genLayout) return genLayout.canvas.width
    return treeData ? treeData.canvas.width * HW : 800
  }, [layoutMode, genLayout, treeData])

  const canvasH = useMemo(() => {
    if (layoutMode === 'generations' && genLayout) return genLayout.canvas.height
    return treeData ? treeData.canvas.height * HH : 400
  }, [layoutMode, genLayout, treeData])

  // Initial view: центр на открытом мемориале (root_id)
  useEffect(() => {
    if (!canvasRef.current || !displayGraph?.root_id) return
    if (layoutMode === 'generations' && genLayout?.positions) {
      const p = genLayout.positions[sid(displayGraph.root_id)]
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
  }, [layoutMode, genLayout, treeData, displayGraph?.root_id, memorialId])

  const fitWholeTree = useCallback(() => {
    if (!canvasRef.current) return
    if (layoutMode === 'generations' && genLayout) {
      const next = fitInnerInViewport(
        canvasRef.current,
        genLayout.canvas.width,
        genLayout.canvas.height
      )
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
    if (layoutMode === 'generations' && genLayout?.positions) {
      const p = genLayout.positions[sid(displayGraph.root_id)]
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
  }, [layoutMode, genLayout, displayGraph?.root_id, treeData])

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
        const next = Math.min(MAX_SCALE, Math.max(MIN_SCALE, prev.scale + delta * prev.scale))
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

  const onMouseMove = useCallback((e) => {
    if (!dragRef.current) return
    const { startTX, startTY, startX, startY } = dragRef.current
    setTransform(prev => ({ ...prev, x: startTX + e.clientX - startX, y: startTY + e.clientY - startY }))
  }, [])

  const onMouseUp = useCallback((e) => {
    dragRef.current = null
    e.currentTarget.style.cursor = 'grab'
  }, [])

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
      const next = Math.min(MAX_SCALE, Math.max(MIN_SCALE, pinchRef.current.scale * ratio))
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

  const showGenerations = layoutMode === 'generations' && !!genLayout
  const showPedigree = layoutMode === 'pedigree' && !!treeData
  const hasTree =
    !!displayGraph?.nodes?.length && (showGenerations || showPedigree)

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
            <div className="tree-layout-toggle" role="group" aria-label="Layout">
              <button
                type="button"
                className={`btn-tree-view${layoutMode === 'generations' ? ' btn-tree-view--active' : ''}`}
                onClick={() => setLayoutMode('generations')}
              >
                {t('family.layout_generations')}
              </button>
              <button
                type="button"
                className={`btn-tree-view${layoutMode === 'pedigree' ? ' btn-tree-view--active' : ''}`}
                onClick={() => setLayoutMode('pedigree')}
                disabled={!treeData}
              >
                {t('family.layout_pedigree')}
              </button>
            </div>
          )}
          {hasTree && (
            <>
              <span className="tree-node-count">
                {t('family.people_count')(displayGraph.nodes.length)}
              </span>
              <div className="tree-view-controls" role="group" aria-label={t('family.tree_controls')}>
                <button type="button" className="btn-tree-view" onClick={fitWholeTree}>
                  {t('family.fit_whole_tree')}
                </button>
                <button type="button" className="btn-tree-view" onClick={centerOnThisPerson}>
                  {t('family.center_on_person')}
                </button>
                <button type="button" className="btn-tree-view" onClick={toggleTreeFullscreen}>
                  {treeFullscreen ? t('family.exit_fullscreen') : t('family.fullscreen')}
                </button>
              </div>
            </>
          )}
          <button
            className="btn btn-primary"
            onClick={() => { setShowAddForm(!showAddForm); if (!showAddForm) loadAvailableMemorials() }}
          >
            {showAddForm ? t('common.cancel') : t('family.add_relation')}
          </button>
        </div>
      </div>
      {((FAMILY_TREE_SCOPE === 'kelly' ||
        FAMILY_TREE_SCOPE === 'kelly_anderson' ||
        FAMILY_TREE_SCOPE === 'kelly_anderson_third' ||
        FAMILY_TREE_SCOPE === 'kelly_anderson_four') &&
        graphData?.nodes?.length > 0 && (
        <p className="ft-kelly-only-banner" role="status">
          {t(
            FAMILY_TREE_SCOPE === 'kelly'
              ? 'family.kelly_only_banner'
              : FAMILY_TREE_SCOPE === 'kelly_anderson'
                ? 'family.kelly_anderson_banner'
                : FAMILY_TREE_SCOPE === 'kelly_anderson_third'
                  ? 'family.kelly_anderson_third_banner'
                  : 'family.kelly_anderson_four_banner'
          )}
        </p>
      ))}
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

      {/* Add form */}
      {showAddForm && (
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

      {/* Empty state */}
      {!hasTree && (
        <div className="ft-empty">
          <div className="ft-empty-title">{t('family.empty_title')}</div>
          <div className="ft-empty-hint">{t('family.empty_hint')}</div>
        </div>
      )}

      {/* Tree canvas */}
      {hasTree && (
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
                  {(genLayout.laneGapBands || []).map((band, gi) => (
                    <rect
                      key={`lane-gap-${gi}`}
                      x={band.x}
                      y={band.y}
                      width={band.width}
                      height={band.height}
                      fill="rgba(200, 175, 120, 0.07)"
                      stroke="rgba(200, 175, 120, 0.12)"
                      strokeWidth={1}
                      rx={6}
                    />
                  ))}
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
                    />
                  ))}
                  {spouseMarriageMarkers.map((m) => {
                    const showRings = transform.scale >= MIN_SCALE_MARRIAGE_RINGS
                    return (
                      <g
                        key={m.key}
                        transform={`translate(${m.mx}, ${m.y - 2})`}
                        className="ft-marriage-rings"
                        opacity={showRings ? 1 : 0}
                        style={{ transition: 'opacity 0.2s ease' }}
                      >
                        <title>{t('family.marriage_rings_title')}</title>
                        <circle
                          cx={-5.5}
                          cy={0}
                          r={6.5}
                          fill="none"
                          stroke={m.leftRingStroke}
                          strokeWidth={2.2}
                          strokeLinecap="round"
                        />
                        <circle
                          cx={5.5}
                          cy={0}
                          r={6.5}
                          fill="none"
                          stroke={m.rightRingStroke}
                          strokeWidth={2.2}
                          strokeLinecap="round"
                        />
                      </g>
                    )
                  })}
                </svg>
                {displayGraph.nodes.map((n) => {
                  const id = sid(n.memorial_id)
                  const pos = genLayout.positions[id]
                  if (!pos) return null
                  const { w: nw, h: nh } = genLayout.nodeSize
                  const curSurname = surnameOf(n.name)
                  const prevSurnameVal = previousSurname(n.name)
                  let splitBorderStyle = null
                  const vg = (n.voice_gender || '').toLowerCase()
                  // Рамка 50/50 — в первую очередь для «жены» (две фамилии в имени); явный male не трогаем.
                  if (vg !== 'male' && prevSurnameVal && curSurname && prevSurnameVal !== curSurname) {
                    const neighbors = []
                    for (const e of displayGraph.edges || []) {
                      const s = sid(e.source)
                      const t = sid(e.target)
                      if (s === id && genLayout.positions[t]) neighbors.push(displayGraph.nodes.find((x) => sid(x.memorial_id) === t))
                      else if (t === id && genLayout.positions[s]) neighbors.push(displayGraph.nodes.find((x) => sid(x.memorial_id) === s))
                    }
                    const fromOld = neighbors.filter((m) => m && surnameOf(m.name) === prevSurnameVal)
                    const oldRefs = fromOld.length ? fromOld : displayGraph.nodes.filter((m) => m && surnameOf(m.name) === prevSurnameVal)
                    const mcs = genLayout.memorialClusterStyle
                    let oldColor =
                      oldRefs.length > 0
                        ? (
                            mcs?.[oldRefs[0].memorial_id] ??
                            mcs?.[sid(oldRefs[0].memorial_id)]
                          )?.borderColor
                        : null
                    oldColor =
                      oldColor ||
                      borderColorForSurname(displayGraph.nodes, mcs, prevSurnameVal) ||
                      neutralSurnameRingStroke(prevSurnameVal)
                    let curColor =
                      (mcs?.[n.memorial_id] ?? mcs?.[id])?.borderColor ||
                      borderColorForSurname(displayGraph.nodes, mcs, curSurname) ||
                      neutralSurnameRingStroke(curSurname)

                    if (oldColor && curColor) {
                      let oldOnRight = true
                      if (fromOld.length) {
                        const avgX = fromOld
                          .map((m) => genLayout.positions[sid(m.memorial_id)]?.cx)
                          .filter((v) => typeof v === 'number')
                          .reduce((acc, v, _, arr) => acc + v / arr.length, 0)
                        if (Number.isFinite(avgX)) oldOnRight = avgX > pos.cx
                      }
                      const leftColor = oldOnRight ? curColor : oldColor
                      const rightColor = oldOnRight ? oldColor : curColor
                      const cSty = mcs?.[n.memorial_id] ?? mcs?.[id]
                      splitBorderStyle = buildSplitGenCardBorder({
                        leftColor,
                        rightColor,
                        clusterStyle: cSty,
                        isBridge: bridgeNodeIds.has(id),
                      })
                    }
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
                      lineage={genLayout.lineage[n.memorial_id]}
                      isBridge={bridgeNodeIds.has(id)}
                      clusterStyle={
                        genLayout.memorialClusterStyle?.[n.memorial_id] ??
                        genLayout.memorialClusterStyle?.[id]
                      }
                      splitBorderStyle={splitBorderStyle}
                      relLabel={relLabels[id]}
                      onClick={(mid) => navigate(`/memorials/${mid}`)}
                    />
                  )
                })}
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
      )}

      {/* Connected families (custom-edge clusters not shown in main tree) */}
      {connectedFamilies.length > 0 && (
        <div className="ft-connected-families">
          <div className="ft-cf-header">
            <span className="ft-cf-icon">⟷</span>
            <span className="ft-cf-title">Connected Families</span>
            <span className="ft-cf-hint">Historical connections — click any portrait to open their memorial</span>
          </div>
          {connectedFamilies.map((cluster, ci) => (
            <div key={ci} className="ft-cf-cluster">
              <div className="ft-cf-cluster-name">{cluster.clusterName}</div>
              {cluster.bridgeLabels.length > 0 && (
                <div className="ft-cf-bridge-labels">
                  {cluster.bridgeLabels.map((lbl, li) => (
                    <span key={li} className="ft-cf-bridge-tag">{lbl}</span>
                  ))}
                </div>
              )}
              <div className="ft-cf-cards">
                {cluster.members.slice(0, 8).map(m => (
                  <ConnectedFamilyCard
                    key={m.memorial_id}
                    member={m}
                    bridgeLabel={cluster.bridgeLabels[0] || ''}
                    onClick={id => navigate(`/memorials/${id}`)}
                  />
                ))}
                {cluster.members.length > 8 && (
                  <div className="ft-cf-more">+{cluster.members.length - 8} more</div>
                )}
              </div>
            </div>
          ))}
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
              <button className="btn btn-sm btn-danger" onClick={() => handleDelete(rel.id)}>
                {t('family.delete')}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
