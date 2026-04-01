import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { memorialsAPI, invitesAPI, accessAPI } from '../api/client'
import ApiMediaImage from '../components/ApiMediaImage'
import { useLanguage } from '../contexts/LanguageContext'
import MediaGallery from '../components/MediaGallery'
import MemoryList from '../components/MemoryList'
import AvatarChat from '../components/AvatarChat'
import FamilyTree from '../components/FamilyTree'
import LifeTimeline from '../components/LifeTimeline'
import { buildContributeInviteUrl } from '../utils/inviteUrl'
import { normalizeFlexibleDateInput, parseDateFieldForSubmit } from '../utils/dateInput'
import './MemorialDetail.css'

const MEMORIAL_TABS = new Set(['media', 'memories', 'chat', 'family', 'timeline'])

function MemorialDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { t, lang } = useLanguage()
  const [memorial, setMemorial] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('media')
  const [mountedTabs, setMountedTabs] = useState(new Set(['media']))
  const [editing, setEditing] = useState(false)
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
    birth_date: '',
    death_date: '',
    is_public: false,
    voice_gender: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // QR modal state
  const [showQRModal, setShowQRModal] = useState(false)
  const [qrBlobUrl, setQrBlobUrl] = useState(null)
  const [qrLoading, setQrLoading] = useState(false)

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteLabel, setInviteLabel] = useState('')
  const [creatingInvite, setCreatingInvite] = useState(false)
  const [createdInviteUrl, setCreatedInviteUrl] = useState(null)
  const [inviteList, setInviteList] = useState([])
  const [inviteListLoading, setInviteListLoading] = useState(false)

  // Access management state
  const [showAccessPanel, setShowAccessPanel] = useState(false)
  const [accessList, setAccessList] = useState([])
  const [accessListLoading, setAccessListLoading] = useState(false)
  const [accessGrantEmail, setAccessGrantEmail] = useState('')
  const [accessGrantRole, setAccessGrantRole] = useState('viewer')
  const [grantingAccess, setGrantingAccess] = useState(false)
  const [accessError, setAccessError] = useState(null)
  const [pendingRequests, setPendingRequests] = useState([])
  const [pendingRequestsLoading, setPendingRequestsLoading] = useState(false)

  useEffect(() => {
    loadMemorial()
  }, [id])

  useEffect(() => {
    setMountedTabs(new Set(['media']))
    setActiveTab('media')
    setQrBlobUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return null
    })
    setShowQRModal(false)
  }, [id])

  useEffect(() => {
    const tab = searchParams.get('tab')
    if (!tab || !MEMORIAL_TABS.has(tab)) return
    setActiveTab(tab)
    setMountedTabs((prev) => new Set([...prev, tab]))
  }, [id, searchParams])

  const loadMemorial = async () => {
    try {
      setLoading(true)
      const response = await memorialsAPI.get(id)
      setMemorial(response.data)
      // Заполняем форму редактирования
      setEditFormData({
        name: response.data.name || '',
        description: response.data.description || '',
        birth_date: response.data.birth_date
          ? new Date(response.data.birth_date).toISOString().split('T')[0]
          : '',
        death_date: response.data.death_date
          ? new Date(response.data.death_date).toISOString().split('T')[0]
          : '',
        is_public: response.data.is_public || false,
        voice_gender: response.data.voice_gender || '',
      })
    } catch (err) {
      setError(err.response?.data?.detail || t('detail.error_load'))
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(t('detail.delete_confirm', { name: memorial.name }))) return
    setDeleting(true)
    try {
      await memorialsAPI.delete(id)
      navigate('/')
    } catch (err) {
      alert(err.response?.data?.detail || t('detail.delete_error'))
      setDeleting(false)
    }
  }

  const handleShowQR = async () => {
    setShowQRModal(true)
    if (qrBlobUrl) return
    setQrLoading(true)
    try {
      const response = await memorialsAPI.getQR(id)
      setQrBlobUrl(URL.createObjectURL(response.data))
    } catch (err) {
      alert(t('detail.qr_error'))
      setShowQRModal(false)
    } finally {
      setQrLoading(false)
    }
  }

  const handleDownloadQR = () => {
    if (!qrBlobUrl) return
    const a = document.createElement('a')
    a.href = qrBlobUrl
    a.download = `memorial_${id}_qr.png`
    a.click()
  }

  const handleSetCover = async (mediaId) => {
    try {
      await memorialsAPI.setCover(id, mediaId)
      await loadMemorial()
    } catch (err) {
      alert(err.response?.data?.detail || t('detail.cover_error'))
    }
  }

  const handleEditDateBlur = (field) => (e) => {
    const v = e.target.value.trim()
    if (!v) return
    const n = normalizeFlexibleDateInput(v)
    if (n && n !== e.target.value) {
      setEditFormData((prev) => ({ ...prev, [field]: n }))
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    const br = parseDateFieldForSubmit(editFormData.birth_date)
    const dr = parseDateFieldForSubmit(editFormData.death_date)
    if (!br.ok || !dr.ok) {
      alert(t('detail.date_invalid'))
      return
    }
    setSubmitting(true)
    try {
      const submitData = {
        ...editFormData,
        birth_date: br.iso ? `${br.iso}T00:00:00Z` : null,
        death_date: dr.iso ? `${dr.iso}T00:00:00Z` : null,
        voice_gender: editFormData.voice_gender || null,
      }
      await memorialsAPI.update(id, submitData)
      setEditing(false)
      await loadMemorial()
    } catch (err) {
      const errorData = err.response?.data
      if (errorData?.detail) {
        if (Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err) => {
            const field = err.loc?.join('.') || t('detail.validation_field')
            return `${field}: ${err.msg}`
          })
          alert(errorMessages.join('\n'))
        } else {
          alert(errorData.detail)
        }
      } else {
        alert(t('detail.update_error'))
      }
    } finally {
      setSubmitting(false)
    }
  }

  const openInviteModal = async () => {
    setShowInviteModal(true)
    setCreatedInviteUrl(null)
    setInviteLabel('')
    setInviteListLoading(true)
    try {
      const res = await invitesAPI.list(id)
      setInviteList(res.data)
    } catch {
      setInviteList([])
    } finally {
      setInviteListLoading(false)
    }
  }

  const handleCreateInvite = async () => {
    setCreatingInvite(true)
    try {
      const res = await invitesAPI.create(id, { label: inviteLabel || null })
      setCreatedInviteUrl(buildContributeInviteUrl(res.data.token) || res.data.invite_url)
      setInviteList(prev => [...prev, res.data])
    } catch {
      alert(t('detail.invite_create_error'))
    } finally {
      setCreatingInvite(false)
    }
  }

  const handleRevokeInvite = async (token) => {
    if (!confirm(t('detail.revoke_invite_confirm'))) return
    try {
      await invitesAPI.revoke(token)
      setInviteList(prev => prev.filter(i => i.token !== token))
      if (createdInviteUrl && createdInviteUrl.includes(token)) {
        setCreatedInviteUrl(null)
      }
    } catch {
      alert(t('detail.revoke_invite_error'))
    }
  }

  const openAccessPanel = async () => {
    setShowAccessPanel(true)
    setAccessError(null)
    setAccessListLoading(true)
    setPendingRequestsLoading(true)
    try {
      const [accessRes, requestsRes] = await Promise.all([
        accessAPI.list(id),
        accessAPI.listRequests(id).catch(() => ({ data: [] })),
      ])
      setAccessList(accessRes.data)
      setPendingRequests(requestsRes.data)
    } catch {
      setAccessList([])
    } finally {
      setAccessListLoading(false)
      setPendingRequestsLoading(false)
    }
  }

  const handleApproveRequest = async (requestId) => {
    try {
      const res = await accessAPI.approveRequest(id, requestId)
      setPendingRequests(prev => prev.filter(r => r.id !== requestId))
      setAccessList(prev => {
        const idx = prev.findIndex(e => e.user_id === res.data.user_id)
        if (idx >= 0) return prev.map((e, i) => i === idx ? res.data : e)
        return [...prev, res.data]
      })
    } catch (err) {
      setAccessError(err.response?.data?.detail || t('detail.access_approve_error'))
    }
  }

  const handleRejectRequest = async (requestId) => {
    try {
      await accessAPI.rejectRequest(id, requestId)
      setPendingRequests(prev => prev.filter(r => r.id !== requestId))
    } catch (err) {
      setAccessError(err.response?.data?.detail || t('detail.access_reject_error'))
    }
  }

  const handleGrantAccess = async () => {
    if (!accessGrantEmail.trim()) return
    setGrantingAccess(true)
    setAccessError(null)
    try {
      const res = await accessAPI.grant(id, { email: accessGrantEmail.trim(), role: accessGrantRole })
      setAccessList(prev => [...prev, res.data])
      setAccessGrantEmail('')
    } catch (err) {
      setAccessError(err.response?.data?.detail || t('detail.access_grant_error'))
    } finally {
      setGrantingAccess(false)
    }
  }

  const handleUpdateAccessRole = async (userId, newRole) => {
    setAccessError(null)
    try {
      const res = await accessAPI.update(id, userId, { role: newRole })
      setAccessList(prev => prev.map(e => e.user_id === userId ? res.data : e))
    } catch (err) {
      setAccessError(err.response?.data?.detail || t('detail.access_role_error'))
    }
  }

  const handleRevokeAccess = async (userId) => {
    if (!confirm(t('detail.access_revoke_confirm'))) return
    setAccessError(null)
    try {
      await accessAPI.revoke(id, userId)
      setAccessList(prev => prev.filter(e => e.user_id !== userId))
    } catch (err) {
      setAccessError(err.response?.data?.detail || t('detail.access_revoke_error'))
    }
  }

  if (loading) {
    return <div className="loading">{t('memorial.loading')}</div>
  }

  if (error || !memorial) {
    return <div className="error-message">{error || t('memorial.not_found')}</div>
  }

  const formatYear = (d) => d ? new Date(d).getFullYear() : null
  const birthYear = formatYear(memorial.birth_date)
  const deathYear = formatYear(memorial.death_date)

  const role = memorial.current_user_role  // 'owner' | 'editor' | 'viewer' | null
  const isOwner = role === 'owner'
  const canEdit = role === 'owner' || role === 'editor'

  return (
    <div className="memorial-detail">

      {/* ── Hero Header ── */}
      <div className="memorial-hero">
        {memorial.cover_photo_id ? (
          <ApiMediaImage
            mediaId={memorial.cover_photo_id}
            thumbnail="large"
            alt={memorial.name}
            className="memorial-hero-img"
            fallback={<div className="memorial-hero-empty">🕯</div>}
          />
        ) : (
          <div className="memorial-hero-empty">🕯</div>
        )}
        <div className="memorial-hero-overlay" />

        <div className="memorial-hero-info">
          <div className="memorial-hero-text">
            <h1 className="memorial-hero-name">{memorial.name}</h1>
            {(birthYear || deathYear) && (
              <p className="memorial-hero-dates">
                {birthYear && birthYear}
                {birthYear && deathYear && ' — '}
                {deathYear && deathYear}
              </p>
            )}
          </div>

          <div className="memorial-hero-actions">
            {canEdit && (
              <button
                className="btn-edit-header"
                onClick={() => setEditing(true)}
                title={t('detail.btn_edit')}
              >
                ✎ {t('detail.btn_edit')}
              </button>
            )}
            <button
              className="btn-icon"
              onClick={handleShowQR}
              title={t('detail.btn_qr')}
            >
              ⊞ {t('detail.btn_qr')}
            </button>
            {isOwner && (
              <button
                className="btn-icon"
                onClick={openInviteModal}
                title={t('detail.btn_invite')}
              >
                ✉ {t('detail.btn_invite')}
              </button>
            )}
            {isOwner && (
              <button
                className="btn-icon"
                onClick={openAccessPanel}
                title={t('detail.btn_access')}
              >
                🔑 {t('detail.btn_access')}
              </button>
            )}
            {isOwner && (
              <button
                className="btn-danger"
                onClick={handleDelete}
                disabled={deleting}
                title={t('detail.btn_delete')}
              >
                {deleting ? t('detail.deleting') : '✕'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Edit Form ── */}
      {editing && canEdit && (
        <div className="memorial-edit-wrap">
          <h2 className="edit-form-title">{t('detail.edit_title')}</h2>
          <form onSubmit={handleUpdate} className="edit-form" lang={lang === 'en' ? 'en' : 'ru'}>
            <div className="form-group">
              <label htmlFor="name">{t('detail.label_name')}</label>
              <input
                type="text"
                id="name"
                value={editFormData.name}
                onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="description">{t('detail.label_description')}</label>
              <textarea
                id="description"
                value={editFormData.description}
                onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                rows="3"
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="birth_date">{t('detail.label_birth')}</label>
                <input
                  type="text"
                  id="birth_date"
                  value={editFormData.birth_date}
                  onChange={(e) => setEditFormData({ ...editFormData, birth_date: e.target.value })}
                  onBlur={handleEditDateBlur('birth_date')}
                  placeholder={t('detail.date_placeholder')}
                  autoComplete="off"
                  inputMode="text"
                  spellCheck={false}
                />
              </div>
              <div className="form-group">
                <label htmlFor="death_date">{t('detail.label_death')}</label>
                <input
                  type="text"
                  id="death_date"
                  value={editFormData.death_date}
                  onChange={(e) => setEditFormData({ ...editFormData, death_date: e.target.value })}
                  onBlur={handleEditDateBlur('death_date')}
                  placeholder={t('detail.date_placeholder')}
                  autoComplete="off"
                  inputMode="text"
                  spellCheck={false}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={editFormData.is_public}
                  onChange={(e) => setEditFormData({ ...editFormData, is_public: e.target.checked })}
                />
                {t('detail.public_memorial')}
              </label>
            </div>
            <div className="form-group">
              <label htmlFor="edit-voice_gender">{t('detail.voice_avatar')}</label>
              <select
                id="edit-voice_gender"
                value={editFormData.voice_gender}
                onChange={(e) => setEditFormData({ ...editFormData, voice_gender: e.target.value })}
              >
                <option value="">{t('detail.voice_unspecified')}</option>
                <option value="male">{t('detail.voice_male')}</option>
                <option value="female">{t('detail.voice_female')}</option>
              </select>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? t('detail.saving') : t('detail.save')}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => { setEditing(false); loadMemorial() }}
              >
                {t('detail.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── Description ── */}
      {!editing && memorial.description && (
        <div className="memorial-description-strip">
          <p className="memorial-description">{memorial.description}</p>
        </div>
      )}

      <div className="tabs-wrap">
      <div className="tabs">
        {[
          { key: 'media', label: t('tabs.media') },
          { key: 'memories', label: t('tabs.memories') },
          { key: 'chat', label: t('tabs.chat') },
          { key: 'family', label: t('tabs.family') },
          { key: 'timeline', label: t('tabs.timeline') },
        ].map(({ key, label }) => (
          <button
            key={key}
            className={activeTab === key ? 'active' : ''}
            onClick={() => {
              setActiveTab(key)
              setMountedTabs(prev => new Set([...prev, key]))
            }}
          >
            {label}
          </button>
        ))}
      </div>
      </div>

      <div className="tab-content">
        {mountedTabs.has('media') && (
          <div style={{ display: activeTab === 'media' ? '' : 'none' }}>
            <MediaGallery
              memorialId={id}
              onReload={loadMemorial}
              coverPhotoId={memorial.cover_photo_id}
              onSetCover={canEdit ? handleSetCover : undefined}
              canEdit={canEdit}
            />
          </div>
        )}
        {mountedTabs.has('memories') && (
          <div style={{ display: activeTab === 'memories' ? '' : 'none' }}>
            <MemoryList memorialId={id} memorialName={memorial.name} onReload={loadMemorial} canEdit={canEdit} />
          </div>
        )}
        {mountedTabs.has('chat') && (
          <div style={{ display: activeTab === 'chat' ? '' : 'none' }}>
            <AvatarChat
              memorialId={id}
              coverPhotoId={memorial.cover_photo_id}
              memorialName={memorial.name}
            />
          </div>
        )}
        {mountedTabs.has('family') && (
          <div style={{ display: activeTab === 'family' ? '' : 'none' }}>
            <FamilyTree memorialId={id} />
          </div>
        )}
        {mountedTabs.has('timeline') && (
          <div style={{ display: activeTab === 'timeline' ? '' : 'none' }}>
            <LifeTimeline memorialId={id} />
          </div>
        )}
      </div>

      {showQRModal && (
        <div className="modal-overlay" onClick={() => setShowQRModal(false)}>
          <div className="modal-content qr-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{t('detail.qr_modal_title')}</h3>
              <button className="modal-close" onClick={() => setShowQRModal(false)}>✕</button>
            </div>
            <div className="qr-modal-body">
              {qrLoading ? (
                <div className="qr-loading">{t('detail.qr_generating')}</div>
              ) : qrBlobUrl ? (
                <>
                  <img src={qrBlobUrl} alt="QR" className="qr-image" />
                  <p className="qr-hint" dangerouslySetInnerHTML={{ __html: t('detail.qr_hint') }} />
                  <div className="qr-url-row">
                    <code className="qr-url">{window.location.origin}/memorial/{id}</code>
                    <button className="btn-copy" onClick={() => navigator.clipboard.writeText(`${window.location.origin}/memorial/${id}`).then(() => alert(t('detail.link_copied')))}>
                      {t('detail.copy')}
                    </button>
                  </div>
                  <button className="btn btn-secondary" onClick={handleDownloadQR}>
                    {t('detail.download_png')}
                  </button>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {showAccessPanel && (
        <div className="modal-overlay" onClick={() => setShowAccessPanel(false)}>
          <div className="modal-content invite-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{t('detail.access_title')}</h3>
              <button className="modal-close" onClick={() => setShowAccessPanel(false)}>✕</button>
            </div>

            <div className="invite-form">
              <label>{t('detail.access_email')}</label>
              <input
                type="email"
                value={accessGrantEmail}
                onChange={e => setAccessGrantEmail(e.target.value)}
                placeholder="user@example.com"
              />
              <label>{t('detail.access_role')}</label>
              <select
                value={accessGrantRole}
                onChange={e => setAccessGrantRole(e.target.value)}
              >
                <option value="viewer">{t('detail.role_viewer')}</option>
                <option value="editor">{t('detail.role_editor')}</option>
              </select>
              <button
                className="btn btn-primary"
                onClick={handleGrantAccess}
                disabled={grantingAccess || !accessGrantEmail.trim()}
              >
                {grantingAccess ? t('detail.granting') : t('detail.grant_access')}
              </button>
              {accessError && <p className="error-message" style={{ marginTop: '8px' }}>{accessError}</p>}
            </div>

            {(pendingRequestsLoading || pendingRequests.length > 0) && (
              <div className="invite-list-section">
                <h4>{t('detail.access_requests')} {pendingRequests.length > 0 && `(${pendingRequests.length})`}</h4>
                {pendingRequestsLoading ? (
                  <p className="invite-list-empty">{t('detail.loading_short')}</p>
                ) : (
                  <ul className="invite-list">
                    {pendingRequests.map(req => (
                      <li key={req.id} className="invite-item" style={{ alignItems: 'flex-start', gap: '8px', flexWrap: 'wrap' }}>
                        <div style={{ flex: 1 }}>
                          <span className="invite-item-label">{req.user_email}</span>
                          <span style={{ color: '#888', fontSize: '12px', marginLeft: '6px' }}>
                            → {req.requested_role}
                          </span>
                          {req.message && (
                            <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#aaa' }}>{req.message}</p>
                          )}
                        </div>
                        <button
                          className="btn btn-primary"
                          style={{ fontSize: '12px', padding: '4px 10px' }}
                          onClick={() => handleApproveRequest(req.id)}
                        >
                          {t('detail.approve')}
                        </button>
                        <button
                          className="btn-revoke"
                          onClick={() => handleRejectRequest(req.id)}
                        >
                          {t('detail.reject')}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <div className="invite-list-section">
              <h4>{t('detail.users_with_access')}</h4>
              {accessListLoading ? (
                <p className="invite-list-empty">{t('detail.loading_short')}</p>
              ) : accessList.length === 0 ? (
                <p className="invite-list-empty">{t('detail.no_access_users')}</p>
              ) : (
                <ul className="invite-list">
                  {accessList.map(entry => (
                    <li key={entry.user_id} className="invite-item" style={{ alignItems: 'center', gap: '8px' }}>
                      <span className="invite-item-label" style={{ flex: 1 }}>
                        {entry.user_email}
                        {entry.user_full_name && ` (${entry.user_full_name})`}
                      </span>
                      {entry.role === 'owner' ? (
                        <span style={{ color: '#888', fontSize: '13px' }}>{t('detail.owner')}</span>
                      ) : (
                        <select
                          value={entry.role}
                          onChange={e => handleUpdateAccessRole(entry.user_id, e.target.value)}
                          style={{ fontSize: '13px', padding: '2px 6px' }}
                        >
                          <option value="viewer">viewer</option>
                          <option value="editor">editor</option>
                        </select>
                      )}
                      {entry.role !== 'owner' && (
                        <button
                          className="btn-revoke"
                          onClick={() => handleRevokeAccess(entry.user_id)}
                        >
                          {t('detail.revoke')}
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {showInviteModal && (
        <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="modal-content invite-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{t('detail.invite_title')}</h3>
              <button className="modal-close" onClick={() => setShowInviteModal(false)}>✕</button>
            </div>

            <div className="invite-form">
              <label>{t('detail.invite_name_label')}</label>
              <input
                type="text"
                value={inviteLabel}
                onChange={e => setInviteLabel(e.target.value)}
                placeholder={t('detail.invite_placeholder')}
              />
              <button
                className="btn btn-primary"
                onClick={handleCreateInvite}
                disabled={creatingInvite}
              >
                {creatingInvite ? t('detail.creating') : t('detail.create_link')}
              </button>
            </div>

            {createdInviteUrl && (
              <div className="invite-created">
                <p>{t('detail.link_created')}</p>
                <div className="invite-url-row">
                  <code className="invite-url">{createdInviteUrl}</code>
                  <button
                    className="btn-copy"
                    onClick={() => {
                      navigator.clipboard.writeText(createdInviteUrl)
                        .then(() => alert(t('detail.link_copied')))
                    }}
                  >
                    {t('detail.copy')}
                  </button>
                </div>
              </div>
            )}

            <div className="invite-list-section">
              <h4>{t('detail.active_links')}</h4>
              {inviteListLoading ? (
                <p className="invite-list-empty">{t('detail.loading_short')}</p>
              ) : inviteList.length === 0 ? (
                <p className="invite-list-empty">{t('detail.no_links')}</p>
              ) : (
                <ul className="invite-list">
                  {inviteList.map(inv => (
                    <li key={inv.token} className="invite-item">
                      <span className="invite-item-label">{inv.label || t('detail.no_name')}</span>
                      <span className="invite-item-uses">{t('detail.uses_count', { n: inv.uses_count })}</span>
                      <button
                        className="btn-revoke"
                        onClick={() => handleRevokeInvite(inv.token)}
                      >
                        {t('detail.revoke')}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MemorialDetail

