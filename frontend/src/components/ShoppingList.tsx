import { useState } from 'react'
import type { ShoppingListItem } from '../types/recipe'

function formatItem(item: ShoppingListItem): string {
  if (item.quantity && item.unit) {
    return `${item.quantity} ${item.unit} ${item.name}`
  }
  return item.raw_text
}

export function ShoppingList({ items }: { items: ShoppingListItem[] }) {
  const [checked, setChecked] = useState<Set<string>>(new Set())

  function toggle(name: string) {
    setChecked((previous) => {
      const next = new Set(previous)
      if (next.has(name)) {
        next.delete(name)
      } else {
        next.add(name)
      }
      return next
    })
  }

  if (items.length === 0) {
    return <p>No ingredients yet.</p>
  }

  return (
    <ul className="shopping-list">
      {items.map((item) => (
        <li key={item.name}>
          <label>
            <input
              type="checkbox"
              checked={checked.has(item.name)}
              onChange={() => toggle(item.name)}
            />
            <span
              style={checked.has(item.name) ? { textDecoration: 'line-through' } : undefined}
            >
              {formatItem(item)}
            </span>
          </label>
        </li>
      ))}
    </ul>
  )
}
