import { createPortal } from 'react-dom'
import { useState, useRef, useEffect, useCallback } from 'react'
import apiClient, { aiAPI, memorialsAPI } from '../api/client'
import ApiMediaImage from './ApiMediaImage'
import ChatAudioPlayer from './ChatAudioPlayer'
import { Link, useLocation } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import { useAuth } from '../context/AuthContext'
import './AvatarChat.css'

// Запись аудио для клона голоса
function useVoiceRecorder() {
  const { t } = useLanguage()
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])

  const start = async () => {
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
      recorderRef.current = recorder
      setIsRecording(true)
    } catch {
      alert(t('chat.mic_denied'))
    }
  }

  const stop = () => {
    recorderRef.current?.stop()
    setIsRecording(false)
  }

  const reset = () => {
    setAudioBlob(null)
    setAudioUrl(null)
    if (isRecording) { recorderRef.current?.stop(); setIsRecording(false) }
  }

  return { isRecording, audioBlob, audioUrl, start, stop, reset }
}

/** URL, по которому браузер может воспроизвести аудио (никогда s3://, голый filename превращаем в /api/v1/media/audio/...) */
function getPlayableAudioUrl(url) {
  if (!url) return null
  if (url.startsWith('s3://')) return null
  if (/^https?:\/\//.test(url) || url.startsWith('/')) return url
  const base = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
  return `${base}/media/audio/${url}`
}

function AvatarChat({ memorialId, coverPhotoId, memorialName, onMessageSent, portraitSettings, onEditPortrait, canManageVoice = false, textOnly = false, disabled = false, inviteToken }) {
  const location = useLocation()
  const [quotaBlocked, setQuotaBlocked] = useState(false)
  const [chatUsage, setChatUsage] = useState(null)
  const authReturn = `${location.pathname}${location.search}${location.hash}`
  const avatarPhotoId = portraitSettings?.avatar?.media_id || coverPhotoId
  const portraitVersion = JSON.stringify(portraitSettings || {})
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [includeAudio, setIncludeAudio] = useState(false)
  const { lang, t } = useLanguage()
  const { user } = useAuth()
  const monthlyLimitReached = !!user && chatUsage?.chat_messages_limit != null && chatUsage.chat_messages_used >= chatUsage.chat_messages_limit
  const chatBlocked = quotaBlocked || monthlyLimitReached
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [includeFamilyMemories, setIncludeFamilyMemories] = useState(false)

  // Family RAG is a paid feature (Plus / Pro). Free users see a locked toggle.
  const hasFamilyRag = user && (user.is_admin || user.is_demo || ['plus', 'pro', 'lifetime_pro'].includes(user.subscription_plan))
  const [syncing, setSyncing] = useState(false)
  const [uploadingVoice, setUploadingVoice] = useState(false)
  const [voiceName, setVoiceName] = useState('')
  const [hasCustomVoice, setHasCustomVoice] = useState(false)
  const [showVoicePanel, setShowVoicePanel] = useState(false)
  const [voiceStep, setVoiceStep] = useState(0)
  const voiceDialog = useRef(null)
  const voiceBody = useRef(null)
  const [voiceSamples, setVoiceSamples] = useState([]) // { id, file, label }[] — накопленные образцы перед отправкой
  const [preparingSample, setPreparingSample] = useState(null)
  const [modelPreviews, setModelPreviews] = useState({})
  const [previewBusy, setPreviewBusy] = useState(null)
  const voiceBusy = uploadingVoice || preparingSample !== null || previewBusy !== null
  useEffect(() => {
    if (showVoicePanel && voiceDialog.current && !voiceDialog.current.open) voiceDialog.current.showModal()
  }, [showVoicePanel])
  useEffect(() => { voiceBody.current?.scrollTo(0, 0) }, [voiceStep])

  const [speechSpeed, setSpeechSpeed] = useState(1)
  const [pronunciationText, setPronunciationText] = useState('')
  const sampleUrls = useRef(new Set())
  const sampleGeneration = useRef(0)
  const localText = (ru, en) => lang === 'ru' ? ru : en
  const sampleUrl = (file) => {
    const url = URL.createObjectURL(file)
    sampleUrls.current.add(url)
    return url
  }
  useEffect(() => {
    setVoiceSamples([])
    setModelPreviews({})
    setShowVoicePanel(false)
    setVoiceStep(0)
    sampleGeneration.current += 1
    setPreparingSample(null)
    setPreviewBusy(null)
    return () => {
      sampleGeneration.current += 1
      sampleUrls.current.forEach((url) => URL.revokeObjectURL(url))
      sampleUrls.current.clear()
    }
  }, [memorialId])
  const [ttsStatus, setTtsStatus] = useState(null)
  const [elQuota, setElQuota] = useState(null)
  const [elQuotaErr, setElQuotaErr] = useState(null)
  const messagesEndRef = useRef(null)
  const voiceRecorder = useVoiceRecorder()

  const storageKey = `chat_${memorialId}`

  const scrollToBottom = () => {
    const container = messagesEndRef.current?.parentElement
    container?.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
  }

  useEffect(() => {
    if (messages.length > 0) scrollToBottom()
  }, [messages])

  useEffect(() => {
    let cancelled = false
    setTtsStatus(null)
    setElQuota(null)
    setElQuotaErr(null)
    if (!user || textOnly) return () => { cancelled = true }
    aiAPI.getTtsStatus(memorialId).then(async (res) => {
      if (cancelled) return
      setTtsStatus(res.data)
      if (res.data.provider === 'elevenlabs') {
        try {
          const quota = await aiAPI.getElevenLabsQuota()
          if (!cancelled) setElQuota(quota.data)
        } catch {
          if (!cancelled) setElQuotaErr(true)
        }
      }
    }).catch(() => {})
    return () => {
      cancelled = true
    }
  }, [memorialId, user, textOnly])

  const refreshUsage = useCallback(async () => {
    if (!user) return
    try { setChatUsage((await apiClient.get('/billing/usage')).data) } catch { /* Usage hint is optional; server still enforces the quota. */ }
  }, [user])
  useEffect(() => {
    setQuotaBlocked(false)
    setChatUsage(null)
    refreshUsage()
  }, [user?.id, memorialId, refreshUsage])

  // Load chat history from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = JSON.parse(saved)
        setMessages(Array.isArray(parsed) ? parsed : [])
      }
    } catch (e) {
      // ignore corrupt data
    }
  }, [storageKey])

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(messages))
      } catch (e) {
        // ignore storage errors
      }
    }
  }, [messages, storageKey])

  // Polling анимации: каждые 5 сек проверяем статус для pending сообщений
  useEffect(() => {
    const pendingMessages = messages.filter(
      (m) => m.role === 'assistant' && m.animationTaskId && m.videoStatus === 'pending'
    )
    if (pendingMessages.length === 0) return

    const interval = setInterval(async () => {
      for (const msg of pendingMessages) {
        try {
          const res = await aiAPI.getAnimationStatus({
            task_id: msg.animationTaskId,
            provider: msg.animationProvider,
          })
          const { status, video_url } = res.data
          if (['done', 'completed'].includes(status) && video_url) {
            setMessages((prev) =>
              prev.map((m) =>
                m.animationTaskId === msg.animationTaskId
                  ? { ...m, videoUrl: video_url, videoStatus: 'ready' }
                  : m
              )
            )
          } else if (status === 'error' || status === 'failed') {
            setMessages((prev) =>
              prev.map((m) =>
                m.animationTaskId === msg.animationTaskId
                  ? { ...m, videoStatus: 'error' }
                  : m
              )
            )
          }
        } catch (err) {
          console.warn('Animation status poll error:', err)
        }
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [messages])

  useEffect(() => {
    if (!canManageVoice) return
    const checkVoice = async () => {
      try {
        const response = await memorialsAPI.get(memorialId)
        setHasCustomVoice(!!response.data.voice_id)
      } catch (err) {
        console.error('Error checking voice:', err)
      }
    }
    checkVoice()
  }, [memorialId, canManageVoice])

  const handleVoiceUpload = (e) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return
    const invalid = files.find((f) => !f.type.startsWith('audio/') && !/\.(mp3|wav|m4a|ogg|oga|opus|flac|aac|mpeg|mpga|mp4|mov|m4v|webm)$/i.test(f.name))
    if (invalid) {
      alert(t('chat.voice_file_type_error'))
      return
    }
    setVoiceSamples((prev) => [
      ...prev,
      ...files.map((file) => ({ id: `${Date.now()}_${file.name}_${Math.random()}`, file, originalUrl: sampleUrl(file), label: file.name })),
    ])
    e.target.value = ''
  }

  const handleAddRecording = () => {
    if (!voiceRecorder.audioBlob) return
    const file = new File([voiceRecorder.audioBlob], `voice_clone_${voiceSamples.length + 1}.webm`, { type: 'audio/webm' })
    setVoiceSamples((prev) => [
      ...prev,
      { id: `${Date.now()}_rec_${Math.random()}`, file, originalUrl: sampleUrl(file), label: t('chat.voice_recording_label', { n: String(prev.length + 1) }) },
    ])
    voiceRecorder.reset()
  }

  const handleRemoveSample = (id) => {
    const sample = voiceSamples.find((s) => s.id === id)
    ;[sample?.originalUrl, sample?.cleanedUrl].filter(Boolean).forEach((url) => {
      URL.revokeObjectURL(url)
      sampleUrls.current.delete(url)
    })
    setVoiceSamples((prev) => prev.filter((s) => s.id !== id))
  }

  const handlePrepareSample = async (sample) => {
    setPreparingSample(sample.id)
    const generation = sampleGeneration.current
    try {
      const response = await aiAPI.prepareVoice(memorialId, sample.file)
      if (generation !== sampleGeneration.current) return
      const file = new File([response.data], 'cleaned.mp3', { type: 'audio/mpeg' })
      const url = sampleUrl(file)
      if (sample.cleanedUrl) {
        URL.revokeObjectURL(sample.cleanedUrl)
        sampleUrls.current.delete(sample.cleanedUrl)
      }
      setVoiceSamples((prev) => prev.map((s) => s.id === sample.id
        ? { ...s, cleanedFile: file, cleanedUrl: url, useCleaned: false } : s))
    } catch (error) {
      let detail = error.response?.data?.detail
      if (error.response?.data instanceof Blob) {
        try { detail = JSON.parse(await error.response.data.text()).detail } catch { /* use fallback */ }
      }
      alert(detail || localText('Не удалось очистить запись.', 'Could not clean the recording.'))
    } finally { if (generation === sampleGeneration.current) setPreparingSample(null) }
  }

  const handleModelPreview = async (model) => {
    setPreviewBusy(model)
    const generation = sampleGeneration.current
    try {
      const response = await aiAPI.previewVoice(memorialId, model, lang)
      if (generation !== sampleGeneration.current) return
      const url = sampleUrl(response.data)
      const previous = modelPreviews[model]
      if (previous) { URL.revokeObjectURL(previous); sampleUrls.current.delete(previous) }
      setModelPreviews((prev) => ({ ...prev, [model]: url }))
    } catch (err) {
      let detail
      if (err.response?.data instanceof Blob) {
        try { detail = JSON.parse(await err.response.data.text()).detail } catch { /* readable fallback */ }
      }
      alert(detail || localText('Не удалось создать тестовую озвучку.', 'Could not generate the voice preview.'))
    } finally { if (generation === sampleGeneration.current) setPreviewBusy(null) }
  }

  const handleSelectModel = async (model) => {
    const generation = sampleGeneration.current
    setPreviewBusy(model)
    try {
      await aiAPI.selectVoiceModel(memorialId, model)
      if (generation !== sampleGeneration.current) return
      setTtsStatus((prev) => ({ ...prev, model }))
      Object.values(modelPreviews).forEach((url) => { URL.revokeObjectURL(url); sampleUrls.current.delete(url) })
      setModelPreviews({})
      setVoiceStep(3)
    } catch (err) { alert(err.response?.data?.detail || localText('Не удалось сохранить модель.', 'Could not save the model.')) }
    finally { if (generation === sampleGeneration.current) setPreviewBusy(null) }
  }

  const handleCloneVoice = async () => {
    if (voiceSamples.length === 0) return
    setUploadingVoice(true)
    try {
      await aiAPI.uploadVoice(
        memorialId,
        voiceSamples.map((s) => s.useCleaned && s.cleanedFile ? s.cleanedFile : s.file),
        voiceName || undefined
      )
      setVoiceStep(2)
      Object.values(modelPreviews).forEach((url) => { URL.revokeObjectURL(url); sampleUrls.current.delete(url) })
      setModelPreviews({})
      setHasCustomVoice(true)
      const status = await aiAPI.getTtsStatus(memorialId).catch(() => null)
      if (status) setTtsStatus(status.data)
      setShowVoicePanel(true)
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail || t('chat.voice_clone_error')
      const guestLimit = status === 401 && detail?.code === 'guest_chat_limit'
      if (status === 402 || status === 429 || guestLimit) {
        if (!includeFamilyMemories) setQuotaBlocked(true)
        alert(`⚠️ ${detail}`)
      } else {
        alert(detail)
      }
    } finally {
      setUploadingVoice(false)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading || disabled || chatBlocked) return

    const pronunciations = {}
    for (const line of pronunciationText.split('\n').filter((line) => line.trim())) {
      const separator = line.indexOf('=')
      const word = line.slice(0, separator).trim()
      const spoken = line.slice(separator + 1).trim()
      if (separator < 1 || !spoken || word.length > 80 || spoken.length > 80 || Object.keys(pronunciations).length >= 20) {
        alert(localText('Укажите до 20 строк: слово = произношение (до 80 символов).', 'Use up to 20 lines: word = pronunciation (up to 80 characters).'))
        return
      }
      pronunciations[word] = spoken
    }
    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: userMessage }])
    setLoading(true)

    try {
      const response = await aiAPI.chat({
        memorial_id: parseInt(memorialId),
        question: userMessage,
        speech_speed: speechSpeed,
        pronunciations,
        include_audio: !textOnly && includeAudio,
        include_family_memories: !textOnly && includeFamilyMemories,
        invite_token: inviteToken || undefined,
        language: lang,
      })

      // Браузер воспроизводит только http(s) или относительный /api/...; s3:// и голый filename — нормализуем
      let audioUrl = response.data.audio_url || null
      if (audioUrl) {
        if (audioUrl.startsWith('s3://')) audioUrl = null
        else if (!/^https?:\/\//.test(audioUrl) && !audioUrl.startsWith('/')) {
          const base = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
          audioUrl = `${base}/media/audio/${audioUrl}`
        }
      }

      const assistantMessage = {
        role: 'assistant',
        text: response.data.answer,
        audioUrl,
        audioError: response.data.audio_error || null,
        animationTaskId: response.data.animation_task_id || null,
        animationProvider: response.data.animation_provider || null,
        videoUrl: null,
        videoStatus: response.data.animation_task_id ? 'pending' : null,
        sources: response.data.sources || [],
      }

      setMessages((prev) => [...prev, assistantMessage])
      if (!user && response.data.guest_questions_remaining === 0) setQuotaBlocked(true)
      onMessageSent?.(response.data)
      refreshUsage()
    } catch (err) {
      console.error('Chat error:', err)
      const status = err.response?.status
      const detail = err.response?.data?.detail || err.message || t('chat.chat_error')
      // 402 = paid feature — show upgrade prompt, not a generic error
      const guestLimit = status === 401 && detail?.code === 'guest_chat_limit'
      if (status === 402 || status === 429 || guestLimit) {
        if (!includeFamilyMemories) setQuotaBlocked(true)
        if (includeFamilyMemories) {
          setIncludeFamilyMemories(false)
        }
        const errorMessage = {
          role: 'error',
          text: typeof detail === 'string' ? detail : detail?.message || (lang === 'en' ? 'Your free questions have been used. Sign in or choose a plan to continue.' : 'Бесплатные вопросы закончились. Войдите или выберите тариф, чтобы продолжить.'),
        }
        setMessages((prev) => [...prev, errorMessage])
      } else {
        const errorMessage = { role: 'error', text: typeof detail === 'string' ? detail : detail?.message || t('chat.chat_error') }
        setMessages((prev) => [...prev, errorMessage])
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestedQuestion = (question) => {
    setInput(question)
  }

  const handleClearHistory = () => {
    if (!confirm(t('chat.clear_confirm'))) return
    setMessages([])
    localStorage.removeItem(storageKey)
  }

  const handleSyncFamily = async () => {
    if (!confirm(t('chat.sync_confirm'))) return
    setSyncing(true)
    try {
      const res = await aiAPI.syncFamilyMemories(memorialId)
      const { created, skipped } = res.data
      alert(t('chat.sync_done', { created: String(created), skipped: String(skipped) }))
    } catch (err) {
      alert(err.response?.data?.detail || t('chat.sync_error'))
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className={`avatar-chat${isFullscreen ? ' avatar-chat--fullscreen' : ''}`}>
      {/* ─── Left: Avatar panel ──────────────────────────────────── */}
      <div className="avatar-panel">
        {avatarPhotoId ? (
          <ApiMediaImage
            mediaId={avatarPhotoId}
            portrait={{ memorialId, kind: 'avatar', version: portraitVersion }}
            thumbnail={null}
            avatarReference
            alt={memorialName || 'Avatar'}
            className="avatar-panel-photo"
            eager
            fallback={
              <div className="avatar-panel-placeholder">
                <span>{memorialName ? memorialName[0].toUpperCase() : '?'}</span>
              </div>
            }
          />
        ) : (
          <div className="avatar-panel-placeholder">
            <span>{memorialName ? memorialName[0].toUpperCase() : '?'}</span>
          </div>
        )}
        {loading && (
          <div className="avatar-thinking-overlay">
            <span></span><span></span><span></span>
          </div>
        )}
        {onEditPortrait && <button type="button" className="avatar-portrait-edit" onClick={onEditPortrait}>{t('portraits.edit_avatar')}</button>}
        <div className="avatar-panel-footer">
          {memorialName && (
            <div className="avatar-panel-name">{memorialName}</div>
          )}
          <div className="avatar-panel-status">
            <span className={`avatar-status-dot${loading ? ' avatar-status-dot--active' : ''}`}></span>
            <span className="avatar-status-text">
              {loading ? t('chat.avatar_thinking') : t('chat.avatar_ready')}
            </span>
          </div>
        </div>
      </div>

      {/* ─── Right: Chat panel ───────────────────────────────────── */}
      <div className="chat-panel">
      {ttsStatus?.provider === 'fish_audio' ? (
        <p className="chat-tts-quota">{t(ttsStatus.configured ? 'chat.tts_fish_ready' : 'chat.tts_fish_off')}</p>
      ) : elQuotaErr ? (
        <p className="chat-tts-quota chat-tts-quota--muted">{t('chat.tts_quota_err')}</p>
      ) : elQuota && !elQuota.configured ? (
        <p className="chat-tts-quota chat-tts-quota--muted">{t('chat.tts_quota_off')}</p>
      ) : elQuota && elQuota.configured ? (
        <p className="chat-tts-quota">
          {elQuota.character_limit > 0
            ? t('chat.tts_quota_on', {
                remaining: String(elQuota.characters_remaining),
                limit: String(elQuota.character_limit),
                tier: String(elQuota.tier ?? '—'),
              })
            : t('chat.tts_quota_unlimited')}
        </p>
      ) : null}
      {user && chatUsage && <p className="chat-usage-hint">
        {chatUsage.chat_messages_limit == null
          ? (lang === 'en' ? 'Unlimited text questions' : 'Текстовые вопросы без ограничений')
          : (lang === 'en' ? `Remaining: ${Math.max(0, chatUsage.chat_messages_limit - chatUsage.chat_messages_used)} of ${chatUsage.chat_messages_limit} questions this month` : `Осталось ${Math.max(0, chatUsage.chat_messages_limit - chatUsage.chat_messages_used)} из ${chatUsage.chat_messages_limit} вопросов в этом месяце`)}
        {chatUsage.chat_messages_limit != null && chatUsage.chat_messages_used >= chatUsage.chat_messages_limit && <Link to={`/pricing?next=${encodeURIComponent(authReturn)}`}>{lang === 'en' ? 'Choose a plan' : 'Выбрать тариф'}</Link>}
      </p>}
      <div className="chat-header">
        <div className="chat-header-title">
          <h2>
            {memorialName
              ? lang === 'en'
                ? t('chat.title_with', { name: memorialName })
                : `Чат с ${memorialName}`
              : t('chat.title_default')}
          </h2>
        </div>
        <div className="header-controls">
          {!textOnly && <label className="audio-toggle" data-tour="chat-audio-toggle">
            <input
              type="checkbox"
              checked={includeAudio}
              onChange={(e) => setIncludeAudio(e.target.checked)}
            />
            {t('chat.audio_label')}
          </label>}
          {!textOnly && <label
            className={`audio-toggle family-memories-toggle${!hasFamilyRag ? ' feature-locked' : ''}`}
            title={!hasFamilyRag ? t('chat.family_locked_tooltip') : undefined}
          >
            <input
              type="checkbox"
              checked={includeFamilyMemories}
              disabled={!hasFamilyRag}
              onChange={(e) => {
                if (!hasFamilyRag) return
                setIncludeFamilyMemories(e.target.checked)
              }}
            />
            {t('chat.family_label')}
            {hasFamilyRag ? (
              <>
                <span className="info-trigger" title={t('chat.family_tooltip_title')} tabIndex={0}>?</span>
                <span className="info-tooltip">
                  {t('chat.family_tooltip_on')}
                  <br /><br />
                  {t('chat.family_tooltip_off')}
                </span>
              </>
            ) : (
              <span className="plan-badge">Plus</span>
            )}
          </label>}
          {canManageVoice && <button
            className="btn-clear-history"
            onClick={handleSyncFamily}
            disabled={syncing}
            title={t('chat.sync_family')}
          >
            {syncing ? `⏳ ${t('chat.syncing')}` : `🔄 ${t('chat.sync_family')}`}
          </button>}
          <button
            className="btn-fullscreen"
            onClick={() => setIsFullscreen((v) => !v)}
            title={isFullscreen ? t('chat.exit_fullscreen') : t('chat.fullscreen')}
          >
            {isFullscreen ? '⛶' : '⛶'}
            {isFullscreen ? t('chat.exit_fullscreen') : t('chat.fullscreen')}
          </button>
          {messages.length > 0 && (
            <button className="btn-clear-history" onClick={handleClearHistory} title={t('chat.clear_history')}>
              {t('chat.clear_history')}
            </button>
          )}
          {canManageVoice && <div className="voice-clone-section" data-tour="chat-voice">
            {hasCustomVoice ? (
              <div className="voice-status-row">
                <span className="voice-status">✅ {t('chat.voice_uploaded')}</span>
                <button
                  className="btn-voice-change"
                  onClick={() => { setVoiceStep(2); setShowVoicePanel(true) }}
                >
                  {t('chat.voice_change')}
                </button>
              </div>
            ) : (
              <button
                className="btn-voice-clone"
                onClick={() => { setVoiceStep(0); setShowVoicePanel(true) }}
              >
                🎤 {t('chat.voice_clone')}
              </button>
            )}
          </div>}
        </div>
      </div>

      {canManageVoice && showVoicePanel && createPortal(
        <dialog className="voice-wizard" ref={voiceDialog} aria-labelledby="voice-wizard-title" onCancel={(e) => { e.preventDefault(); if (!voiceBusy && !voiceRecorder.isRecording) { setShowVoicePanel(false); voiceRecorder.reset() } }}>
        <div className="voice-clone-panel">
          <div className="voice-clone-panel-header">
            <h3 id="voice-wizard-title">{localText('Настройка голоса', 'Voice setup')}</h3>
            <button type="button" className="btn-close-panel" disabled={voiceBusy || voiceRecorder.isRecording} onClick={() => { setShowVoicePanel(false); voiceRecorder.reset() }} aria-label={t('chat.voice_panel_close')}>✕</button>
          </div>
          <ol className="voice-wizard-steps" aria-label={localText('Этапы настройки', 'Setup steps')}>
            {[localText('Запись', 'Recording'), localText('Подготовка', 'Preparation'), localText('Звучание', 'Sound'), localText('Готово', 'Done')].map((label, i) => <li key={label} aria-current={voiceStep === i ? 'step' : undefined} className={voiceStep === i ? 'active' : voiceStep > i ? 'complete' : ''}><span>{i + 1}</span>{label}</li>)}
          </ol>
          <div className="voice-wizard-body" ref={voiceBody}>
          {voiceStep === 0 && <>
          <h4>{localText('Добавьте запись голоса', 'Add a voice recording')}</h4>
          <p className="voice-preparation-note">{localText('Лучше всего — 30–60 секунд речи одного человека без музыки и сильного эха. Можно загрузить видео: звук извлечётся автоматически.', 'Use 30–60 seconds of one person speaking, without music or strong echo. Video is supported: audio is extracted automatically.')}</p>
          <div className="voice-clone-name">
            <input
              type="text"
              placeholder={t('chat.voice_name_placeholder')}
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              disabled={uploadingVoice || preparingSample !== null || previewBusy !== null}
            />
          </div>
          <div className="voice-clone-options">
            <div className="voice-clone-option">
              <p className="option-label">{t('chat.voice_record_now')} <span className="option-hint">{t('chat.voice_if_alive')}</span>:</p>
              {!voiceRecorder.audioBlob ? (
                <div className="record-controls">
                  {!voiceRecorder.isRecording ? (
                    <button type="button" className="btn-record" onClick={voiceRecorder.start} disabled={uploadingVoice || preparingSample !== null || previewBusy !== null}>
                      🔴 {t('chat.voice_record_start')}
                    </button>
                  ) : (
                    <button type="button" className="btn-record recording" onClick={voiceRecorder.stop}>
                      ⏹️ {t('chat.voice_record_stop')}
                    </button>
                  )}
                  {voiceRecorder.isRecording && <span className="rec-indicator">{t('chat.rec_indicator')}</span>}
                </div>
              ) : (
                <div className="audio-preview">
                  <ChatAudioPlayer src={voiceRecorder.audioUrl} className="audio-player-small" />
                  <div className="audio-preview-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleAddRecording}
                      disabled={uploadingVoice || preparingSample !== null || previewBusy !== null}
                    >
                      ➕ {t('chat.voice_add_sample')}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={voiceRecorder.reset}>
                      {t('chat.voice_rerecord')}
                    </button>
                  </div>
                </div>
              )}
            </div>
            <div className="voice-clone-divider">{t('chat.voice_or')}</div>
            <div className="voice-clone-option">
              <p className="option-label">{t('chat.voice_upload_label')} <span className="option-hint">{t('chat.voice_upload_hint')}</span>:</p>
              <p className="option-sublabel">{t('chat.voice_video_hint')}</p>
              <label className="btn-upload-voice">
                {uploadingVoice ? `⏳ ${t('chat.voice_cloning')}` : `📁 ${t('chat.voice_choose_file')}`}
                <input
                  type="file"
                  accept="audio/*,video/mp4,video/quicktime,video/webm,.mp4,.mov,.m4v,.webm"
                  multiple
                  onChange={handleVoiceUpload}
                  disabled={uploadingVoice || preparingSample !== null || previewBusy !== null}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          </div>

          </>}
          {voiceStep === 2 && hasCustomVoice && ttsStatus?.provider === 'fish_audio' && <section className="voice-clone-samples">
            <h4>{localText('Сравнить звучание моделей', 'Compare model voices')}</h4>
            <p className="voice-preparation-note">{localText('Один клон, одинаковый тестовый текст, темп 1×. Создание теста оплачивается по тарифу Fish Audio; повторное прослушивание готового теста бесплатно. После выбора модели тестовые записи удалятся из этого окна; клон сохранится.', 'One clone, identical test text, speed 1×. Generating a preview is billed by Fish Audio; replaying it is free. Selecting a model clears the temporary previews; your clone stays unchanged.')}</p>
            {['s1', 's2-pro', 's2.1-pro'].map((model) => <div key={model} className="voice-sample-preview" style={{ marginBottom: 12 }}>
              <strong>{model} {ttsStatus.model === model ? localText('— используется', '— selected') : ''}</strong>
              <button type="button" className="btn-voice-change" disabled={previewBusy !== null || uploadingVoice || preparingSample !== null} onClick={() => handleModelPreview(model)}>{previewBusy === model ? localText('Подготовка…', 'Preparing…') : localText('Создать тестовую озвучку', 'Generate voice preview')}</button>
              {modelPreviews[model] && <>
                <audio controls preload="metadata" src={modelPreviews[model]} />
                <button type="button" className="btn-voice-change" disabled={previewBusy !== null || uploadingVoice} onClick={() => handleSelectModel(model)}>{localText('Использовать эту модель', 'Use this model')}</button>
              </>}
            </div>)}
          </section>}

          {voiceStep === 1 && voiceSamples.length > 0 && (
            <div className="voice-clone-samples">
              <p className="voice-preparation-note">{localText('Для естественного клона выберите 30–60 секунд спокойной речи одного человека, без музыки, других голосов и сильного эха. Не смешивайте разные записи по громкости и манере речи. Если исходник звучит хорошо, очистка не нужна. После очистки исходный образец остаётся выбранным — переключитесь только после сравнения.', 'For a natural clone, choose 30–60 seconds of calm speech by one person, without music, other voices or strong echo. Avoid mixing recordings with different levels or speaking styles. Clean recordings do not need processing. The original remains selected after cleaning; switch only after comparing.')}</p>
              <p className="voice-preparation-note">{localText('Мягкая очистка уменьшает шум и тихие вдохи, но может затронуть тихую речь. Сравните записи. Файлы доступны для повторной попытки, пока открыта эта страница. Повторный клон может звучать так же. Повторное клонирование — новая операция по тарифу провайдера.', 'Gentle cleaning reduces noise and quiet breaths but may affect quiet speech. Compare recordings. Samples remain available while this page is open. A recreated clone may sound the same. Recreating a clone is a new operation under the provider’s pricing.')}</p>
              <p className="option-label">{t('chat.voice_samples_count', { n: String(voiceSamples.length) })}</p>
              <ul className="voice-samples-list">
                {voiceSamples.map((s) => (
                  <li key={s.id} className="voice-samples-item">
                    <div className="voice-sample-preview">
                      <span className="voice-samples-item-label">🎵 {s.label}</span>
                      <label>{localText('Исходная запись', 'Original recording')}<audio controls preload="metadata" src={s.originalUrl} /></label>
                      <button type="button" className="btn-voice-change" disabled={uploadingVoice || preparingSample !== null || previewBusy !== null} onClick={() => handlePrepareSample(s)}>
                        {preparingSample === s.id ? localText('Очищаем…', 'Cleaning…') : localText('Очистить и прослушать', 'Clean and preview')}
                      </button>
                      {s.cleanedUrl && <>
                        <label>{localText('Очищенная запись', 'Cleaned recording')}<audio controls preload="metadata" src={s.cleanedUrl} /></label>
                        <label><input type="checkbox" checked={s.useCleaned} onChange={(e) => setVoiceSamples((prev) => prev.map((item) => item.id === s.id ? { ...item, useCleaned: e.target.checked } : item))} disabled={uploadingVoice || preparingSample !== null || previewBusy !== null} /> {localText('Клонировать из очищенной записи', 'Clone from cleaned recording')}</label>
                      </>}
                    </div>
                    <button
                      type="button"
                      className="btn-remove-sample"
                      onClick={() => handleRemoveSample(s.id)}
                      disabled={uploadingVoice || preparingSample !== null || previewBusy !== null}
                      aria-label={t('chat.voice_remove_sample')}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>

            </div>
          )}
          {voiceStep === 3 && <div className="voice-wizard-success">
            <span aria-hidden="true">✓</span>
            <h4>{localText('Голос готов к разговору', 'Your voice is ready')}</h4>
            <p>{localText('Выбрана модель', 'Selected model')}: <strong>{ttsStatus?.model || ttsStatus?.provider}</strong></p>
            <p>{localText('Новые ответы будут звучать этим голосом. Повторно создавать клон не нужно.', 'New answers will use this voice. There is no need to create the clone again.')}</p>
          </div>}
          </div>
          <footer className="voice-wizard-footer">
            <div>{voiceStep === 0 && <small>{localText('Добавлено записей', 'Recordings added')}: {voiceSamples.length}</small>}
              {voiceStep === 2 && <button type="button" className="btn btn-secondary" disabled={voiceBusy} onClick={() => setVoiceStep(0)}>{localText('Заменить запись', 'Replace recording')}</button>}
              {voiceStep === 1 && <button type="button" className="btn btn-secondary" disabled={voiceBusy} onClick={() => setVoiceStep(0)}>{localText('Назад', 'Back')}</button>}
            </div>
            {voiceStep === 0 && <button type="button" className="btn btn-primary" disabled={!voiceSamples.length || voiceBusy || voiceRecorder.isRecording} onClick={() => setVoiceStep(1)}>{localText('Далее: прослушать запись', 'Next: listen to recording')}</button>}
            {voiceStep === 1 && <button type="button" className="btn btn-primary" disabled={!voiceSamples.length || voiceBusy} onClick={handleCloneVoice}>{uploadingVoice ? localText('Создаём голос…', 'Creating voice…') : localText('Создать голос и выбрать звучание', 'Create voice and choose sound')}</button>}
            {voiceStep === 2 && <button type="button" className="btn btn-primary" disabled={voiceBusy} onClick={() => setVoiceStep(3)}>{localText('Оставить текущую модель', 'Keep current model')}</button>}
            {voiceStep === 3 && <button type="button" className="btn btn-primary" onClick={() => { setShowVoicePanel(false); voiceRecorder.reset(); setIncludeAudio(true) }}>{localText('Готово — перейти в чат', 'Done — return to chat')}</button>}
          </footer>
        </div>
        </dialog>, document.body
      )}

      {!textOnly && includeAudio && <details className="speech-settings">
        <summary>{localText('Настройки озвучивания', 'Speech settings')}</summary>
        {ttsStatus?.provider === 'fish_audio' && <label>{localText('Темп голоса', 'Speech speed')} <select value={speechSpeed} onChange={(e) => setSpeechSpeed(Number(e.target.value))}>
          <option value="0.85">0.85×</option><option value="0.95">0.95×</option><option value="1">1×</option><option value="1.1">1.1×</option>
        </select></label>}
        <label>{localText('Произношение: слово = как произнести (до 20 строк)', 'Pronunciation: word = spoken spelling (up to 20 lines)')}
          <textarea rows="3" maxLength={3300} value={pronunciationText} onChange={(e) => setPronunciationText(e.target.value)} placeholder={localText('Сачко = Сачкó', 'name = phonetic spelling')} />
        </label>
        <p>{localText('Меняется только озвучка, текст ответа сохраняется. Ударения зависят от модели: проверьте на коротком ответе. Для спокойной речи попробуйте 0.85× или 0.95×.', 'Only speech changes; the written answer stays unchanged. Stress depends on the model: test a short answer. Try 0.85× or 0.95× for a slower pace.')}</p>
      </details>}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>{t('chat.welcome_intro')}</p>
            <div className="suggested-questions">
              <p className="suggested-label">{t('chat.suggested_label')}</p>
              <div className="suggested-list">
                {t('chat.questions').map((q, i) => (
                  <button
                    key={i}
                    className="suggested-btn"
                    onClick={() => handleSuggestedQuestion(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {(Array.isArray(messages) ? messages : []).map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'assistant' && (
              <div className="message-avatar">
                {avatarPhotoId ? (
                  <ApiMediaImage
                    mediaId={avatarPhotoId}
            portrait={{ memorialId, kind: 'avatar', version: portraitVersion }}
                    thumbnail="medium"
                    alt={memorialName || 'Avatar'}
                    className="message-avatar-img"
                    fallback={
                      <div className="message-avatar-placeholder">
                        {memorialName ? memorialName[0].toUpperCase() : '?'}
                      </div>
                    }
                  />
                ) : (
                  <div className="message-avatar-placeholder">
                    {memorialName ? memorialName[0].toUpperCase() : '?'}
                  </div>
                )}
              </div>
            )}
            <div className="message-content">
              <p>{msg.text}</p>
              {msg.videoUrl ? (
                <div className="video-container">
                  <video
                    controls
                    autoPlay
                    src={msg.videoUrl}
                    className="avatar-video"
                  >
                    {t('chat.browser_no_video')}
                  </video>
                </div>
              ) : msg.videoStatus === 'pending' ? (
                <div className="video-loading">
                  <span className="video-loading-icon">🎬</span> {t('chat.video_generating')}
                </div>
              ) : getPlayableAudioUrl(msg.audioUrl) ? (
                <div className="audio-container">
                  <ChatAudioPlayer
                    src={getPlayableAudioUrl(msg.audioUrl)}
                    className="audio-player"
                  />
                </div>
              ) : msg.audioError ? (
                <div className="audio-error">
                  {t('chat.audio_failed')} {msg.audioError}
                </div>
              ) : null}
              {Array.isArray(msg.sources) && msg.sources.length > 0 && (
                <details className="chat-sources-details">
                  <summary className="chat-sources-summary">
                    {t('chat.sources_toggle', { count: msg.sources.length })}
                  </summary>
                  <ul className="chat-sources-list">
                    {msg.sources.map((source, i) => (
                      <li key={i}>{source}</li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {chatBlocked && <div className="chat-limit-actions">
        {!user ? <>
          <Link className="btn btn-primary" to={`/register?next=${encodeURIComponent(authReturn)}`} state={{ from: { pathname: authReturn } }}>{lang === 'en' ? 'Register — 15 questions per month' : 'Зарегистрироваться — 15 вопросов в месяц'}</Link>
          <Link to={`/login?next=${encodeURIComponent(authReturn)}`} state={{ from: { pathname: authReturn } }}>{lang === 'en' ? 'Sign in' : 'Войти'}</Link>
        </> : <Link className="btn btn-primary" to={`/pricing?next=${encodeURIComponent(authReturn)}`}>{lang === 'en' ? 'Choose a plan' : 'Выбрать тариф'}</Link>}
      </div>}
      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('chat.placeholder')}
          disabled={loading || disabled || chatBlocked}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || disabled || chatBlocked || !input.trim()}
          className="send-btn"
        >
          {t('chat.send')}
        </button>
      </form>
      </div>{/* end .chat-panel */}
    </div>
  )
}

export default AvatarChat
