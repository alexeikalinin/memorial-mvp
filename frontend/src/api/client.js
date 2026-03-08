import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptors для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Логируем ошибку, но не показываем весь traceback пользователю
    if (error.response?.data) {
      const errorData = error.response.data
      // Если это детальная ошибка с traceback, извлекаем только сообщение
      if (typeof errorData === 'string' && errorData.includes('Traceback')) {
        // Извлекаем последнюю строку с ошибкой
        const lines = errorData.split('\n')
        const lastError = lines.find(line => 
          line.includes('Error') || line.includes('Exception') || line.includes('Connection')
        )
        if (lastError) {
          console.error('API Error:', lastError)
        } else {
          console.error('API Error:', errorData.substring(0, 200))
        }
      } else {
        console.error('API Error:', errorData)
      }
    } else {
      console.error('API Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default apiClient

// API методы
export const memorialsAPI = {
  list: () => apiClient.get('/memorials/'),
  create: (data) => apiClient.post('/memorials/', data),
  get: (id) => apiClient.get(`/memorials/${id}`),
  update: (id, data) => apiClient.patch(`/memorials/${id}`, data),
  delete: (id) => apiClient.delete(`/memorials/${id}`),
  getQR: (id) => apiClient.get(`/memorials/${id}/qr`, { responseType: 'blob' }),
  uploadMedia: (memorialId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(`/memorials/${memorialId}/media/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getMedia: (memorialId) => apiClient.get(`/memorials/${memorialId}/media`),
  deleteMedia: (memorialId, mediaId) => apiClient.delete(`/memorials/${memorialId}/media/${mediaId}`),
  createMemory: (memorialId, data) =>
    apiClient.post(`/memorials/${memorialId}/memories`, data),
  updateMemory: (memorialId, memoryId, data) =>
    apiClient.patch(`/memorials/${memorialId}/memories/${memoryId}`, data),
  deleteMemory: (memorialId, memoryId) =>
    apiClient.delete(`/memorials/${memorialId}/memories/${memoryId}`),
  getMemories: (memorialId, q = null) =>
    apiClient.get(`/memorials/${memorialId}/memories`, q ? { params: { q } } : {}),
  setCover: (memorialId, mediaId) =>
    apiClient.patch(`/memorials/${memorialId}/cover`, { media_id: mediaId }),
  getTimeline: (memorialId) =>
    apiClient.get(`/memorials/${memorialId}/timeline`),
}

export const aiAPI = {
  animatePhoto: (data) => apiClient.post('/ai/photo/animate', data),
  getAnimationStatus: (data) => apiClient.post('/ai/animation/status', data),
  chat: (data) => apiClient.post('/ai/avatar/chat', data),
  syncFamilyMemories: (memorialId, dryRun = false) =>
    apiClient.post(`/ai/family/sync-memories/${memorialId}?dry_run=${dryRun}`),
  transcribe: (audioFile, language = 'ru') => {
    const formData = new FormData()
    formData.append('audio_file', audioFile)
    formData.append('language', language)
    return apiClient.post('/ai/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  uploadVoice: (memorialId, file, voiceName) => {
    const formData = new FormData()
    formData.append('audio_file', file)
    if (voiceName) {
      formData.append('voice_name', voiceName)
    }
    return apiClient.post(`/ai/voice/upload?memorial_id=${memorialId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const mediaAPI = {
  get: (mediaId, thumbnail = null) => {
    const params = thumbnail ? { thumbnail } : {}
    return apiClient.get(`/media/${mediaId}`, { params, responseType: 'blob' })
  },
  getInfo: (mediaId) => apiClient.get(`/media/${mediaId}/info`),
}

export const embeddingsAPI = {
  recreateMemory: (memoryId) =>
    apiClient.post(`/embeddings/memories/${memoryId}/recreate`),
  recreateAll: (memorialId) =>
    apiClient.post(`/embeddings/memorials/${memorialId}/recreate-all`),
  getStatus: (memorialId) =>
    apiClient.get(`/embeddings/memorials/${memorialId}/status`),
}

export const familyAPI = {
  createRelationship: (memorialId, data) =>
    apiClient.post(`/family/memorials/${memorialId}/relationships`, data),
  getRelationships: (memorialId, relationshipType = null) => {
    const params = relationshipType ? { relationship_type: relationshipType } : {}
    return apiClient.get(`/family/memorials/${memorialId}/relationships`, { params })
  },
  deleteRelationship: (relationshipId) =>
    apiClient.delete(`/family/relationships/${relationshipId}`),
  getFamilyTree: (memorialId, maxDepth = 3) =>
    apiClient.get(`/family/memorials/${memorialId}/tree`, { params: { max_depth: maxDepth } }),
}

