import { useLocation } from 'react-router-dom'
import { Menu, Sun, Moon } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'

const pageTitles: Record<string, string> = {
  '/': 'Generar PDF',
  '/history': 'Historial',
}

export default function Header() {
  const location = useLocation()
  const setSidebarOpen = useAppStore((s) => s.setSidebarOpen)
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)
  const darkMode = useAppStore((s) => s.darkMode)
  const toggleDarkMode = useAppStore((s) => s.toggleDarkMode)
  const title = pageTitles[location.pathname] || 'AutoInspec'

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 -ml-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <Menu className="w-5 h-5 text-slate-500 dark:text-slate-400" />
        </button>
        <div>
          <h1 className="font-display text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h1>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 hidden sm:block">AutoInspec · Generación de PDF</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title={darkMode ? 'Modo claro' : 'Modo oscuro'}
        >
          {darkMode ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-500" />
          )}
        </button>
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-medium text-emerald-700 dark:text-emerald-300">Sistema activo</span>
        </div>
      </div>
    </header>
  )
}
