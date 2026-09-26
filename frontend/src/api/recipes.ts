import { apiClient } from './client'
import type {
  Recipe,
  RecipeListVisibilityFilter,
  RecipeUpdate,
  ShoppingListItem,
} from '../types/recipe'

export interface ListRecipesParams {
  visibility?: RecipeListVisibilityFilter
  tag?: string
  status?: string
}

function buildQuery(params: ListRecipesParams): string {
  const search = new URLSearchParams()
  if (params.visibility) search.set('visibility', params.visibility)
  if (params.tag) search.set('tag', params.tag)
  if (params.status) search.set('status', params.status)
  const query = search.toString()
  return query ? `?${query}` : ''
}

export const recipesApi = {
  list: (params: ListRecipesParams = {}) =>
    apiClient.get<Recipe[]>(`/api/v1/recipes${buildQuery(params)}`),
  get: (id: string) => apiClient.get<Recipe>(`/api/v1/recipes/${id}`),
  update: (id: string, data: RecipeUpdate) =>
    apiClient.patch<Recipe>(`/api/v1/recipes/${id}`, data),
  delete: (id: string) => apiClient.delete<void>(`/api/v1/recipes/${id}`),
  setVisibility: (id: string, visibility: 'personal' | 'household') =>
    apiClient.patch<Recipe>(`/api/v1/recipes/${id}/visibility`, { visibility }),
  shoppingList: (id: string) =>
    apiClient.get<ShoppingListItem[]>(`/api/v1/recipes/${id}/shopping-list`),
}
