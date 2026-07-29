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
      className={`fixed left-0 top-0 h-full bg-slate-900 dark:bg-slate-950 text-white transition-all duration-300 z-50 flex flex-col
        ${sidebarOpen ? 'w-64' : 'w-[72px]'}`}
    >
      <div className="flex items-center h-16 px-4 border-b border-slate-800">
        {sidebarOpen && (
          <div className="flex items-center gap-2.5 flex-1 min-w-0">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center text-[11px] font-bold shrink-0">
              AI
            </div>
            <span className="font-display text-sm font-semibold truncate">AutoInspec</span>
          </div>
        )}
        <button
          onClick={() => toggle(!sidebarOpen)}
          className={`p-1.5 rounded-lg hover:bg-slate-800 transition-colors ${sidebarOpen ? '' : 'mx-auto'}`}
        >
          <ChevronLeft className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${!sidebarOpen ? 'rotate-180' : ''}`} />
        </button>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 text-sm font-medium group
              ${isActive
                ? 'bg-primary-600/20 text-primary-300 border-l-2 border-primary-500'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border-l-2 border-transparent'
              }`
            }
          >
            <item.icon className="w-5 h-5 shrink-0" />
            {sidebarOpen && <span>{item.label}</span>}
            {!sidebarOpen && (
              <div className="absolute left-[72px] bg-slate-800 text-slate-200 text-xs px-2.5 py-1 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
                {item.label}
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-slate-800">
        <button
          onClick={toggleDarkMode}
          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl transition-all duration-200 text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 ${!sidebarOpen ? 'justify-center' : ''}`}
        >
          {darkMode ? <Sun className="w-5 h-5 shrink-0" /> : <Moon className="w-5 h-5 shrink-0" />}
          {sidebarOpen && <span>{darkMode ? 'Modo claro' : 'Modo oscuro'}</span>}
        </button>
      </div>
    </aside>
  )
}
