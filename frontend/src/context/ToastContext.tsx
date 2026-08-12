import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'

type ToastType = 'success' | 'error' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
}

interface ToastContextValue {
  toast: (type: ToastType, message: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

const icons = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
}

// Signage code: green guides, yellow warns, red prohibits — carried by the
// left bar + icon on a neutral surface, not a full-bleed color fill.
const styles = {
  success: 'border-l-signal-500 text-signal-700 dark:text-signal-300',
  error: 'border-l-stop-500 text-stop-600 dark:text-stop-300',
  info: 'border-l-plate-500 text-plate-700 dark:text-plate-300',
}
const iconStyles = {
  success: 'text-signal-500',
  error: 'text-stop-500',
  info: 'text-plate-500',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((type: ToastType, message: string) => {
    const id = crypto.randomUUID()
    setToasts((prev) => [...prev, { id, type, message }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  function remove(id: string) {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-20 md:bottom-6 right-4 md:right-6 z-[200] flex flex-col gap-3 pointer-events-none">
        {toasts.map((t) => {
          const Icon = icons[t.type]
          return (
            <div
              key={t.id}
              role={t.type === 'error' ? 'alert' : 'status'}
              className={`pointer-events-auto flex animate-slide-up items-start gap-3 rounded-plate border border-border border-l-4 bg-surface px-4 py-3 shadow-lg shadow-black/10 ${styles[t.type]}`}
            >
              <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${iconStyles[t.type]}`} />
              <p className="text-sm font-medium flex-1 min-w-[200px] max-w-sm text-fg">{t.message}</p>
              <button
                onClick={() => remove(t.id)}
                aria-label="Cerrar notificación"
                className="p-0.5 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
