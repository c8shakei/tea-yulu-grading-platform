import request, { unwrap } from '../utils/request'

export function getStatsOverview() {
  return request.get('/api/stats/overview').then(unwrap)
}

export function getUserStats(userId) {
  return request.get(`/api/stats/user/${userId}`).then(unwrap)
}
