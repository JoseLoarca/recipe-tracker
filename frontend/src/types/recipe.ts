export type RecipeVisibility = 'personal' | 'household'
export type RecipeStatus = 'pending' | 'processing' | 'complete' | 'failed'
export type MacroSource = 'usda_verified' | 'llm_estimated' | 'mixed'

export interface Step {
  step_number: number
  text: string
}

export interface Ingredient {
  id: string
  raw_text: string
  name: string
  quantity: number | null
  unit: string | null
  calories: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  macro_source: MacroSource
  sort_order: number
}

export interface IngredientWrite {
  raw_text: string
  name: string
  quantity?: number | null
  unit?: string | null
  calories?: number | null
  protein_g?: number | null
  carbs_g?: number | null
  fat_g?: number | null
  macro_source: MacroSource
}

export interface RecipeMacros {
  portion_count: number
  calories_per_portion: number
  protein_g_per_portion: number
  carbs_g_per_portion: number
  fat_g_per_portion: number
  macro_source: MacroSource
}

export interface Recipe {
  id: string
  owner_user_id: string
  household_id: string | null
  visibility: RecipeVisibility
  name: string
  source_url: string
  status: RecipeStatus
  failure_reason: string | null
  created_at: string
  updated_at: string
  steps: Step[]
  ingredients: Ingredient[]
  macros: RecipeMacros | null
  tags: string[]
}

export interface RecipeUpdate {
  name?: string
  portion_count?: number
  steps?: string[]
  ingredients?: IngredientWrite[]
  tags?: string[]
}

export interface ShoppingListItem {
  name: string
  quantity: number | null
  unit: string | null
  raw_text: string
}

export type RecipeListVisibilityFilter = 'mine' | 'household' | 'all'
