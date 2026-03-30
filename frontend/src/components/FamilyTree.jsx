import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import { familyAPI, memorialsAPI } from '../api/client'
import ApiMediaImage from './ApiMediaImage'
import calcTree from 'relatives-tree'
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
function NodeCard({ extNode, nodeMap, isRoot, relLabel, onClick }) {
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

  return (
    <div
      className={[
        'ft-node',
        isRoot     ? 'ft-node--root'     : '',
        isDeceased ? 'ft-node--deceased' : '',
      ].filter(Boolean).join(' ')}
      style={{ position: 'absolute', left: x, top: y, width: NODE_W, height: NODE_H }}
      onClick={() => onClick(memorial.memorial_id)}
      title={memorial.name}
    >
      <div className="ft-node-avatar-wrap">
        <div className="ft-node-avatar">
          {memorial.cover_photo_id ? (
            <ApiMediaImage
              mediaId={memorial.cover_photo_id}
              thumbnail="small"
              alt={memorial.name}
              className="ft-node-img"
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

  // ── Derived data ───────────────────────────────────────────────
  // Map id → memorial object for fast lookup
  const nodeMap = useMemo(() => {
    if (!graphData?.nodes) return {}
    return Object.fromEntries(graphData.nodes.map(n => [sid(n.memorial_id), n]))
  }, [graphData])

  // relatives-tree layout
  const treeData = useMemo(() => {
    if (!graphData?.nodes?.length) return null
    try {
      const libNodes = toLibNodes(graphData.nodes, graphData.edges)
      return calcTree(libNodes, {
        rootId: sid(graphData.root_id),
        placeholders: true,
      })
    } catch (e) {
      console.error('calcTree error', e)
      return null
    }
  }, [graphData])

  // Relationship labels (BFS from root)
  const relLabels = useMemo(() => {
    if (!graphData) return {}
    return buildRelLabels(graphData.nodes, graphData.edges, graphData.root_id, t)
  }, [graphData, t])

  // Connected families: nodes present in full-tree but NOT placed by relatives-tree
  // (i.e., reachable only via custom edges from the structural family cluster)
  const connectedFamilies = useMemo(() => {
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
  const canvasW = treeData ? treeData.canvas.width  * HW : 800
  const canvasH = treeData ? treeData.canvas.height * HH : 400

  // Initial view: center on the opened memorial (API root_id === this page)
  useEffect(() => {
    if (!treeData || !canvasRef.current || !graphData?.root_id) return
    const rootNode = treeData.nodes.find(n => n.id === sid(graphData.root_id))
    const next = centerRootInViewport(canvasRef.current, rootNode)
    if (next) setTransform(next)
  }, [treeData, graphData?.root_id, memorialId])

  const fitWholeTree = useCallback(() => {
    if (!graphData || !treeData || !canvasRef.current) return
    const innerW = treeData.canvas.width * HW
    const innerH = treeData.canvas.height * HH
    const next = fitInnerInViewport(canvasRef.current, innerW, innerH)
    if (next) setTransform(next)
  }, [graphData, treeData])

  const centerOnThisPerson = useCallback(() => {
    if (!graphData?.root_id || !treeData || !canvasRef.current) return
    const rootNode = treeData.nodes.find(n => n.id === sid(graphData.root_id))
    const next = centerRootInViewport(canvasRef.current, rootNode)
    if (next) setTransform(next)
  }, [graphData?.root_id, treeData])

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

  const hasTree = !!treeData

  return (
    <div className="family-tree">
      {/* Header */}
      <div className="tree-header">
        <h2>{t('family.title')}</h2>
        <div className="tree-header-actions">
          {hasTree && (
            <>
              <span className="tree-node-count">
                {t('family.people_count')(graphData.nodes.length)}
              </span>
              <div className="tree-view-controls" role="group" aria-label={t('family.tree_controls')}>
                <button type="button" className="btn-tree-view" onClick={fitWholeTree}>
                  {t('family.fit_whole_tree')}
                </button>
                <button type="button" className="btn-tree-view" onClick={centerOnThisPerson}>
                  {t('family.center_on_person')}
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
      {hasTree && (
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
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
              transformOrigin: '0 0',
            }}
          >
            {/* Connectors — library gives us axis-aligned segments as [x1,y1,x2,y2] grid coords */}
            <svg
              style={{ position: 'absolute', top: 0, left: 0, width: canvasW, height: canvasH, pointerEvents: 'none', overflow: 'visible' }}
            >
              {treeData.connectors.map(([x1, y1, x2, y2], i) => (
                <line
                  key={i}
                  x1={x1 * HW} y1={y1 * HH}
                  x2={x2 * HW} y2={y2 * HH}
                  stroke="rgba(196,168,130,0.65)"
                  strokeWidth="1.5"
                />
              ))}
            </svg>

            {/* Nodes */}
            {treeData.nodes.map(extNode => (
              <NodeCard
                key={extNode.id}
                extNode={extNode}
                nodeMap={nodeMap}
                isRoot={extNode.id === sid(graphData.root_id)}
                relLabel={relLabels[extNode.id]}
                onClick={id => navigate(`/memorials/${id}`)}
              />
            ))}
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
