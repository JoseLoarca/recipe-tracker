import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import App from '../../src/App'
import { AuthProvider } from '../../src/context/AuthContext'

describe('App', () => {
  it('renders the login page when not authenticated', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('not authenticated'))

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: /recipe tracker/i })).toBeInTheDocument()
  })
})
