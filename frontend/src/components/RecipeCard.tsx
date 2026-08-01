import { Link } from 'react-router'
import type { Recipe } from '../types/recipe'
import { MacroBadge } from './MacroBadge'

export function RecipeCard({ recipe }: { recipe: Recipe }) {
  return (
    <Link to={`/recipes/${recipe.id}`} className="recipe-card">
      <h3>{recipe.name}</h3>
      <p className="recipe-card__visibility">{recipe.visibility}</p>
      {recipe.macros && (
        <p>
          {Math.round(recipe.macros.calories_per_portion)} kcal/portion{' '}
          <MacroBadge source={recipe.macros.macro_source} />
        </p>
      )}
      {recipe.tags.length > 0 && (
        <ul className="recipe-card__tags">
          {recipe.tags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>
      )}
    </Link>
  )
}
