import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { invitesAPI, memorialsAPI, aiAPI } from '../api/client'
import ApiMediaImage from '../components/ApiMediaImage'
import AvatarChat from '../components/AvatarChat'
import { useLanguage } from '../contexts/LanguageContext'
import './ContributePage.css'

function ContributePage() {
  const { token } = useParams()
  const { t } = useLanguage()
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('record')

  // Recording state
  const [recording, setRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [transcribing, setTranscribing] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [memoryTitle, setMemoryTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [viralSharing, setViralSharing] = useState(false)

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => {
    const stored = sessionStorage.getItem('invite_token')
    if (!stored || stored !== token) {
      sessionStorage.setItem('invite_token', token)
    }
    invitesAPI.validate(token)
      .then(res => setInfo(res.data))
      .catch(err => setError(err.response?.data?.detail || t('contribute.invalid_link')))
      .finally(() => setLoading(false))
  }, [token])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = e => chunksRef.current.push(e.data)
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        stream.getTracks().forEach(t => t.stop())
        handleTranscribe(blob)
      }
      recorder.start()
      mediaRecorderRef.current = recorder
      setRecording(true)
      setAudioBlob(null)
      setTranscript('')
      setSaved(false)
    } catch {
      alert(t('contribute.mic_denied'))
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      setRecording(false)
    }
  }

  const handleTranscribe = async (blob) => {
    setTranscribing(true)
    try {
      const file = new File([blob], 'recording.webm', { type: 'audio/webm' })
      const res = await aiAPI.transcribe(file)
      setTranscript(res.data.text || '')
    } catch {
      setTranscript('')
      alert(t('contribute.transcribe_error'))
    } finally {
      setTranscribing(false)
    }
  }

  const handleViralShare = async () => {
    setViralSharing(true)
    try {
      const res = await invitesAPI.create(info.memorial_id, {})
      const url = res.data.invite_url
      const name = info.memorial_name || t('contribute.viral_name_fallback')
      const text = t('contribute.viral_text', { name, url })
      if (navigator.share) {
        await navigator.share({ title: t('contribute.viral_native_title', { name }), text, url })
      } else {
        await navigator.clipboard.writeText(text)
        alert(t('contribute.clipboard_copied'))
      }
    } catch {
      // user cancelled share or error — ignore
    } finally {
      setViralSharing(false)
    }
  }

  const handleSave = async () => {
    if (!transcript.trim()) return
    setSaving(true)
    try {
      await memorialsAPI.createMemory(info.memorial_id, {
        title: memoryTitle || null,
        content: transcript,
        source: 'voice_invite',
      }, token)
      setSaved(true)
      setTranscript('')
      setMemoryTitle('')
      setAudioBlob(null)
    } catch {
      alert(t('contribute.save_error'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="contribute-loading">{t('contribute.loading')}</div>
  if (error) return (
    <div className="contribute-invalid">
      <div className="invalid-icon">🔗</div>
      <h2>{t('contribute.invalid_link')}</h2>
      <p>{error}</p>
    </div>
  )

  return (
    <div className="contribute-page">
      <div className="contribute-header">
        {info.cover_photo_id && (
          <ApiMediaImage
            mediaId={info.cover_photo_id}
            thumbnail="small"
            alt={info.memorial_name}
            className="contribute-cover"
          />
        )}
        <div className="contribute-info">
          <h1>{info.memorial_name}</h1>
          {info.label && (
            <p className="contribute-label">{t('contribute.invitation_for', { label: info.label })}</p>
          )}
          <p className="contribute-subtitle">
            {t('contribute.subtitle', { name: info.memorial_name })}<br />
            {t('contribute.subtitle2')}
          </p>
        </div>
      </div>

      <div className="contribute-tabs">
        {info.permissions.add_memories && (
          <button
            className={activeTab === 'record' ? 'active' : ''}
            onClick={() => setActiveTab('record')}
          >
            {t('contribute.tab_record')}
          </button>
        )}
        {info.permissions.chat && (
          <button
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            {t('contribute.tab_chat')}
          </button>
        )}
      </div>

      <div className="contribute-content">
        {activeTab === 'record' && info.permissions.add_memories && (
          <div className="record-tab">
            {saved ? (
              <div className="save-success">
                <div className="success-icon">✅</div>
                <h3>{t('contribute.saved_title')}</h3>
                <p className="save-success-hint">{t('contribute.saved_hint')}</p>
                <div className="save-success-actions">
                  <button
                    className="btn-record-again"
                    onClick={() => setSaved(false)}
                  >
                    {t('contribute.record_again')}
                  </button>
                  <button
                    className="btn-viral-share"
                    onClick={handleViralShare}
                    disabled={viralSharing}
                  >
                    {viralSharing ? '...' : t('contribute.viral_share')}
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="record-area">
                  {!recording && !audioBlob && !transcribing && (
                    <>
                      <p className="record-hint">{t('contribute.record_hint')}</p>
                      <button className="btn-record" onClick={startRecording}>
                        <span className="record-dot"></span>
                        {t('contribute.btn_record')}
                      </button>
                    </>
                  )}
                  {recording && (
                    <button className="btn-stop" onClick={stopRecording}>
                      <span className="stop-icon">⏹</span>
                      {t('contribute.btn_stop')}
                    </button>
                  )}
                  {transcribing && (
                    <div className="transcribing-status">
                      <div className="spinner"></div>
                      {t('contribute.transcribing')}
                    </div>
                  )}
                </div>

                {(transcript !== '' || audioBlob) && !transcribing && (
                  <div className="transcript-area">
                    <label htmlFor="memory-title">{t('contribute.label_title')}</label>
                    <input
                      id="memory-title"
                      type="text"
                      value={memoryTitle}
                      onChange={e => setMemoryTitle(e.target.value)}
                      placeholder={t('contribute.placeholder_title')}
                    />
                    <label htmlFor="transcript">{t('contribute.label_text')}</label>
                    <textarea
                      id="transcript"
                      value={transcript}
                      onChange={e => setTranscript(e.target.value)}
                      rows={6}
                      placeholder={t('contribute.placeholder_text')}
                    />
                    <div className="transcript-actions">
                      <button
                        className="btn-save"
                        onClick={handleSave}
                        disabled={saving || !transcript.trim()}
                      >
                        {saving ? t('contribute.btn_saving') : t('contribute.btn_save_memory')}
                      </button>
                      <button
                        className="btn-record-again"
                        onClick={() => {
                          setAudioBlob(null)
                          setTranscript('')
                          setMemoryTitle('')
                        }}
                      >
                        {t('contribute.btn_rerecord')}
                      </button>
                    </div>
                  </div>
                )}

                {!audioBlob && !recording && !transcribing && (
                  <div className="manual-entry">
                    <p className="or-divider">{t('contribute.or_type')}</p>
                    <input
                      type="text"
                      value={memoryTitle}
                      onChange={e => setMemoryTitle(e.target.value)}
                      placeholder={t('contribute.placeholder_title_manual')}
                    />
                    <textarea
                      value={transcript}
                      onChange={e => setTranscript(e.target.value)}
                      rows={5}
                      placeholder={t('contribute.placeholder_text_manual')}
                    />
                    {transcript.trim() && (
                      <button
                        className="btn-save"
                        onClick={handleSave}
                        disabled={saving}
                      >
                        {saving ? t('contribute.btn_saving') : t('contribute.btn_save')}
                      </button>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'chat' && info.permissions.chat && (
          <AvatarChat
            memorialId={info.memorial_id}
            coverPhotoId={info.cover_photo_id}
            memorialName={info.memorial_name}
          />
        )}
      </div>
    </div>
  )
}

export default ContributePage
