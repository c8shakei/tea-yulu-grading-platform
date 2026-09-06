import request, { unwrap } from '../utils/request'

export function register(data) {
  return request.post('/api/auth/register', data).then(unwrap)
}

export function login(data) {
  return request.post('/api/auth/login', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }).then(unwrap)
}

export function getMe() {
  return request.get('/api/auth/me').then(unwrap)
}

export function logout() {
  return request.post('/api/auth/logout').then(unwrap)
}
