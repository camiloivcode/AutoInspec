import { useLocation } from 'react-router-dom'
import { Sun, Moon } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { useSystemStatus } from '../hooks/useSystemStatus'

const pageTitles: Record<string, string> = {
  '/': 'Generar PDF',
  '/history': 'Historial',
}

export default function Header() {
  const location = useLocation()
  const darkMode = useAppStore((s) => s.darkMode)
  const toggleDarkMode = useAppStore((s) => s.toggleDarkMode)
  const { online } = useSystemStatus()
  const title = pageTitles[location.pathname] || 'AutoInspec'

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b-2 border-border-strong bg-surface px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <span className="hidden h-8 w-1.5 shrink-0 rounded-full bg-signal-500 md:block" aria-hidden="true" />
        <div className="min-w-0">
          <h1 className="truncate font-display text-base font-bold uppercase tracking-[0.06em] text-fg">{title}</h1>
          <p className="hidden text-[11px] uppercase tracking-[0.1em] text-fg-subtle sm:block">
            Inspección vehicular
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleDarkMode}
          aria-label={darkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
          aria-pressed={darkMode}
          className="rounded-chip p-2 text-fg-muted transition-colors hover:bg-bg-subtle"
        >
          {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
        <div
          className="hidden items-center gap-2 rounded-chip border border-border-strong px-2.5 py-1.5 sm:flex"
          role="status"
          aria-label={online ? 'Sistema conectado' : 'Sistema sin conexión'}
        >
          <span className={`h-2 w-2 rounded-full ${online ? 'bg-signal-500' : 'bg-stop-500'}`} />
          <span className="font-mono text-[11px] font-bold uppercase tracking-[0.08em] text-fg-muted">
            {online ? 'En línea' : 'Sin conexión'}
          </span>
        </div>
      </div>
    </header>
  )
}
