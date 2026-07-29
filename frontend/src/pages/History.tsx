import { useState, useEffect, useCallback } from 'react'
import { Download, Trash2, FileText, AlertCircle, Search, Clock, FileDown } from 'lucide-react'
import { useToast } from '../context/ToastContext'

interface HistoryRecord {
  id: string
  driver_name: string
  plate: string
  filename: string
  file_size: number
  created_at: string
}

function formatRelativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'ahora mismo'
  if (mins < 60) return `hace ${mins} min`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `hace ${hours}h`
  const days = Math.floor(hours / 24)
  if (days < 7) return `hace ${days}d`
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function SkeletonCard() {
  return (
    <div className="glass-card p-4 flex items-center gap-4 animate-pulse">
      <div className="w-11 h-11 rounded-xl bg-slate-200 dark:bg-slate-700 shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
        <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/4" />
      </div>
      <div className="flex gap-1">
        <div className="w-9 h-9 rounded-xl bg-slate-200 dark:bg-slate-700" />
        <div className="w-9 h-9 rounded-xl bg-slate-200 dark:bg-slate-700" />
      </div>
    </div>
  )
}

export default function History() {
  const [records, setRecords] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const { toast } = useToast()

  const fetchHistory = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const res = await fetch('/api/history')
      if (!res.ok) throw new Error('Error al cargar historial')
      setRecords(await res.json())
    } catch (err: any) {
      setError(err.message || 'Error de conexión')
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  async function handleDelete(id: string) {
    try {
      const res = await fetch(`/api/history/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Error al eliminar')
      setRecords((prev) => prev.filter((r) => r.id !== id))
      toast('success', 'Documento eliminado')
    } catch (err: any) {
      toast('error', err.message)
    }
  }

  const filtered = records.filter(
    (r) =>
      r.driver_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.plate.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6 animate-fade-in">
        <div>
          <div className="h-7 bg-slate-200 dark:bg-slate-700 rounded w-24 mb-2 animate-pulse" />
          <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-48 animate-pulse" />
        </div>
        <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded-xl w-72 animate-pulse" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="font-display text-xl font-semibold text-slate-900 dark:text-slate-100">Historial</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Documentos generados anteriormente</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800/50 flex items-start gap-3 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-500 mt-0.5 shrink-0" />
          <p className="text-sm text-rose-700 dark:text-rose-300">{error}</p>
        </div>
      )}

      <div className="relative max-w-sm">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar por conductor o placa..."
          className="input-field pl-10"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
            <FileText className="w-8 h-8 text-slate-300 dark:text-slate-600" />
          </div>
          <p className="font-display text-base font-semibold text-slate-600 dark:text-slate-400">
            {searchTerm ? 'Sin resultados' : 'No hay PDFs generados aún'}
          </p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
            {searchTerm ? 'Intente con otro término de búsqueda' : 'Genere su primer PDF desde la sección Generar PDF'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((record, i) => (
            <div
              key={record.id}
              className="glass-card p-4 flex items-center gap-4 hover:shadow-lg transition-all duration-200 animate-slide-up group"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center shrink-0 shadow-lg shadow-primary-500/20">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-medium text-slate-900 dark:text-slate-100 truncate">{record.driver_name}</p>
                  <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                    {record.plate}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400 dark:text-slate-500 mt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatRelativeTime(record.created_at)}
                  </span>
                  <span>{formatSize(record.file_size)}</span>
                </div>
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <a
                  href={`/api/history/download/${record.filename}`}
                  download
                  className="p-2.5 rounded-xl text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                  title="Descargar"
                >
                  <Download className="w-4 h-4" />
                </a>
                <button
                  onClick={() => handleDelete(record.id)}
                  className="p-2.5 rounded-xl text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-colors"
                  title="Eliminar"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="text-center">
        <button onClick={fetchHistory} className="btn-ghost text-sm">
          <FileDown className="w-4 h-4" /> Actualizar lista
        </button>
      </div>
    </div>
  )
}
