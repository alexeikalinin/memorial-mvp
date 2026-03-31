import { useState, useEffect, useRef } from 'react'
import { memorialsAPI, aiAPI, invitesAPI } from '../api/client'
import { aboutName } from '../utils/declension'
import { buildContributeInviteUrl } from '../utils/inviteUrl'
import { useLanguage } from '../contexts/LanguageContext'
import './MemoryList.css'

function formatApiDetail(err) {
  const d = err.response?.data?.detail
  if (!d) return err.message || ''
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    return d.map((x) => (typeof x === 'object' && x?.msg ? x.msg : String(x))).join('; ')
  }
  return String(d)
}

function MemoryList({ memorialId, memorialName, onReload, canEdit = true, onOpenAvatarChat }) {
  const { lang, t } = useLanguage()
  const locale = lang === 'en' ? 'en-US' : 'ru-RU'
  const [memories, setMemories] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ title: '', content: '', event_date: '' })
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editFormData, setEditFormData] = useState({ title: '', content: '', event_date: '' })
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [sharePanel, setSharePanel] = useState(null)
  const [sharingLoading, setSharingLoading] = useState(false)
  const [urlCopied, setUrlCopied] = useState(false)
  const [textCopied, setTextCopied] = useState(false)

  // Аудио-транскрипция
  const [showAudio, setShowAudio] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [transcribing, setTranscribing] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  useEffect(() => {
    loadMemories(debouncedQuery)
  }, [memorialId, debouncedQuery])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      chunksRef.current = []
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        setAudioUrl(URL.createObjectURL(blob))
        stream.getTracks().forEach((t) => t.stop())
      }
      recorder.start()
      mediaRecorderRef.current = recorder
      setIsRecording(true)
    } catch {
      alert(t('memoryList.mic_denied'))
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }

  const handleAudioFileSelect = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setAudioBlob(file)
    setAudioUrl(URL.createObjectURL(file))
  }

  const handleTranscribe = async () => {
    if (!audioBlob) return
    setTranscribing(true)
    try {
      const file = audioBlob instanceof File
        ? audioBlob
        : new File([audioBlob], 'recording.webm', { type: 'audio/webm' })
      const response = await aiAPI.transcribe(file)
      const text = response.data.text
      setFormData((prev) => ({
        ...prev,
        content: prev.content ? prev.content + '\n\n' + text : text,
      }))
      setShowAudio(false)
      setAudioBlob(null)
      setAudioUrl(null)
    } catch (err) {
      alert(err.response?.data?.detail || t('memoryList.transcribe_error'))
    } finally {
      setTranscribing(false)
    }
  }

  const resetAudio = () => {
    setAudioBlob(null)
    setAudioUrl(null)
    if (isRecording) {
      mediaRecorderRef.current?.stop()
      setIsRecording(false)
    }
  }

  const handleShareInvite = async () => {
    setSharingLoading(true)
    try {
      const res = await invitesAPI.create(memorialId, {})
      const url = buildContributeInviteUrl(res.data.token) || res.data.invite_url
      const fallbackName = t('memoryList.anonymous_person')
      const text =
        lang === 'en'
          ? t('memoryList.invite_sms', {
              name: memorialName || fallbackName,
              url,
            })
          : t('memoryList.invite_sms', {
              name: aboutName(memorialName || fallbackName),
              url,
            })
      setSharePanel({ url, text })
      setUrlCopied(false)
      setTextCopied(false)
    } catch (err) {
      const msg = formatApiDetail(err)
      alert(msg || t('memoryList.invite_link_error'))
    } finally {
      setSharingLoading(false)
    }
  }

  const handleCopyUrl = async () => {
    await navigator.clipboard.writeText(sharePanel.url)
    setUrlCopied(true)
    setTimeout(() => setUrlCopied(false), 2000)
  }

  const handleCopyText = async () => {
    await navigator.clipboard.writeText(sharePanel.text)
    setTextCopied(true)
    setTimeout(() => setTextCopied(false), 2000)
  }

  const handleNativeShare = () => {
    if (navigator.share) {
      navigator.share({
        title:
          lang === 'en'
            ? t('memoryList.native_share_title', {
                name: memorialName || t('memoryList.anonymous_person'),
              })
            : t('memoryList.native_share_title', {
                name: aboutName(memorialName || t('memoryList.anonymous_person')),
              }),
        text: sharePanel.text,
        url: sharePanel.url,
      })
    } else {
      handleCopyText()
    }
  }

  const loadMemories = async (q = '') => {
    try {
      setLoading(true)
      setLoadError(null)
      const response = await memorialsAPI.getMemories(memorialId, q || null)
      setMemories(Array.isArray(response.data) ? response.data : [])
    } catch (err) {
      console.error('Error loading memories:', err)
      setMemories([])
      setLoadError(
        err.response?.data?.detail || err.message || t('memoryList.network_error')
      )
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const submitData = {
        ...formData,
        event_date: formData.event_date ? `${formData.event_date}T00:00:00Z` : null,
      }
      await memorialsAPI.createMemory(memorialId, submitData)
      setFormData({ title: '', content: '', event_date: '' })
      setShowForm(false)
      await loadMemories(debouncedQuery)
      if (onReload) onReload()
    } catch (err) {
      alert(err.response?.data?.detail || t('memoryList.submit_error_add'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="memory-list">
      <div className="memory-header">
        <h2>{t('memoryList.title')}</h2>
        <div className="memory-header-actions">
          {typeof onOpenAvatarChat === 'function' && (
            <button
              type="button"
              className="btn btn-memory-chat"
              onClick={() => onOpenAvatarChat()}
            >
              💬 {t('tabs.chat')}
            </button>
          )}
          <button
            className="btn btn-share"
            onClick={handleShareInvite}
            disabled={sharingLoading}
          >
            {sharingLoading ? t('memoryList.invite_loading') : `🔗 ${t('memoryList.invite_friend')}`}
          </button>
          {canEdit && (
            <button
              className="btn btn-primary"
              onClick={() => setShowForm(!showForm)}
            >
              {showForm ? t('common.cancel') : t('memoryList.add_memory')}
            </button>
          )}
        </div>
      </div>

      {sharePanel && (
        <div className="share-panel">
          <div className="share-panel-header">
            <span>
              {memorialName
                ? t('memoryList.share_heading', {
                    name:
                      lang === 'en' ? memorialName : aboutName(memorialName),
                  })
                : t('memoryList.share_heading_no_name')}
            </span>
            <button className="share-panel-close" onClick={() => setSharePanel(null)}>✕</button>
          </div>
          <div className="share-url-row">
            <span className="share-url-text">{sharePanel.url}</span>
            <button className="btn btn-copy" onClick={handleCopyUrl}>
              {urlCopied ? t('memoryList.copied') : t('memoryList.copy')}
            </button>
          </div>
          <div className="share-message-section">
            <p className="share-message-label">{t('memoryList.or_ready_message')}</p>
            <p className="share-message-text">«{sharePanel.text}»</p>
            <div className="share-actions">
              <button className="btn btn-copy" onClick={handleCopyText}>
                {textCopied ? t('memoryList.copied') : t('memoryList.copy_text')}
              </button>
              <button className="btn btn-primary" onClick={handleNativeShare}>
                {t('memoryList.share')}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="memory-search">
        <input
          type="text"
          placeholder={t('memoryList.search_placeholder')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        {searchQuery && (
          <button className="search-clear" onClick={() => setSearchQuery('')}>✕</button>
        )}
      </div>
      {searchQuery && !loading && (
        <p className="search-results-count">
          {t('memoryList.found_count', { n: String(memories.length) })}
        </p>
      )}

      {loading && <div className="loading">{t('memoryList.loading')}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="memory-form">
          <div className="form-group">
            <label htmlFor="title">{t('memoryList.title_optional')}</label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder={t('memoryList.short_title_ph')}
            />
          </div>
          <div className="form-group">
            <label htmlFor="content">{t('memoryList.memory_text_label')}</label>
            <textarea
              id="content"
              value={formData.content}
              onChange={(e) =>
                setFormData({ ...formData, content: e.target.value })
              }
              rows="6"
              required
              placeholder={t('memoryList.memory_content_ph')}
            />
          </div>

          {/* Аудио-транскрипция */}
          <div className="audio-transcribe-section">
            <button
              type="button"
              className="btn-audio-toggle"
              onClick={() => { setShowAudio(!showAudio); resetAudio() }}
            >
              🎙️ {showAudio ? t('memoryList.voice_hide') : t('memoryList.voice_show')}
            </button>

            {showAudio && (
              <div className="audio-controls">
                <p className="audio-hint">
                  {t('memoryList.audio_hint')}
                </p>
                <div className="audio-buttons">
                  {!audioBlob && (
                    <>
                      {!isRecording ? (
                        <button type="button" className="btn-record" onClick={startRecording}>
                          🔴 {t('memoryList.record_start')}
                        </button>
                      ) : (
                        <button type="button" className="btn-record recording" onClick={stopRecording}>
                          ⏹️ {t('memoryList.record_stop')}
                        </button>
                      )}
                      <label className="btn-upload-audio">
                        📁 {t('memoryList.upload_audio')}
                        <input
                          type="file"
                          accept="audio/*"
                          onChange={handleAudioFileSelect}
                          style={{ display: 'none' }}
                        />
                      </label>
                    </>
                  )}
                  {audioBlob && (
                    <div className="audio-preview">
                      <audio controls src={audioUrl} className="audio-player-small" />
                      <div className="audio-preview-actions">
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={handleTranscribe}
                          disabled={transcribing}
                        >
                          {transcribing ? `⏳ ${t('memoryList.transcribing')}` : `✍️ ${t('memoryList.transcribe_btn')}`}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={resetAudio}>
                          {t('memoryList.delete')}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="event_date">{t('memoryList.when_optional')}</label>
            <input
              type="date"
              id="event_date"
              value={formData.event_date}
              onChange={(e) =>
                setFormData({ ...formData, event_date: e.target.value })
              }
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? t('memoryList.saving') : t('memoryList.save')}
          </button>
        </form>
      )}

      {!loading && loadError ? (
        <div className="empty-state load-error">
          <p>{t('memoryList.load_failed')}</p>
          <p className="hint">{loadError}</p>
          <button type="button" className="btn-retry" onClick={() => loadMemories(debouncedQuery)}>
            {t('memoryList.retry')}
          </button>
        </div>
      ) : !loading && memories.length === 0 ? (
        <div className="empty-state">
          {searchQuery ? (
            <p>{t('memoryList.empty_search', { q: searchQuery })}</p>
          ) : (
            <>
              <p>{t('memoryList.empty_none')}</p>
              <p className="hint">
                {t('memoryList.empty_hint')}
              </p>
            </>
          )}
        </div>
      ) : !loading && (
        <div className="memories">
          {memories.map((memory) => (
            <div key={memory.id} className="memory-card">
              {editingId === memory.id ? (
                <form
                  onSubmit={async (e) => {
                    e.preventDefault()
                    setSubmitting(true)
                    try {
                      const submitData = {
                        ...editFormData,
                        event_date: editFormData.event_date ? `${editFormData.event_date}T00:00:00Z` : null,
                      }
                      await memorialsAPI.updateMemory(memorialId, memory.id, submitData)
                      setEditingId(null)
                      setEditFormData({ title: '', content: '', event_date: '' })
                      await loadMemories(debouncedQuery)
                      if (onReload) onReload()
                    } catch (err) {
                      alert(err.response?.data?.detail || t('memoryList.submit_error_update'))
                    } finally {
                      setSubmitting(false)
                    }
                  }}
                  className="memory-edit-form"
                >
                  <div className="form-group">
                    <label htmlFor={`edit-title-${memory.id}`}>{t('memoryList.edit_title_label')}</label>
                    <input
                      type="text"
                      id={`edit-title-${memory.id}`}
                      value={editFormData.title}
                      onChange={(e) =>
                        setEditFormData({ ...editFormData, title: e.target.value })
                      }
                      placeholder={t('memoryList.short_title_ph')}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor={`edit-content-${memory.id}`}>{t('memoryList.edit_content_label')}</label>
                    <textarea
                      id={`edit-content-${memory.id}`}
                      value={editFormData.content}
                      onChange={(e) =>
                        setEditFormData({ ...editFormData, content: e.target.value })
                      }
                      rows="6"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor={`edit-event-date-${memory.id}`}>{t('memoryList.edit_when')}</label>
                    <input
                      type="date"
                      id={`edit-event-date-${memory.id}`}
                      value={editFormData.event_date}
                      onChange={(e) =>
                        setEditFormData({ ...editFormData, event_date: e.target.value })
                      }
                    />
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                      {submitting ? t('memoryList.saving') : t('memoryList.save')}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => {
                        setEditingId(null)
                        setEditFormData({ title: '', content: '' })
                      }}
                    >
                      {t('common.cancel')}
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  {memory.title && <h3>{memory.title}</h3>}
                  <p>{memory.content}</p>
                  <div className="memory-meta">
                    {memory.event_date && (
                      <span className="event-date">
                        {new Date(memory.event_date).toLocaleDateString(locale, {
                          year: 'numeric',
                          month: 'long',
                        })}
                      </span>
                    )}
                    <span>
                      {t('memoryList.added')}{' '}
                      {new Date(memory.created_at).toLocaleDateString(locale)}
                    </span>
                    {canEdit && (
                    <div className="memory-actions">
                      <button
                        className="btn-edit"
                        onClick={() => {
                          setEditingId(memory.id)
                          setEditFormData({
                            title: memory.title || '',
                            content: memory.content,
                            event_date: memory.event_date
                              ? new Date(memory.event_date).toISOString().split('T')[0]
                              : '',
                          })
                        }}
                      >
                        ✏️ {t('memoryList.edit')}
                      </button>
                      <button
                        className="btn-delete"
                        onClick={async () => {
                          if (confirm(t('memoryList.confirm_delete'))) {
                            try {
                              await memorialsAPI.deleteMemory(memorialId, memory.id)
                              await loadMemories(debouncedQuery)
                              if (onReload) onReload()
                            } catch (err) {
                              alert(err.response?.data?.detail || t('memoryList.delete_error'))
                            }
                          }
                        }}
                      >
                        🗑️ {t('memoryList.delete_memory')}
                      </button>
                    </div>
                    )}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MemoryList

