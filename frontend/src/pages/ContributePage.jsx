import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { invitesAPI, memorialsAPI, aiAPI, getMediaUrl } from '../api/client'
import AvatarChat from '../components/AvatarChat'
import './ContributePage.css'

function ContributePage() {
  const { token } = useParams()
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
      .catch(err => setError(err.response?.data?.detail || 'Ссылка недействительна'))
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
      alert('Не удалось получить доступ к микрофону. Разрешите доступ в браузере.')
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
      alert('Не удалось расшифровать запись. Введите текст вручную.')
    } finally {
      setTranscribing(false)
    }
  }

  const handleViralShare = async () => {
    setViralSharing(true)
    try {
      const res = await invitesAPI.create(info.memorial_id, {})
      const url = res.data.invite_url
      const name = info.memorial_name || 'этого человека'
      const text = `Я поделился воспоминаниями о ${name}. Расскажи и ты: ${url}`
      if (navigator.share) {
        await navigator.share({ title: `Воспоминания о ${name}`, text, url })
      } else {
        await navigator.clipboard.writeText(text)
        alert('Текст скопирован в буфер обмена!')
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
      })
      setSaved(true)
      setTranscript('')
      setMemoryTitle('')
      setAudioBlob(null)
    } catch {
      alert('Ошибка при сохранении воспоминания. Попробуйте ещё раз.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="contribute-loading">Загрузка...</div>
  if (error) return (
    <div className="contribute-invalid">
      <div className="invalid-icon">🔗</div>
      <h2>Ссылка недействительна</h2>
      <p>{error}</p>
    </div>
  )

  return (
    <div className="contribute-page">
      <div className="contribute-header">
        {info.cover_photo_id && (
          <img
            src={getMediaUrl(info.cover_photo_id, 'small')}
            alt={info.memorial_name}
            className="contribute-cover"
          />
        )}
        <div className="contribute-info">
          <h1>{info.memorial_name}</h1>
          {info.label && (
            <p className="contribute-label">Приглашение для: {info.label}</p>
          )}
          <p className="contribute-subtitle">
            Вас пригласили поделиться воспоминаниями о {info.memorial_name}.<br />
            Ваши слова очень важны — они сохранятся навсегда.
          </p>
        </div>
      </div>

      <div className="contribute-tabs">
        {info.permissions.add_memories && (
          <button
            className={activeTab === 'record' ? 'active' : ''}
            onClick={() => setActiveTab('record')}
          >
            🎙 Записать воспоминание
          </button>
        )}
        {info.permissions.chat && (
          <button
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            💬 Чат
          </button>
        )}
      </div>

      <div className="contribute-content">
        {activeTab === 'record' && info.permissions.add_memories && (
          <div className="record-tab">
            {saved ? (
              <div className="save-success">
                <div className="success-icon">✅</div>
                <h3>Воспоминание сохранено!</h3>
                <p className="save-success-hint">Спасибо! Ваши слова теперь часть этой памяти.</p>
                <div className="save-success-actions">
                  <button
                    className="btn-record-again"
                    onClick={() => setSaved(false)}
                  >
                    Записать ещё
                  </button>
                  <button
                    className="btn-viral-share"
                    onClick={handleViralShare}
                    disabled={viralSharing}
                  >
                    {viralSharing ? '...' : '💌 Поделиться дальше — пусть другие тоже расскажут'}
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="record-area">
                  {!recording && !audioBlob && !transcribing && (
                    <>
                      <p className="record-hint">Нажмите кнопку и говорите. Мы запишем и сохраним ваши слова.</p>
                      <button className="btn-record" onClick={startRecording}>
                        <span className="record-dot"></span>
                        Нажмите, чтобы записать
                      </button>
                    </>
                  )}
                  {recording && (
                    <button className="btn-stop" onClick={stopRecording}>
                      <span className="stop-icon">⏹</span>
                      Остановить запись
                    </button>
                  )}
                  {transcribing && (
                    <div className="transcribing-status">
                      <div className="spinner"></div>
                      Расшифровываю запись...
                    </div>
                  )}
                </div>

                {(transcript !== '' || audioBlob) && !transcribing && (
                  <div className="transcript-area">
                    <label htmlFor="memory-title">Заголовок (необязательно)</label>
                    <input
                      id="memory-title"
                      type="text"
                      value={memoryTitle}
                      onChange={e => setMemoryTitle(e.target.value)}
                      placeholder="Например: Наше последнее лето"
                    />
                    <label htmlFor="transcript">Текст воспоминания</label>
                    <textarea
                      id="transcript"
                      value={transcript}
                      onChange={e => setTranscript(e.target.value)}
                      rows={6}
                      placeholder="Введите или отредактируйте текст воспоминания..."
                    />
                    <div className="transcript-actions">
                      <button
                        className="btn-save"
                        onClick={handleSave}
                        disabled={saving || !transcript.trim()}
                      >
                        {saving ? 'Сохранение...' : 'Сохранить воспоминание'}
                      </button>
                      <button
                        className="btn-record-again"
                        onClick={() => {
                          setAudioBlob(null)
                          setTranscript('')
                          setMemoryTitle('')
                        }}
                      >
                        Записать заново
                      </button>
                    </div>
                  </div>
                )}

                {!audioBlob && !recording && !transcribing && (
                  <div className="manual-entry">
                    <p className="or-divider">— или введите текстом —</p>
                    <input
                      type="text"
                      value={memoryTitle}
                      onChange={e => setMemoryTitle(e.target.value)}
                      placeholder="Заголовок (необязательно)"
                    />
                    <textarea
                      value={transcript}
                      onChange={e => setTranscript(e.target.value)}
                      rows={5}
                      placeholder="Напишите воспоминание..."
                    />
                    {transcript.trim() && (
                      <button
                        className="btn-save"
                        onClick={handleSave}
                        disabled={saving}
                      >
                        {saving ? 'Сохранение...' : 'Сохранить'}
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
