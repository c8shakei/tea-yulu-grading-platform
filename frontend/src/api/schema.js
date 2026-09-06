import request, { unwrap } from '../utils/request'

export function getSchema() {
  return request.get('/api/ui/schema').then(unwrap)
}
