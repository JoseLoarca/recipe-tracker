import type { RecipeVisibility } from '../types/recipe'

interface VisibilityToggleProps {
  visibility: RecipeVisibility
  isOwner: boolean
  onChange: (visibility: RecipeVisibility) => void
  disabled?: boolean
}

export function VisibilityToggle({
  visibility,
  isOwner,
  onChange,
  disabled,
}: VisibilityToggleProps) {
  if (!isOwner) {
    return <span className="visibility-toggle visibility-toggle--readonly">{visibility}</span>
  }

  return (
    <select
      aria-label="Recipe visibility"
      value={visibility}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value as RecipeVisibility)}
    >
      <option value="personal">Personal</option>
      <option value="household">Household</option>
    </select>
  )
}
