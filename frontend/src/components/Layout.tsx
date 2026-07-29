import { useLocation } from 'react-router-dom'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import { ToastProvider } from '../context/ToastContext'
import { useAppStore } from '../store/useAppStore'
import { useEffect, useRef, useState, type ReactNode } from 'react'

function PageTransition({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [displayChildren, setDisplayChildren] = useState(children)
  const [transitionStage, setTransitionStage] = useState('enter')
  const prevPath = useRef(location.pathname)

  useEffect(() => {
    if (location.pathname !== prevPath.current) {
      setTransitionStage('exit')
      prevPath.current = location.pathname
      setTimeout(() => {
        setDisplayChildren(children)
        setTransitionStage('enter')
      }, 200)
    } else {
      setDisplayChildren(children)
    }
  }, [children, location.pathname])

  return (
    <div
      className={`transition-all duration-200 ${
        transitionStage === 'enter' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'
      }`}
    >
      {displayChildren}
    </div>
  )
}

export default function Layout() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)

  return (
    <ToastProvider>
      <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-300">
        <Sidebar />
        <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-[72px]'}`}>
          <Header />
          <main className="flex-1 overflow-y-auto">
            <PageTransition>
              <Outlet />
            </PageTransition>
          </main>
        </div>
      </div>
    </ToastProvider>
  )
}
