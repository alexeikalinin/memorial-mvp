import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

/** URL для отображения медиа (картинки/видео). Учитывает VITE_API_URL для продакшена (Vercel + отдельный backend). */
export const getMediaUrl = (mediaId, thumbnail = null) => {
  if (!mediaId) return ''
  const base = API_BASE_URL
  return thumbnail ? `${base}/media/${mediaId}?thumbnail=${thumbnail}` : `${base}/media/${mediaId}`
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Добавляем Bearer token к каждому запросу
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
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

export const authAPI = {
  register: (data) => apiClient.post('/auth/register', data),
  login:    (data) => apiClient.post('/auth/login', data),
  me:       ()     => apiClient.get('/auth/me'),
}

// API методы
export const memorialsAPI = {
  list: (language = null) => apiClient.get('/memorials/', language ? { params: { language } } : {}),
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
  createMemory: (memorialId, data, inviteToken = null) =>
    apiClient.post(
      `/memorials/${memorialId}/memories`,
      data,
      inviteToken ? { params: { invite_token: inviteToken } } : {}
    ),
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

export const invitesAPI = {
  create: (memorialId, data) =>
    apiClient.post(`/invites/memorials/${memorialId}/create`, data),
  list: (memorialId) =>
    apiClient.get(`/invites/memorials/${memorialId}/list`),
  validate: (token) =>
    apiClient.get(`/invites/validate/${token}`),
  revoke: (token) =>
    apiClient.delete(`/invites/${token}`),
}

export const accessAPI = {
  list:           (memorialId) =>
    apiClient.get(`/memorials/${memorialId}/access`),
  grant:          (memorialId, data) =>
    apiClient.post(`/memorials/${memorialId}/access`, data),
  update:         (memorialId, userId, data) =>
    apiClient.patch(`/memorials/${memorialId}/access/${userId}`, data),
  revoke:         (memorialId, userId) =>
    apiClient.delete(`/memorials/${memorialId}/access/${userId}`),
  requestAccess:  (memorialId, data) =>
    apiClient.post(`/memorials/${memorialId}/access/request`, data),
  listRequests:   (memorialId) =>
    apiClient.get(`/memorials/${memorialId}/access/requests`),
  approveRequest: (memorialId, requestId) =>
    apiClient.post(`/memorials/${memorialId}/access/requests/${requestId}/approve`),
  rejectRequest:  (memorialId, requestId) =>
    apiClient.post(`/memorials/${memorialId}/access/requests/${requestId}/reject`),
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
  getFullTree: (memorialId, maxDepth = 6) =>
    apiClient.get(`/family/memorials/${memorialId}/full-tree`, { params: { max_depth: maxDepth } }),
  getHiddenConnections: (memorialId, maxDepth = 6) =>
    apiClient.get(`/family/memorials/${memorialId}/hidden-connections`, { params: { max_depth: maxDepth } }),
  getNetworkClusters: (memorialId) =>
    apiClient.get(`/family/memorials/${memorialId}/network-clusters`),
}

