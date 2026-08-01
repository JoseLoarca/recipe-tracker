import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { recipesApi } from '../api/recipes'
import { ApiError } from '../api/client'
import { MacroBadge } from '../components/MacroBadge'
import { ShoppingList } from '../components/ShoppingList'
import { VisibilityToggle } from '../components/VisibilityToggle'
import { useAuth } from '../context/auth-context'
import type { Recipe, RecipeVisibility, ShoppingListItem } from '../types/recipe'

export function RecipeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)
    Promise.all([recipesApi.get(id), recipesApi.shoppingList(id)])
      .then(([fetchedRecipe, items]) => {
        setRecipe(fetchedRecipe)
        setShoppingList(items)
      })
      .catch((err) => {
        setError(err instanceof ApiError && err.status === 404 ? 'Recipe not found.' : 'Could not load recipe.')
      })
      .finally(() => setLoading(false))
  }, [id])

  async function handleVisibilityChange(visibility: RecipeVisibility) {
    if (!id) return
    const updated = await recipesApi.setVisibility(id, visibility)
    setRecipe(updated)
  }

  async function handleDelete() {
    if (!id || !window.confirm('Delete this recipe?')) return
    await recipesApi.delete(id)
    navigate('/')
  }

  if (loading) return <p>Loading…</p>
  if (error) return <p role="alert">{error}</p>
  if (!recipe) return null

  const isOwner = user?.id === recipe.owner_user_id

  return (
    <main className="recipe-detail-page">
      <Link to="/">&larr; Back to recipes</Link>
      <h1>{recipe.name}</h1>
      <a href={recipe.source_url} target="_blank" rel="noreferrer">
        View original video
      </a>

      <section className="recipe-detail-page__actions">
        <VisibilityToggle
          visibility={recipe.visibility}
          isOwner={isOwner}
          onChange={handleVisibilityChange}
        />
        {isOwner && (
          <>
            <Link to={`/recipes/${recipe.id}/edit`}>Edit</Link>
            <button type="button" onClick={() => void handleDelete()}>
              Delete
            </button>
          </>
        )}
      </section>

      {recipe.tags.length > 0 && (
        <ul className="recipe-detail-page__tags">
          {recipe.tags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>
      )}

      {recipe.macros && (
        <section>
          <h2>
            Macros per portion <MacroBadge source={recipe.macros.macro_source} />
          </h2>
          <ul>
            <li>{Math.round(recipe.macros.calories_per_portion)} kcal</li>
            <li>{Math.round(recipe.macros.protein_g_per_portion)}g protein</li>
            <li>{Math.round(recipe.macros.carbs_g_per_portion)}g carbs</li>
            <li>{Math.round(recipe.macros.fat_g_per_portion)}g fat</li>
          </ul>
        </section>
      )}

      <section>
        <h2>Steps</h2>
        <ol>
          {recipe.steps.map((step) => (
            <li key={step.step_number}>{step.text}</li>
          ))}
        </ol>
      </section>

      <section>
        <h2>Shopping list</h2>
        <ShoppingList items={shoppingList} />
      </section>
    </main>
  )
}
