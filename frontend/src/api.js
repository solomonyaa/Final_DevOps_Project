import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const username = localStorage.getItem('username')
  const password = localStorage.getItem('password')
  if (username && password) config.auth = { username, password }
  return config
})

export default api
