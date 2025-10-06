import axios from 'axios'
import { toast } from 'react-toastify'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const api = axios.create({ baseURL, timeout: 30000 })

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const msg = error?.response?.data?.detail || error?.message || 'Unexpected error'
    toast.error(msg)
    return Promise.reject(error)
  },
)
