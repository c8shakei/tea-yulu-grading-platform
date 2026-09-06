import request, { unwrap } from '../utils/request'

export function getTrace(id) {
  return request.get(`/api/trace/${id}`).then(unwrap)
}

export function appendTrace(traceId, payload) {
  return request.post('/api/trace', { trace_id: traceId, payload }).then(unwrap)
}
