import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ShoppingList } from '../../src/components/ShoppingList'
import type { ShoppingListItem } from '../../src/types/recipe'

const items: ShoppingListItem[] = [
  { name: 'chicken breast', quantity: 2, unit: 'lbs', raw_text: '2lbs chicken breast' },
  { name: 'quinoa', quantity: 1, unit: 'cup', raw_text: '1 cup quinoa' },
]

describe('ShoppingList', () => {
  it('renders one checklist item per ingredient', () => {
    render(<ShoppingList items={items} />)
    expect(screen.getAllByRole('checkbox')).toHaveLength(2)
    expect(screen.getByText('2 lbs chicken breast')).toBeInTheDocument()
    expect(screen.getByText('1 cup quinoa')).toBeInTheDocument()
  })

  it('renders a fallback message when there are no items', () => {
    render(<ShoppingList items={[]} />)
    expect(screen.getByText('No ingredients yet.')).toBeInTheDocument()
  })

  it('toggles an item checked state on click', () => {
    render(<ShoppingList items={items} />)
    const checkbox = screen.getAllByRole('checkbox')[0]

    expect(checkbox).not.toBeChecked()
    fireEvent.click(checkbox)
    expect(checkbox).toBeChecked()
    fireEvent.click(checkbox)
    expect(checkbox).not.toBeChecked()
  })
})
