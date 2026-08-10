import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import BottomNav from './BottomNav'
import { useAppStore } from '../store/useAppStore'

export default function Layout() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-bg text-fg transition-colors duration-300">
      <Sidebar />
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? 'md:ml-64' : 'md:ml-[72px]'}`}>
        <Header />
        <main className="flex-1 overflow-y-auto pb-16 md:pb-0">
          <div key={location.pathname} className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
      <BottomNav />
    </div>
  )
}
