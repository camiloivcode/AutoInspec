import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import GenerarPDF from './pages/GenerarPDF'
import History from './pages/History'
import NotFound from './pages/NotFound'
import { useAppStore } from './store/useAppStore'

export default function App() {
  const darkMode = useAppStore((s) => s.darkMode)

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<GenerarPDF />} />
        <Route path="/history" element={<History />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
