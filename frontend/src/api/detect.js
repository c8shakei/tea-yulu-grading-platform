import request, { unwrap } from '../utils/request'

export function detectImage(file) {
  const form = new FormData()
  form.append('image', file)
  return request.post('/api/detect', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(unwrap)
}

export function getDetections() {
  return request.get('/api/detections').then(unwrap)
}
