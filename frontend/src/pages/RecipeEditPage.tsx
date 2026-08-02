import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router'
import { recipesApi } from '../api/recipes'
import { ApiError } from '../api/client'
import type { IngredientWrite, MacroSource, Recipe } from '../types/recipe'

function ingredientFromRecipe(recipe: Recipe): IngredientWrite[] {
  return recipe.ingredients.map((ingredient) => ({
    raw_text: ingredient.raw_text,
    name: ingredient.name,
    quantity: ingredient.quantity,
    unit: ingredient.unit,
    calories: ingredient.calories,
    protein_g: ingredient.protein_g,
    carbs_g: ingredient.carbs_g,
    fat_g: ingredient.fat_g,
    macro_source: ingredient.macro_source,
  }))
}

const EMPTY_INGREDIENT: IngredientWrite = {
  raw_text: '',
  name: '',
  quantity: null,
  unit: null,
  calories: null,
  protein_g: null,
  carbs_g: null,
  fat_g: null,
  macro_source: 'llm_estimated',
}

export function RecipeEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [name, setName] = useState('')
  const [portionCount, setPortionCount] = useState(1)
  const [stepsText, setStepsText] = useState('')
  const [tagsText, setTagsText] = useState('')
  const [ingredients, setIngredients] = useState<IngredientWrite[]>([])

  useEffect(() => {
    if (!id) return
    recipesApi
      .get(id)
      .then((recipe) => {
        setName(recipe.name)
        setPortionCount(recipe.macros?.portion_count ?? 1)
        setStepsText(recipe.steps.map((step) => step.text).join('\n'))
        setTagsText(recipe.tags.join(', '))
        setIngredients(ingredientFromRecipe(recipe))
      })
      .catch(() => setError('Could not load recipe.'))
      .finally(() => setLoading(false))
  }, [id])

  function updateIngredient(index: number, patch: Partial<IngredientWrite>) {
    setIngredients((previous) =>
      previous.map((ingredient, i) => (i === index ? { ...ingredient, ...patch } : ingredient)),
    )
  }

  function removeIngredient(index: number) {
    setIngredients((previous) => previous.filter((_, i) => i !== index))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!id) return
    setSaving(true)
    setError(null)
    try {
      await recipesApi.update(id, {
        name,
        portion_count: portionCount,
        steps: stepsText
          .split('\n')
          .map((line) => line.trim())
          .filter((line) => line.length > 0),
        tags: tagsText
          .split(',')
          .map((tag) => tag.trim())
          .filter((tag) => tag.length > 0),
        ingredients,
      })
      navigate(`/recipes/${id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save changes.')
      setSaving(false)
    }
  }

  if (loading) return <p>Loading…</p>

  return (
    <main className="recipe-edit-page">
      <h1>Edit recipe</h1>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={handleSubmit}>
        <label htmlFor="name">Name</label>
        <input id="name" value={name} onChange={(event) => setName(event.target.value)} required />

        <label htmlFor="portion-count">Portions</label>
        <input
          id="portion-count"
          type="number"
          min={1}
          value={portionCount}
          onChange={(event) => setPortionCount(Number(event.target.value))}
          required
        />

        <label htmlFor="steps">Steps (one per line)</label>
        <textarea
          id="steps"
          value={stepsText}
          onChange={(event) => setStepsText(event.target.value)}
          rows={6}
        />

        <label htmlFor="tags">Tags (comma-separated)</label>
        <input id="tags" value={tagsText} onChange={(event) => setTagsText(event.target.value)} />

        <fieldset>
          <legend>Ingredients</legend>
          {ingredients.map((ingredient, index) => (
            <div className="recipe-edit-page__ingredient-row" key={index}>
              <input
                aria-label="Ingredient text"
                placeholder="2lbs chicken breast"
                value={ingredient.raw_text}
                onChange={(event) =>
                  updateIngredient(index, {
                    raw_text: event.target.value,
                    name: ingredient.name || event.target.value,
                  })
                }
              />
              <select
                aria-label="Macro source"
                value={ingredient.macro_source}
                onChange={(event) =>
                  updateIngredient(index, {
                    macro_source: event.target.value as MacroSource,
                  })
                }
              >
                <option value="usda_verified">Verified</option>
                <option value="llm_estimated">Estimated</option>
              </select>
              <button type="button" onClick={() => removeIngredient(index)}>
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => setIngredients((previous) => [...previous, { ...EMPTY_INGREDIENT }])}
          >
            Add ingredient
          </button>
        </fieldset>

        <button type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </form>
    </main>
  )
}
