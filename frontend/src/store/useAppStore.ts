import { create } from 'zustand'

interface AppState {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  darkMode: boolean
  toggleDarkMode: () => void
}

function getInitialDarkMode(): boolean {
  try {
    const stored = localStorage.getItem('darkMode')
    if (stored !== null) return stored === 'true'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  } catch {
    return false
  }
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  darkMode: getInitialDarkMode(),
  toggleDarkMode: () =>
    set((state) => {
      const next = !state.darkMode
      try {
        localStorage.setItem('darkMode', String(next))
      } catch {
        // localStorage may be unavailable (private mode, disabled) — theme still applies to the DOM.
      }
      if (next) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
      return { darkMode: next }
    }),
}))
