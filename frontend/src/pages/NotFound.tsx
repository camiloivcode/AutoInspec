import { useNavigate } from 'react-router-dom'
import { FileQuestion, ArrowLeft } from 'lucide-react'

export default function NotFound() {
  const navigate = useNavigate()
  return (
    <div className="flex items-center justify-center h-full px-6">
      <div className="glass-card p-12 text-center max-w-md animate-scale-in">
        <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
          <FileQuestion className="w-10 h-10 text-slate-300 dark:text-slate-600" />
        </div>
        <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">404</h1>
        <p className="text-slate-500 dark:text-slate-400 mb-8">Esta página no existe</p>
        <button onClick={() => navigate('/')} className="btn-primary">
          <ArrowLeft className="w-4 h-4" /> Volver al inicio
        </button>
      </div>
    </div>
  )
}
