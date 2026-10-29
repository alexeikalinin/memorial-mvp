import {GUEST_ANSWERS_ENABLED} from '../config/guestAnswers'
import { createAudioRecorder, recordingBlob, recordingFile, releaseRecorder } from '../utils/audioRecording'
import { createPortal } from 'react-dom'
import { useState, useRef, useEffect, useCallback, useId } from 'react'
import apiClient, { aiAPI, memorialsAPI } from '../api/client'
import ApiMediaImage from './ApiMediaImage'
import ChatAudioPlayer from './ChatAudioPlayer'
import { Link, useLocation } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import { useAuth } from '../context/AuthContext'
import './AvatarChat.css'
import FeaturedAnswers from './FeaturedAnswers'

// Запись аудио для клона голоса
function useVoiceRecorder() {
  const { t } = useLanguage()
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => () => releaseRecorder(recorderRef.current), [])

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = createAudioRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
      recorder.onstop = () => {
        const blob = recordingBlob(chunksRef.current, recorder)
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
  if (url.startsWith('/api/v1/')) return `${(import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')}${url.slice(7)}`
  if (/^https?:\/\//.test(url) || url.startsWith('/')) return url
  const base = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
  return `${base}/media/audio/${url}`
}

function AvatarChat({ memorialId, coverPhotoId, memorialName, onMessageSent, portraitSettings, onEditPortrait, canManageVoice = false, textOnly = false, disabled = false, inviteToken, onAddMemory }) {
  const location = useLocation()
  const [quotaBlocked, setQuotaBlocked] = useState(false)
  const [chatUsage, setChatUsage] = useState(null)
  const authReturn = `${location.pathname}${location.search}${location.hash}`
  const avatarPhotoId = portraitSettings?.avatar?.media_id || coverPhotoId
  const portraitVersion = JSON.stringify(portraitSettings || {})
  const [messages, setMessages] = useState([])
  const [speechStyle, setSpeechStyle] = useState('natural')
  const [revoiceBusy, setRevoiceBusy] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [includeAudio, setIncludeAudio] = useState(false)
  const { lang, t } = useLanguage()
  const { user } = useAuth()
  const monthlyLimitReached = !!user && chatUsage?.chat_messages_limit != null && chatUsage.chat_messages_used >= chatUsage.chat_messages_limit
  const chatBlocked = quotaBlocked || monthlyLimitReached
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showChatSettings, setShowChatSettings] = useState(false)
  const chatSettingsDialog = useRef(null)
  const settingsTitleId = useId()
  useEffect(() => {
    const dialog = chatSettingsDialog.current
    if (showChatSettings && dialog && !dialog.open) dialog.showModal()
    if (!showChatSettings && dialog?.open) dialog.close()
  }, [showChatSettings])
  useEffect(() => { setShowChatSettings(false) }, [memorialId])

  const chatContainerRef = useRef(null)
  useEffect(() => {
    if (!isFullscreen) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const focusFrame = requestAnimationFrame(() => chatContainerRef.current?.querySelector('.btn-fullscreen')?.focus())
    const onKeyDown = (event) => {
      if (document.querySelector('dialog[open]')) return
      if (event.key === 'Escape') {
        event.preventDefault()
        setIsFullscreen(false)
      }
      if (event.key === 'Tab') {
        const controls = [...(chatContainerRef.current?.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), a[href], summary') || [])]
          .filter(element => element.getClientRects().length)
        const first = controls[0], last = controls[controls.length - 1]
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      cancelAnimationFrame(focusFrame)
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [isFullscreen])

  const [includeFamilyMemories, setIncludeFamilyMemories] = useState(false)
  const prepareForGuests=GUEST_ANSWERS_ENABLED && !textOnly && canManageVoice && new URLSearchParams(location.search).get('prepareGuests')==='1'

  // Family RAG is a paid feature (Plus / Pro). Free users see a locked toggle.
  const hasFamilyRag = user && (user.is_admin || user.is_demo || ['plus', 'pro', 'lifetime_pro'].includes(user.subscription_plan))
  useEffect(()=>{setIncludeFamilyMemories(Boolean(hasFamilyRag))},[hasFamilyRag,user?.id])
  const useFamilySearch=!textOnly && Boolean(hasFamilyRag) && includeFamilyMemories && !prepareForGuests
  const [uploadingVoice, setUploadingVoice] = useState(false)
  const [voiceVersions, setVoiceVersions] = useState([])
  const [versionPreviews, setVersionPreviews] = useState({})
  const [versionBusy, setVersionBusy] = useState(null)
  const refreshVoiceVersions = useCallback(async () => {
    const generation = sampleGeneration.current
    const response = await aiAPI.listVoiceVersions(memorialId)
    if (generation === sampleGeneration.current) setVoiceVersions(response.data.voices)
  }, [memorialId])
  const handleSavedVoice = async (version, select) => {
    const generation = sampleGeneration.current
    setVersionBusy(version.id)
    try {
      if (select) {
        await aiAPI.selectVoiceVersion(memorialId, version.id)
        if (generation !== sampleGeneration.current) return
        await refreshVoiceVersions()
        const status = await aiAPI.getTtsStatus(memorialId)
        setTtsStatus(status.data)
        setHasCustomVoice(true)
        Object.values(modelPreviews).forEach((url) => URL.revokeObjectURL(url))
        setModelPreviews({})
      } else if (!versionPreviews[version.id]) {
        const response = await aiAPI.previewVoiceVersion(memorialId, version.id, localText('ru', 'en'))
        if (generation !== sampleGeneration.current) return
        setVersionPreviews((prev) => ({ ...prev, [version.id]: sampleUrl(new Blob([response.data], { type: 'audio/mpeg' })) }))
      }
    } catch (error) {
      alert(error.response?.data?.detail || localText('Не удалось загрузить голос.', 'Could not load the voice.'))
    } finally { if (generation === sampleGeneration.current) setVersionBusy(null) }
  }

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
  const voiceBusy = uploadingVoice || preparingSample !== null || previewBusy !== null || versionBusy !== null
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
    const urls = sampleUrls.current
    return () => {
      sampleGeneration.current += 1
      urls.forEach((url) => URL.revokeObjectURL(url))
      urls.clear()
    }
  }, [memorialId])
  useEffect(() => {
    setVoiceVersions([])
    setVersionBusy(null)
    setVersionPreviews({})
    if (canManageVoice) refreshVoiceVersions().catch(() => {})
  }, [memorialId, canManageVoice, refreshVoiceVersions])
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
    const file = recordingFile(voiceRecorder.audioBlob, `voice_clone_${voiceSamples.length + 1}`)
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
      await refreshVoiceVersions()
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
        if (!useFamilySearch) setQuotaBlocked(true)
        alert(`⚠️ ${detail}`)
      } else {
        alert(detail)
      }
    } finally {
      setUploadingVoice(false)
    }
  }

  const handleChooseAudio = async (message, index, accept) => {
    if (revoiceBusy || !message.audioPreview) return
    setRevoiceBusy(true)
    try {
      const preview = message.audioPreview
      const response = await apiClient.post(`/ai/avatar/audio-preview/${preview.cacheId}/${preview.id}`, { accept })
      setMessages(previous => previous.map((item, i) => i === index ? { ...item,
        ...(accept ? { audioUrl: response.data.audio_url, audioError: null, audioStyle: preview.style } : {}), audioPreview: null } : item))
    } catch { alert(localText('Не удалось сохранить выбор. Попробуйте ещё раз.', 'Could not save your choice. Please retry.')) }
    finally { setRevoiceBusy(false) }
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
        speech_style: speechStyle,
        pronunciations,
        include_audio: !textOnly && includeAudio,
        include_family_memories: useFamilySearch,
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
        question: userMessage,
        familyContext: useFamilySearch,
        pronunciations,
        text: response.data.answer,
        audioUrl,
        audioStyle: textOnly ? null : speechStyle,
        audioError: response.data.audio_error || null,
        animationTaskId: response.data.animation_task_id || null,
        animationProvider: response.data.animation_provider || null,
        videoUrl: null,
        videoStatus: response.data.animation_task_id ? 'pending' : null,
        sources: response.data.sources || [],
        suggestMemory: response.data.suggest_memory === true,
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
        if (!useFamilySearch) setQuotaBlocked(true)
        if (useFamilySearch) {
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

  const chatContent = (
    <div ref={chatContainerRef} className={`avatar-chat${isFullscreen ? ' avatar-chat--fullscreen' : ''}`} role={isFullscreen ? 'dialog' : undefined} aria-modal={isFullscreen || undefined} aria-label={isFullscreen ? localText('Чат с аватаром', 'Avatar chat') : undefined}>
      {/* ─── Left: Avatar panel ──────────────────────────────────── */}
      <div className="avatar-panel">
        {avatarPhotoId ? (
          <ApiMediaImage
            mediaId={avatarPhotoId}
            thumbnail={null}
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
      {prepareForGuests && <aside className="chat-guest-preparation" aria-label={localText('Подготовка ответа для гостей','Prepare a guest answer')}><strong>{localText('Подготовка ответа для гостей','Preparing a guest answer')}</strong><p>{localText('Задайте вопрос. Для аудио включите «Голос» перед отправкой. Здесь используются только воспоминания этого мемориала; ответ ещё не опубликован.', 'Ask a question. Turn on Voice before sending if you want audio. Only this memorial’s memories are used; nothing is published yet.')}</p><Link to={`/memorials/${memorialId}?tab=memories`}>{localText('Выбрать сохранённые ответы для гостей','Choose saved answers for guests')}</Link><Link to={`/memorials/${memorialId}?tab=chat`}>{localText('Вернуться к обычному разговору','Return to a normal conversation')}</Link></aside>}

      <div className="chat-header chat-header--minimal">
        <div className="chat-header-title">
          <h2 title={memorialName || undefined}>{memorialName || t('chat.title_default')}</h2>
          <span className="chat-header-subtitle">{localText('Разговор', 'Conversation')}</span>
        </div>
        <div className="header-controls">
          {!textOnly && <label className={`chat-voice-toggle${includeAudio ? ' is-active' : ''}`} data-tour="chat-audio-toggle" title={t('chat.audio_label')}>
            <input type="checkbox" checked={includeAudio} onChange={e => setIncludeAudio(e.target.checked)} aria-label={t('chat.audio_label')} />
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5Z" /><path d={includeAudio ? 'M15 8c3 2 3 6 0 8m3-11c5 4 5 10 0 14' : 'm16 9 5 6m0-6-5 6'} /></svg>
            <span>{localText('Голос', 'Voice')}</span>
          </label>}
          <button type="button" className="btn-fullscreen chat-tool-button" onClick={() => setIsFullscreen(value => !value)} title={isFullscreen ? t('chat.exit_fullscreen') : t('chat.fullscreen')} aria-label={isFullscreen ? t('chat.exit_fullscreen') : t('chat.fullscreen')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d={isFullscreen ? 'M9 3v6H3m12-6v6h6M3 15h6v6m12-6h-6v6' : 'M9 3H3v6m12-6h6v6M3 15v6h6m12-6v6h-6'} /></svg>
          </button>
          <button type="button" className="chat-tool-button chat-settings-toggle" onClick={() => setShowChatSettings(true)} title={localText('Настройки чата', 'Chat settings')} aria-label={localText('Настройки чата', 'Chat settings')} aria-haspopup="dialog" aria-expanded={showChatSettings} data-tour="chat-voice">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="1.6" /><circle cx="12" cy="12" r="1.6" /><circle cx="19" cy="12" r="1.6" /></svg>
          </button>
        </div>
      </div>

      {createPortal(<dialog ref={chatSettingsDialog} className="chat-settings-dialog" aria-labelledby={settingsTitleId} onCancel={() => setShowChatSettings(false)} onClose={() => setShowChatSettings(false)} onClick={event => { if (event.target === event.currentTarget) setShowChatSettings(false) }}>
        <div className="chat-settings-heading"><h3 id={settingsTitleId}>{localText('Настройки разговора', 'Conversation settings')}</h3><button type="button" className="chat-tool-button" onClick={() => setShowChatSettings(false)} aria-label={localText('Закрыть настройки', 'Close settings')}>×</button></div>
        <div className="chat-settings-body">
          {!textOnly && (includeAudio || hasCustomVoice) && <section className="speech-settings"><h4>{localText('Эмоции и звучание', 'Emotion and delivery')}</h4>

        {ttsStatus?.provider === 'fish_audio' && <label>{localText('Подача', 'Delivery')} <select value={speechStyle} onChange={e => setSpeechStyle(e.target.value)}><option value="natural">{localText('Естественно', 'Natural')}</option><option value="calm">{localText('Спокойно', 'Calm')}</option><option value="warm">{localText('Тепло', 'Warm')}</option><option value="happy">{localText('Радостно', 'Happy')}</option><option value="sad">{localText('С грустью', 'Sad')}</option><option value="nostalgic">{localText('Ностальгично', 'Nostalgic')}</option></select></label>}
            <details className="chat-settings-advanced"><summary>{localText('Темп и произношение', 'Speed and pronunciation')}</summary>
        {ttsStatus?.provider === 'fish_audio' && <label>{localText('Темп голоса', 'Speech speed')} <select value={speechSpeed} onChange={(e) => setSpeechSpeed(Number(e.target.value))}>
          <option value="0.85">0.85×</option><option value="0.95">0.95×</option><option value="1">1×</option><option value="1.1">1.1×</option>
        </select></label>}
        <label>{localText('Произношение: слово = как произнести (до 20 строк)', 'Pronunciation: word = spoken spelling (up to 20 lines)')}
          <textarea rows="3" maxLength={3300} value={pronunciationText} onChange={(e) => setPronunciationText(e.target.value)} placeholder={localText('Сачко = Сачкó', 'name = phonetic spelling')} />
        </label>
        <p>{localText('Новый дубль создаётся платным запросом к сервису озвучки. Повторное прослушивание готовой записи не запускает генерацию.', 'A new take uses a paid speech request. Replaying an existing recording does not generate it again.')}</p>
        <p>{localText('Меняется только озвучка, текст ответа сохраняется. Ударения зависят от модели: проверьте на коротком ответе. Для спокойной речи попробуйте 0.85× или 0.95×.', 'Only speech changes; the written answer stays unchanged. Stress depends on the model: test a short answer. Try 0.85× or 0.95× for a slower pace.')}</p>

            </details>
            <p>{localText('Подача применяется к новым дублям. Готовые записи остаются прежними, пока вы не выберете замену.', 'Delivery applies to new takes. Existing audio stays unchanged until you choose a replacement.')}</p>

          </section>}
          {canManageVoice && <section className="chat-settings-section">
            <h4>{localText('Голос и портрет', 'Voice and portrait')}</h4>
            <p>{hasCustomVoice ? localText('Используется сохранённый голос.', 'Using your saved voice.') : localText('Добавьте образец, чтобы настроить голос.', 'Add a sample to set up the voice.')}</p>
            <div className="chat-settings-actions"><button type="button" onClick={() => { setShowChatSettings(false); setVoiceStep(hasCustomVoice ? 2 : 0); setShowVoicePanel(true) }}>{hasCustomVoice ? localText('Изменить голос', 'Change voice') : localText('Настроить голос', 'Set up voice')}</button>
            {onEditPortrait && <button type="button" onClick={() => { setShowChatSettings(false); onEditPortrait() }}>{t('portraits.edit_avatar')}</button>}</div>
          </section>}
          {!textOnly && <section className="chat-settings-section">
            <h4>{localText('Семейные воспоминания', 'Family memories')}</h4>
            <label className="chat-settings-check"><input type="checkbox" checked={useFamilySearch} disabled={!hasFamilyRag || prepareForGuests} onChange={e => setIncludeFamilyMemories(e.target.checked)} />{t('chat.family_label')}</label>
            <p>{localText('Помогает аватару отвечать на вопросы, используя также воспоминания связанных родственников, к которым у вас есть доступ. Включайте, если хотите учитывать общие семейные истории.', 'Helps the avatar answer using accessible memories of linked relatives. Enable it to include shared family stories.')}</p>
            <p>{localText('Работает во время разговора. Новые записи в архиве не создаются.', 'Works during the conversation. It does not create archive entries.')}</p>
            <details><summary>{localText('Пример: как это работает', 'Example: how it works')}</summary><p>{localText('У Светланы записано: «Мы с Ларисой каждое лето ездили к бабушке». На странице Ларисы такой истории нет. Если их страницы связаны родством и у вас есть доступ, аватар Ларисы сможет использовать воспоминание Светланы для ответа о летних поездках.', 'Svetlana has a memory: “Larisa and I visited our grandmother every summer.” Larisa’s page has no such memory. If their pages are linked and you have access, Larisa’s avatar can use Svetlana’s memory to answer about those summer visits.')}</p><p>{localText('История останется на странице Светланы. Чтобы пользоваться семейным поиском, создавать связанные записи отдельно не требуется.', 'The memory stays on Svetlana’s page. You do not need to create linked entries to use family search.')}</p></details>
            {prepareForGuests && <p>{localText('В режиме подготовки для гостей используются только воспоминания этого мемориала.', 'Guest preparation uses only this memorial’s memories.')}</p>}
            {!hasFamilyRag && <p>{t('chat.family_locked_tooltip')}</p>}
          </section>}
          <section className="chat-settings-section chat-settings-usage"><h4>{localText('Использование', 'Usage')}</h4>
      {ttsStatus?.provider === 'fish_audio' ? (
        !ttsStatus.configured && <p className="chat-tts-quota">{t('chat.tts_fish_off')}</p>
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

          </section>
          {messages.length > 0 && <button type="button" className="chat-settings-danger" onClick={handleClearHistory}>{t('chat.clear_history')}</button>}
        </div>
      </dialog>, document.body)}

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
          <section className="voice-clone-samples voice-library" aria-label={localText('Сохранённые голоса', 'Saved voices')}>
            <h4>{localText('Сохранённые голоса', 'Saved voices')}</h4>
            <p className="option-hint">{localText('Новый клон сохраняется отдельно. Смена сохранённого голоса не запускает клонирование. Новая тестовая озвучка расходует API-баланс; повторно слушайте уже созданную запись.', 'New clones are saved separately. Switching saved voices does not clone again. A new voice preview uses API credits; replay an existing preview instead.')}</p>
            {voiceVersions.map((version) => <div key={version.id} className="voice-samples-item voice-version">
              <strong>{version.name} #{version.id} {version.active ? localText('· используется', '· selected') : ''}</strong>
              {version.state === 'ready' ? <>
                {version.provider === 'fish_audio' && !versionPreviews[version.id] && <button type="button" className="btn-voice-change" disabled={voiceBusy || versionBusy !== null} onClick={() => handleSavedVoice(version, false)}>{localText('Создать тестовую озвучку', 'Generate voice preview')}</button>}
                {versionPreviews[version.id] && <audio controls preload="metadata" src={versionPreviews[version.id]} />}
                {!version.active && <button type="button" className="btn-voice-change" disabled={voiceBusy || versionBusy !== null} onClick={() => handleSavedVoice(version, true)}>{localText('Использовать этот голос', 'Use this voice')}</button>}
              </> : <span>{version.state === 'pending' ? localText('Обрабатывается — не отправляйте повторно', 'Processing — do not resubmit') : localText('Попытка не завершена. Автоповтор отключён.', 'Attempt did not complete. Automatic retry is disabled.')}</span>}
            </div>)}
          </section>
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
          {ttsStatus?.provider === 'fish_audio' && <p className="option-hint">{localText('Общая длительность всех образцов — меньше 4 минут 30 секунд. Длинную запись нужно предварительно сократить; оригинал не обрезается автоматически.', 'All samples combined must be shorter than 4 minutes 30 seconds. Trim longer recordings first; originals are not automatically trimmed.')}</p>}
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
            {['s2-pro', 's2.1-pro'].map((model) => <div key={model} className="voice-sample-preview" style={{ marginBottom: 12 }}>
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

        {textOnly && <FeaturedAnswers memorialId={memorialId} inviteToken={inviteToken} />}
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
              {msg.role === 'assistant' && msg.suggestMemory && onAddMemory && (
                <div className="chat-memory-invitation">
                  <p>{t('chat.add_memory_hint')}</p>
                  <button type="button" className="btn btn-secondary" onClick={onAddMemory}>
                    {t('public.share_memory')}
                  </button>
                </div>
              )}
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
                  {msg.audioStyle && <p className="audio-style-label">{localText('Текущая озвучка: ', 'Current delivery: ')}{({ natural: localText('Естественно', 'Natural'), calm: localText('Спокойно', 'Calm'), warm: localText('Тепло', 'Warm'), happy: localText('Радостно', 'Happy'), sad: localText('С грустью', 'Sad'), nostalgic: localText('Ностальгично', 'Nostalgic') })[msg.audioStyle]}</p>}
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
              {msg.audioPreview && <section className="audio-preview" aria-label={localText('Новый дубль озвучки', 'New audio take')}>
                <p>{msg.audioPreview.style && <strong>{({ natural: localText('Естественно', 'Natural'), calm: localText('Спокойно', 'Calm'), warm: localText('Тепло', 'Warm'), happy: localText('Радостно', 'Happy'), sad: localText('С грустью', 'Sad'), nostalgic: localText('Ностальгично', 'Nostalgic') })[msg.audioPreview.style]} · </strong>}{localText('Послушайте новый дубль. Прежняя озвучка остаётся активной до вашего выбора.', 'Listen to the new take. Your previous audio stays active until you choose.')}</p>
                <ChatAudioPlayer src={getPlayableAudioUrl(msg.audioPreview.url)} className="audio-player" />
                <div className="audio-preview-actions">
                <button type="button" disabled={revoiceBusy} onClick={() => handleChooseAudio(msg, idx, true)}>{localText('Использовать этот вариант', 'Use this version')}</button>
                <button type="button" disabled={revoiceBusy} onClick={() => handleChooseAudio(msg, idx, false)}>{localText('Оставить прежний', 'Keep previous')}</button>
                </div>
              </section>}
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
  return isFullscreen ? createPortal(chatContent, document.body) : chatContent
}

export default AvatarChat
