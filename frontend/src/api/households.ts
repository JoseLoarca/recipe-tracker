import { apiClient } from './client'
import type { HouseholdMe } from '../types/auth'

export const householdsApi = {
  me: () => apiClient.get<HouseholdMe>('/api/v1/households/me'),
}
