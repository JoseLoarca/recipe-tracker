import { apiClient } from './client'

export const tagsApi = {
  list: () => apiClient.get<string[]>('/api/v1/tags'),
}
