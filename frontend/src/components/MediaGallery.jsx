import { useState, useEffect } from 'react'
import { memorialsAPI, aiAPI } from '../api/client'
import './MediaGallery.css'

function MediaGallery({ memorialId, onReload, coverPhotoId, onSetCover }) {
  const [media, setMedia] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [animating, setAnimating] = useState(null)
  const [animationStatus, setAnimationStatus] = useState({}) // { mediaId: { status, taskId, provider } }

  useEffect(() => {
    loadMedia()
  }, [memorialId])

  const loadMedia = async () => {
    try {
      setLoading(true)
      const response = await memorialsAPI.getMedia(memorialId)
      setMedia(response.data)
    } catch (err) {
      console.error('Error loading media:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    try {
      await memorialsAPI.uploadMedia(memorialId, file)
      await loadMedia()
      if (onReload) onReload()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при загрузке файла')
    } finally {
      setUploading(false)
      e.target.value = '' // Сброс input
    }
  }

  const handleDelete = async (mediaId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот файл? Это действие нельзя отменить.')) {
      return
    }

    try {
      await memorialsAPI.deleteMedia(memorialId, mediaId)
      // Обновляем список медиа
      loadMedia()
      if (onReload) onReload()
    } catch (err) {
      const errorDetail = err.response?.data?.detail || 'Ошибка при удалении файла'
      alert(`Ошибка: ${errorDetail}`)
      console.error('Error deleting media:', err)
    }
  }

  const handleAnimate = async (mediaId) => {
    setAnimating(mediaId)
    try {
      const response = await aiAPI.animatePhoto({ media_id: mediaId })
      const taskId = response.data.task_id
      const provider = response.data.provider || 'heygen'
      
      // Сохраняем статус анимации
      setAnimationStatus(prev => ({
        ...prev,
        [mediaId]: {
          status: 'pending',
          taskId: taskId,
          provider: provider,
          message: response.data.message || 'Анимация запущена'
        }
      }))
      
      // Начинаем polling для проверки статуса
      startAnimationPolling(mediaId, taskId, provider)
      
    } catch (err) {
      const errorDetail = err.response?.data?.detail || 'Ошибка при запуске анимации'
      let errorMessage = errorDetail
      
      // Понятное сообщение для ошибки Redis
      if (errorDetail.includes('Redis') || errorDetail.includes('Celery') || errorDetail.includes('worker')) {
        errorMessage = `⚠️ Для анимации фото необходимо запустить Redis и Celery worker.\n\n` +
          `Инструкция:\n` +
          `1. Запустите Redis: docker run -d -p 6379:6379 redis\n` +
          `2. Запустите Celery worker: cd backend && celery -A app.workers.worker worker --loglevel=info\n\n` +
          `Подробнее см. в документации.`
      }
      
      alert(errorMessage)
    } finally {
      setAnimating(null)
    }
  }

  const startAnimationPolling = (mediaId, taskId, provider) => {
    let attempts = 0
    const maxAttempts = 120 // 10 минут при проверке каждые 5 секунд
    const pollInterval = 5000 // 5 секунд

    const poll = async () => {
      if (attempts >= maxAttempts) {
        setAnimationStatus(prev => ({
          ...prev,
          [mediaId]: {
            ...prev[mediaId],
            status: 'timeout',
            message: 'Превышено время ожидания'
          }
        }))
        return
      }

      try {
        const response = await aiAPI.getAnimationStatus({
          provider: provider,
          task_id: taskId,
          media_id: mediaId  // Передаем media_id для поиска video_id в БД
        })

        const status = response.data.status
        const videoUrl = response.data.video_url
        const error = response.data.error

        if (status === 'completed' || status === 'done' || status === 'success') {
          if (videoUrl) {
            // Анимация завершена
            setAnimationStatus(prev => ({
              ...prev,
              [mediaId]: {
                ...prev[mediaId],
                status: 'completed',
                videoUrl: videoUrl
              }
            }))
            
            // Сбрасываем состояние анимации
            setAnimating(null)
            
            // Обновляем медиа, чтобы показать новое видео
            setTimeout(() => {
              loadMedia()
              if (onReload) onReload()
              
              // Очищаем статус анимации через 3 секунды (после показа плашки)
              setTimeout(() => {
                setAnimationStatus(prev => {
                  const newStatus = { ...prev }
                  delete newStatus[mediaId]
                  return newStatus
                })
              }, 3000)
            }, 1000)
            
            return
          } else {
            // Статус completed, но нет URL - продолжаем проверку
            setAnimationStatus(prev => ({
              ...prev,
              [mediaId]: {
                ...prev[mediaId],
                status: 'processing',
                message: 'Ожидание видео...'
              }
            }))
            attempts++
            if (attempts < maxAttempts) {
              setTimeout(poll, pollInterval)
            }
            return
          }
        } else if (status === 'failed' || status === 'error') {
          // Ошибка анимации (только если статус явно failed/error)
          setAnimationStatus(prev => ({
            ...prev,
            [mediaId]: {
              ...prev[mediaId],
              status: 'failed',
              message: error || 'Ошибка при создании анимации'
            }
          }))
          return
        } else if (error && status !== 'processing' && status !== 'pending') {
          // Ошибка, но не при обработке
          setAnimationStatus(prev => ({
            ...prev,
            [mediaId]: {
              ...prev[mediaId],
              status: 'failed',
              message: error
            }
          }))
          return
        } else if (status === 'processing' || status === 'pending' || status === 'not_found') {
          // Продолжаем проверку
          setAnimationStatus(prev => ({
            ...prev,
            [mediaId]: {
              ...prev[mediaId],
              status: 'processing',
              message: 'Обработка...'
            }
          }))
          attempts++
          if (attempts < maxAttempts) {
            setTimeout(poll, pollInterval)
          } else {
            setAnimationStatus(prev => ({
              ...prev,
              [mediaId]: {
                ...prev[mediaId],
                status: 'timeout',
                message: 'Превышено время ожидания'
              }
            }))
          }
        } else {
          // Неизвестный статус, продолжаем проверку
          attempts++
          if (attempts < maxAttempts) {
            setTimeout(poll, pollInterval)
          } else {
            setAnimationStatus(prev => ({
              ...prev,
              [mediaId]: {
                ...prev[mediaId],
                status: 'timeout',
                message: 'Превышено время ожидания'
              }
            }))
          }
        }
      } catch (err) {
        // Ошибка при проверке статуса
        const errorMsg = err.response?.data?.detail || err.message || 'Ошибка при проверке статуса'
        
        // Если 404 или "not found", продолжаем проверку (возможно еще обрабатывается)
        if (err.response?.status === 404 || errorMsg.toLowerCase().includes('not found') || errorMsg.toLowerCase().includes('404')) {
          attempts++
          if (attempts < maxAttempts) {
            setAnimationStatus(prev => ({
              ...prev,
              [mediaId]: {
                ...prev[mediaId],
                status: 'processing',
                message: 'Обработка...'
              }
            }))
            setTimeout(poll, pollInterval)
          } else {
            setAnimationStatus(prev => ({
              ...prev,
              [mediaId]: {
                ...prev[mediaId],
                status: 'timeout',
                message: 'Превышено время ожидания'
              }
            }))
          }
        } else {
          // Другие ошибки - останавливаем polling
          setAnimationStatus(prev => ({
            ...prev,
            [mediaId]: {
              ...prev[mediaId],
              status: 'error',
              message: errorMsg.substring(0, 100)
            }
          }))
        }
      }
    }

    // Начинаем polling через 5 секунд
    setTimeout(poll, pollInterval)
  }

  const getMediaUrl = (mediaItem) => {
    if (mediaItem.file_url) return mediaItem.file_url
    if (mediaItem.thumbnail_path) {
      return `/api/v1/media/${mediaItem.id}?thumbnail=medium`
    }
    return `/api/v1/media/${mediaItem.id}`
  }

  if (loading) {
    return <div className="loading">Загрузка медиа...</div>
  }

  return (
    <div className="media-gallery">
      <div className="gallery-header">
        <h2>Медиа-файлы</h2>
        <label className="upload-btn">
          {uploading ? 'Загрузка...' : 'Загрузить файл'}
          <input
            type="file"
            onChange={handleFileUpload}
            disabled={uploading}
            accept="image/*,video/*,audio/*"
            style={{ display: 'none' }}
          />
        </label>
      </div>

      {media.length === 0 ? (
        <div className="empty-state">
          <p>Пока нет загруженных медиа-файлов</p>
          <label className="upload-btn">
            Загрузить первый файл
            <input
              type="file"
              onChange={handleFileUpload}
              disabled={uploading}
              accept="image/*,video/*,audio/*"
              style={{ display: 'none' }}
            />
          </label>
        </div>
      ) : (
        <div className="gallery-grid">
          {media.map((item) => (
            <div key={item.id} className="media-item">
              {item.media_type === 'photo' && (
                <img src={getMediaUrl(item)} alt={item.file_name} />
              )}
              {item.media_type === 'video' && (
                <video src={getMediaUrl(item)} controls />
              )}
              {item.media_type === 'audio' && (
                <div className="audio-placeholder">
                  <span>🎵</span>
                  <p>{item.file_name}</p>
                </div>
              )}
              {coverPhotoId === item.id && (
                <div className="cover-badge">Обложка</div>
              )}
              <div className="media-actions">
                <div className="media-actions-left">
                  {item.media_type === 'photo' && (
                    <>
                      {onSetCover && (
                        coverPhotoId === item.id ? (
                          <button
                            className="btn-cover active"
                            onClick={() => onSetCover(null)}
                            title="Снять обложку"
                          >
                            Снять обложку
                          </button>
                        ) : (
                          <button
                            className="btn-cover"
                            onClick={() => onSetCover(item.id)}
                            title="Сделать обложкой"
                          >
                            Обложка
                          </button>
                        )
                      )}
                    </>
                  )}
                  {item.media_type === 'photo' && !item.is_animated && (
                    <>
                      <button
                        className="btn-animate"
                        onClick={() => handleAnimate(item.id)}
                        disabled={animating === item.id || animationStatus[item.id]?.status === 'processing' || animationStatus[item.id]?.status === 'pending'}
                      >
                        {animating === item.id ? 'Запуск...' :
                         animationStatus[item.id]?.status === 'processing' || animationStatus[item.id]?.status === 'pending' ? 'Обработка...' :
                         'Оживить фото'}
                      </button>
                      {animationStatus[item.id] && (
                        <div className="animation-status">
                          {animationStatus[item.id].status === 'processing' || animationStatus[item.id].status === 'pending' ? (
                            <span className="status-processing">⏳ {animationStatus[item.id].message || 'Обработка...'}</span>
                          ) : animationStatus[item.id].status === 'completed' ? (
                            <span className="status-completed">✅ Анимация готова!</span>
                          ) : animationStatus[item.id].status === 'failed' || animationStatus[item.id].status === 'error' ? (
                            <span className="status-error">❌ {animationStatus[item.id].message || 'Ошибка'}</span>
                          ) : null}
                        </div>
                      )}
                    </>
                  )}
                  {item.is_animated && (
                    <span className="animated-badge">✅ Оживлено</span>
                  )}
                </div>
                <button
                  className="btn-delete"
                  onClick={() => handleDelete(item.id)}
                  title="Удалить файл"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MediaGallery

