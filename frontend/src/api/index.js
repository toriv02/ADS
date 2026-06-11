import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

// Перехватчик для добавления JWT токена
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Перехватчик для обновления токена при 401
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const res = await axios.post('/api/token/refresh/', { refresh })
          localStorage.setItem('access_token', res.data.access)
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`
          return api(originalRequest)
        } catch (err) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// API для аутентификации
export const authApi = {
  login(username, password) {
    return api.post('/token/', { username, password })
  }
}

// API для задач
export const taskApi = {
  list(params) {
    return api.get('/tasks/', { params })
  },
  create(formData) {
    return api.post('/tasks/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  get(id) {
    return api.get(`/tasks/${id}/`)
  },
  getSolution(id) {
    return api.get(`/tasks/${id}/solution/`)
  },
  updateObjects(id, objects) {
    return api.post(`/tasks/${id}/update_objects/`, { objects })
  },
  exportGeoJSON(id) {
    return api.post(`/tasks/${id}/export_geojson/`)
  }
}

// API для пользователей
export const userApi = {
  getCurrent() {
    return api.get('/users/employees/me/')
  }
}

export default api