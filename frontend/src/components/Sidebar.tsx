import { NavLink } from 'react-router-dom'
import { FileText, History, ChevronLeft, Moon, Sun } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'

const navItems = [
  { to: '/', icon: FileText, label: 'Generar PDF' },
  { to: '/history', icon: History, label: 'Historial' },
]

export default function Sidebar() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)
  const toggle = useAppStore((s) => s.setSidebarOpen)
  const darkMode = useAppStore((s) => s.darkMode)
  const toggleDarkMode = useAppStore((s) => s.toggleDarkMode)

  return (
    <aside
      className={`fixed left-0 top-0 z-30 hidden h-full flex-col bg-neutral-900 text-neutral-100 transition-all duration-300 md:flex
        ${sidebarOpen ? 'w-64' : 'w-[72px]'}`}
    >
      <div className="flex h-16 items-center border-b border-white/10 px-4">
        {sidebarOpen && (
          <div className="flex min-w-0 flex-1 items-center gap-2.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-chip bg-signal-500 text-[11px] font-bold text-white">
              AI
            </div>
            <span className="truncate font-display text-sm font-bold uppercase tracking-[0.08em]">AutoInspec</span>
          </div>
        )}
        <button
          onClick={() => toggle(!sidebarOpen)}
          aria-label={sidebarOpen ? 'Contraer menú lateral' : 'Expandir menú lateral'}
          aria-pressed={!sidebarOpen}
          className={`rounded-chip p-1.5 transition-colors hover:bg-white/10 ${sidebarOpen ? '' : 'mx-auto'}`}
        >
          <ChevronLeft className={`h-4 w-4 transition-transform duration-300 ${!sidebarOpen ? 'rotate-180' : ''}`} />
        </button>
      </div>

      <nav className="flex-1 p-3 space-y-1" aria-label="Navegación principal">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            title={!sidebarOpen ? item.label : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-plate px-3 py-2.5 text-sm font-bold uppercase tracking-[0.06em] transition-colors duration-150
              ${isActive ? 'bg-signal-500 text-white' : 'text-white/60 hover:bg-white/10 hover:text-white'}`
            }
          >
            <item.icon className="w-5 h-5 shrink-0" />
            {sidebarOpen && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 p-3">
        <button
          onClick={toggleDarkMode}
          aria-pressed={darkMode}
          className={`flex w-full items-center gap-3 rounded-plate px-3 py-2.5 text-sm font-bold uppercase tracking-[0.06em] text-white/60 transition-colors duration-150 hover:bg-white/10 hover:text-white ${!sidebarOpen ? 'justify-center' : ''}`}
        >
          {darkMode ? <Sun className="h-5 w-5 shrink-0" /> : <Moon className="h-5 w-5 shrink-0" />}
          {sidebarOpen && <span>{darkMode ? 'Modo claro' : 'Modo oscuro'}</span>}
        </button>
      </div>
    </aside>
  )
}
