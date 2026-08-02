import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MacroBadge } from '../../src/components/MacroBadge'

describe('MacroBadge', () => {
  it('renders "Verified" for usda_verified', () => {
    render(<MacroBadge source="usda_verified" />)
    expect(screen.getByText('Verified')).toBeInTheDocument()
  })

  it('renders "Estimated" for llm_estimated', () => {
    render(<MacroBadge source="llm_estimated" />)
    expect(screen.getByText('Estimated')).toBeInTheDocument()
  })

  it('renders "Mixed" for mixed', () => {
    render(<MacroBadge source="mixed" />)
    expect(screen.getByText('Mixed')).toBeInTheDocument()
  })

  it('applies a source-specific class', () => {
    render(<MacroBadge source="llm_estimated" />)
    expect(screen.getByText('Estimated')).toHaveClass('macro-badge--llm_estimated')
  })
})
