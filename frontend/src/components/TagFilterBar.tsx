import { useEffect, useState } from 'react'
import { tagsApi } from '../api/tags'
import type { RecipeListVisibilityFilter } from '../types/recipe'

interface TagFilterBarProps {
  visibility: RecipeListVisibilityFilter
  onVisibilityChange: (visibility: RecipeListVisibilityFilter) => void
  tag: string | null
  onTagChange: (tag: string | null) => void
}

export function TagFilterBar({
  visibility,
  onVisibilityChange,
  tag,
  onTagChange,
}: TagFilterBarProps) {
  const [tags, setTags] = useState<string[]>([])

  useEffect(() => {
    tagsApi.list().then(setTags).catch(() => setTags([]))
  }, [])

  return (
    <div className="tag-filter-bar">
      <div role="group" aria-label="Visibility filter">
        {(['all', 'mine', 'household'] as const).map((option) => (
          <button
            key={option}
            type="button"
            aria-pressed={visibility === option}
            onClick={() => onVisibilityChange(option)}
          >
            {option}
          </button>
        ))}
      </div>
      <select
        aria-label="Filter by tag"
        value={tag ?? ''}
        onChange={(event) => onTagChange(event.target.value || null)}
      >
        <option value="">All tags</option>
        {tags.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    </div>
  )
}
