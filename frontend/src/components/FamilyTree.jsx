import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { familyAPI, memorialsAPI } from '../api/client'
import './FamilyTree.css'

function FamilyTree({ memorialId }) {
  const navigate = useNavigate()
  const [tree, setTree] = useState(null)
  const [relationships, setRelationships] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    related_memorial_id: '',
    relationship_type: 'parent',
    notes: '',
  })
  const [availableMemorials, setAvailableMemorials] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [zoom, setZoom] = useState(1)
  const zoomContainerRef = useRef(null)

  useEffect(() => {
    loadData()
  }, [memorialId])

  useEffect(() => {
    const container = zoomContainerRef.current
    if (!container) return
    const handleWheel = (e) => {
      e.preventDefault()
      setZoom(prev => Math.min(2, Math.max(0.5, prev + (e.deltaY > 0 ? -0.1 : 0.1))))
    }
    container.addEventListener('wheel', handleWheel, { passive: false })
    return () => container.removeEventListener('wheel', handleWheel)
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [treeRes, relsRes] = await Promise.all([
        familyAPI.getFamilyTree(memorialId),
        familyAPI.getRelationships(memorialId),
      ])
      setTree(treeRes.data)
      setRelationships(Array.isArray(relsRes.data) ? relsRes.data : [])
    } catch (err) {
      console.error('Error loading family tree:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadAvailableMemorials = async () => {
    try {
      // TODO: Добавить endpoint для получения списка всех мемориалов
      // Пока используем заглушку
      setAvailableMemorials([])
    } catch (err) {
      console.error('Error loading memorials:', err)
    }
  }

  const handleAddRelationship = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await familyAPI.createRelationship(memorialId, formData)
      setFormData({ related_memorial_id: '', relationship_type: 'parent', notes: '' })
      setShowAddForm(false)
      await loadData()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при добавлении связи')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteRelationship = async (relationshipId) => {
    if (!confirm('Удалить эту связь?')) return
    try {
      await familyAPI.deleteRelationship(relationshipId)
      await loadData()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при удалении связи')
    }
  }

  const getInitials = (name) => {
    if (!name) return '?'
    return name.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase()
  }

  const RELATION_LABELS = {
    child: 'Ребёнок',
    spouse: 'Супруг/а',
    root: 'Страница',
  }

  const renderTreeNode = (node, level = 0, relationLabel = null) => {
    if (!node) return null

    const isDeceased = !!node.death_date
    const effectiveLabel = relationLabel || (level === 0 ? 'root' : null)

    return (
      <div key={node.memorial_id} className="tree-node" style={{ marginLeft: `${level * 40}px` }}>
        <div className="node-row">
          <div
            className={`node-card${isDeceased ? ' node-card--deceased' : ''}${level === 0 ? ' node-card--root' : ''}`}
            onClick={() => navigate(`/memorials/${node.memorial_id}`)}
            aria-label={`Перейти к мемориалу: ${node.name}`}
          >
            {effectiveLabel && (
              <span className={`node-relation-badge node-relation-badge--${effectiveLabel}`}>
                {RELATION_LABELS[effectiveLabel]}
              </span>
            )}
            <div className="node-body">
              <div className={`node-avatar${isDeceased ? ' node-avatar--deceased' : ''}`}>
                {node.cover_photo_url ? (
                  <img
                    src={node.cover_photo_url}
                    alt={node.name}
                    className="node-avatar-img"
                    onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
                  />
                ) : null}
                <span
                  className="node-avatar-initials"
                  style={node.cover_photo_url ? { display: 'none' } : {}}
                >{getInitials(node.name)}</span>
              </div>
              <div className="node-info">
                <div className="node-name">{node.name}</div>
                {node.birth_date && (
                  <div className="node-date">
                    {new Date(node.birth_date).getFullYear()}
                    {node.death_date && ` — ${new Date(node.death_date).getFullYear()}`}
                  </div>
                )}
              </div>
              {isDeceased && <span className="node-candle">∞</span>}
            </div>
          </div>

          {node.spouses && node.spouses.length > 0 && node.spouses.map((spouse) => (
            <div key={spouse.memorial_id} className="spouse-group">
              <div className="marriage-connector">
                <div className="marriage-line" />
                <span className="marriage-symbol">∞</span>
                <div className="marriage-line" />
              </div>
              <div
                className="node-card spouse"
                onClick={() => navigate(`/memorials/${spouse.memorial_id}`)}
                aria-label={`Перейти к мемориалу: ${spouse.name}`}
              >
                <span className="node-relation-badge node-relation-badge--spouse">
                  {RELATION_LABELS.spouse}
                </span>
                <div className="node-body">
                  <div className="node-avatar">
                    {spouse.cover_photo_url ? (
                      <img
                        src={spouse.cover_photo_url}
                        alt={spouse.name}
                        className="node-avatar-img"
                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
                      />
                    ) : null}
                    <span
                      className="node-avatar-initials"
                      style={spouse.cover_photo_url ? { display: 'none' } : {}}
                    >{getInitials(spouse.name)}</span>
                  </div>
                  <div className="node-info">
                    <div className="node-name">{spouse.name}</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {Array.isArray(node.children) && node.children.length > 0 && (
          <div className="children">
            {node.children.map((child) => renderTreeNode(child, level + 1, 'child'))}
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return <div className="loading">Загрузка семейного дерева...</div>
  }

  return (
    <div className="family-tree">
      <div className="tree-header">
        <h2>Семейное дерево</h2>
        <button
          className="btn btn-primary"
          onClick={() => {
            setShowAddForm(!showAddForm)
            if (!showAddForm) loadAvailableMemorials()
          }}
        >
          {showAddForm ? 'Отмена' : 'Добавить связь'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleAddRelationship} className="relationship-form">
          <div className="form-group">
            <label htmlFor="related_memorial_id">ID связанного мемориала *</label>
            <input
              type="number"
              id="related_memorial_id"
              value={formData.related_memorial_id}
              onChange={(e) =>
                setFormData({ ...formData, related_memorial_id: parseInt(e.target.value) })
              }
              required
              placeholder="Введите ID мемориала"
            />
            <small>Введите ID существующего мемориала</small>
          </div>

          <div className="form-group">
            <label htmlFor="relationship_type">Тип связи *</label>
            <select
              id="relationship_type"
              value={formData.relationship_type}
              onChange={(e) =>
                setFormData({ ...formData, relationship_type: e.target.value })
              }
              required
            >
              <option value="parent">Родитель</option>
              <option value="child">Ребенок</option>
              <option value="spouse">Супруг/супруга</option>
              <option value="sibling">Брат/сестра</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="notes">Заметки (опционально)</label>
            <textarea
              id="notes"
              value={formData.notes}
              onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
              }
              rows="2"
              placeholder="Дополнительная информация о связи"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Сохранение...' : 'Добавить связь'}
          </button>
        </form>
      )}

      <div className="tree-section">
        <h3>Визуализация дерева</h3>
        {tree && tree.root ? (
          <div className="tree-container" ref={zoomContainerRef}>
            <div className="tree-zoom-hint">Scroll to zoom · {Math.round(zoom * 100)}%</div>
            <div
              className="zoom-wrapper"
              style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
            >
              {renderTreeNode(tree.root)}
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-tree-icon">🌳</div>
            <p>Здесь будет жить история вашей семьи</p>
            <p className="hint">Добавьте первую связь, чтобы начать строить дерево</p>
          </div>
        )}
      </div>

      <div className="relationships-section">
        <h3>Все связи</h3>
        {relationships.length === 0 ? (
          <div className="empty-state">
            <p>Пока нет добавленных связей</p>
          </div>
        ) : (
          <div className="relationships-list">
            {relationships.map((rel) => (
              <div key={rel.id} className="relationship-item">
                <div className="relationship-info">
                  <span className="relationship-type">
                    {rel.relationship_type === 'parent' && '👨‍👩‍👧 Родитель'}
                    {rel.relationship_type === 'child' && '👶 Ребенок'}
                    {rel.relationship_type === 'spouse' && '💑 Супруг/супруга'}
                    {rel.relationship_type === 'sibling' && '👫 Брат/сестра'}
                  </span>
                  <span className="relationship-name">
                    {rel.related_memorial_name || `ID: ${rel.related_memorial_id}`}
                  </span>
                  {rel.notes && <span className="relationship-notes">{rel.notes}</span>}
                </div>
                <button
                  className="btn-delete"
                  onClick={() => handleDeleteRelationship(rel.id)}
                >
                  Удалить
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default FamilyTree
