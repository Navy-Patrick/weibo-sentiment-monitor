import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 获取看板统计
export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats')
  return response.data
}

// 获取明星列表
export const getStars = async () => {
  const response = await api.get('/stars')
  return response.data
}

// 获取帖子列表
export const getPosts = async (starId?: number) => {
  const response = await api.get('/posts', { params: { star_id: starId } })
  return response.data
}

// 获取帖子评论
export const getComments = async (postId: string) => {
  const response = await api.get(`/posts/${postId}/comments`)
  return response.data
}

// 数据采集配置
export const getCollectionConfig = async () => {
  const response = await api.get('/collection/config')
  return response.data
}

// 开始采集
export const startCollection = async (config: {
  weibo_uid: string
  cookie: string
  posts_count: number
  comments_per_post: number
}) => {
  const response = await api.post('/collection/start', config)
  return response.data
}

// 获取采集状态
export const getCollectionStatus = async () => {
  const response = await api.get('/collection/status')
  return response.data
}

// 获取预警列表
export const getAlerts = async () => {
  const response = await api.get('/alerts')
  return response.data
}

// 处理预警
export const handleAlert = async (alertId: string) => {
  const response = await api.post(`/alerts/${alertId}/handle`)
  return response.data
}

export default api