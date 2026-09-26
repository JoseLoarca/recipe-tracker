import { Route, Routes } from 'react-router'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { RecipeDetailPage } from './pages/RecipeDetailPage'
import { RecipeEditPage } from './pages/RecipeEditPage'
import { RecipeListPage } from './pages/RecipeListPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <RecipeListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recipes/:id"
        element={
          <ProtectedRoute>
            <RecipeDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recipes/:id/edit"
        element={
          <ProtectedRoute>
            <RecipeEditPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
