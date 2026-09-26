import { useEffect, useState } from 'react'
import { recipesApi } from '../api/recipes'
import { RecipeCard } from '../components/RecipeCard'
import { TagFilterBar } from '../components/TagFilterBar'
import { useAuth } from '../context/auth-context'
import type { Recipe, RecipeListVisibilityFilter } from '../types/recipe'

export function RecipeListPage() {
  const { logout } = useAuth()
  const [visibility, setVisibility] = useState<RecipeListVisibilityFilter>('all')
  const [tag, setTag] = useState<string | null>(null)
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    recipesApi
      .list({ visibility, tag: tag ?? undefined })
      .then(setRecipes)
      .catch(() => setError('Could not load recipes.'))
      .finally(() => setLoading(false))
  }, [visibility, tag])

  return (
    <main className="recipe-list-page">
      <header>
        <h1>Recipe Tracker</h1>
        <button type="button" onClick={() => void logout()}>
          Log out
        </button>
      </header>
      <TagFilterBar
        visibility={visibility}
        onVisibilityChange={setVisibility}
        tag={tag}
        onTagChange={setTag}
      />
      {loading && <p>Loading…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && recipes.length === 0 && <p>No recipes yet.</p>}
      <div className="recipe-list-page__grid">
        {recipes.map((recipe) => (
          <RecipeCard key={recipe.id} recipe={recipe} />
        ))}
      </div>
    </main>
  )
}
