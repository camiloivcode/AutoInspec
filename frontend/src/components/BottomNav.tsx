import { NavLink } from 'react-router-dom'
import { FileText, History } from 'lucide-react'

const navItems = [
  { to: '/', icon: FileText, label: 'Generar PDF' },
  { to: '/history', icon: History, label: 'Historial' },
]

export default function BottomNav() {
  return (
    <nav
      aria-label="Navegación principal"
      className="fixed bottom-0 left-0 right-0 z-30 border-t-2 border-border-strong bg-surface pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      <div className="flex">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              `relative flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-bold uppercase tracking-[0.06em] transition-colors ${
                isActive ? 'text-signal-600 dark:text-signal-300' : 'text-fg-subtle'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <span className="absolute inset-x-4 top-0 h-1 rounded-full bg-signal-500" aria-hidden="true" />}
                <item.icon className="h-5 w-5" />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
