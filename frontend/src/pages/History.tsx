import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Trash2, FileText, AlertCircle, Search, Clock } from 'lucide-react'
import { useToast } from '../context/ToastContext'
import { Card, CardBody } from '../components/ui/Card'
import Field from '../components/ui/Field'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import EmptyState from '../components/ui/EmptyState'
import { SkeletonCard } from '../components/ui/Skeleton'

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

async function fetchHistory(): Promise<HistoryRecord[]> {
  const res = await fetch('/api/history')
  if (!res.ok) throw new Error('Error al cargar historial')
  return res.json()
}

export default function History() {
  const [searchTerm, setSearchTerm] = useState('')
  const [pendingDelete, setPendingDelete] = useState<HistoryRecord | null>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: records = [], isLoading, isError } = useQuery({
    queryKey: ['history'],
    queryFn: fetchHistory,
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/history/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Error al eliminar')
    },
    onSuccess: (_data, id) => {
      queryClient.setQueryData<HistoryRecord[]>(['history'], (prev) => prev?.filter((r) => r.id !== id) ?? [])
      toast('success', 'Documento eliminado')
    },
    onError: (err: Error) => toast('error', err.message),
    onSettled: () => setPendingDelete(null),
  })

  const filtered = useMemo(
    () =>
      records.filter(
        (r) =>
          r.driver_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          r.plate.toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [records, searchTerm]
  )

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="font-display text-xl font-semibold text-fg">Historial</h1>
        <p className="text-sm text-fg-muted mt-1">Documentos generados anteriormente</p>
      </div>

      {isError && (
        <div className="flex items-start gap-3 rounded-plate border border-stop-200 bg-stop-50 p-4 dark:border-stop-800 dark:bg-stop-900/20">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-stop-500" />
          <p className="text-sm font-semibold text-stop-700 dark:text-stop-200">
            No se pudo cargar el historial. Revise su conexión y recargue la página.
          </p>
        </div>
      )}

      <Field
        label="Buscar"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="Buscar por conductor o placa..."
        icon={<Search className="w-4 h-4" />}
        className="max-w-sm"
      />

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <EmptyState
            icon={FileText}
            title={searchTerm ? 'Sin resultados' : 'No hay PDFs generados aún'}
            description={searchTerm ? 'Intente con otro término de búsqueda' : 'Genere su primer PDF desde la sección Generar PDF'}
          />
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((record) => (
            <Card key={record.id} className="transition-colors duration-150 hover:border-signal-500">
              <CardBody className="flex items-center gap-4 pb-4 pt-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-plate bg-signal-50 dark:bg-signal-900/20">
                  <FileText className="h-5 w-5 text-signal-600 dark:text-signal-300" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate font-bold text-fg">{record.driver_name}</p>
                    <span className="plate-chip">{record.plate}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-3 font-mono text-xs text-fg-muted">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatRelativeTime(record.created_at)}
                    </span>
                    <span>{formatSize(record.file_size)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <a
                    href={`/api/history/download/${record.filename}`}
                    download
                    aria-label={`Descargar PDF de ${record.driver_name}`}
                    className="rounded-chip p-2.5 text-signal-600 transition-colors hover:bg-signal-500 hover:text-white dark:text-signal-300"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                  <button
                    onClick={() => setPendingDelete(record)}
                    aria-label={`Eliminar PDF de ${record.driver_name}`}
                    className="rounded-chip p-2.5 text-fg-subtle transition-colors hover:bg-stop-500 hover:text-white"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title="Eliminar documento"
        description={
          pendingDelete
            ? `Se eliminará el PDF de ${pendingDelete.driver_name} (${pendingDelete.plate}). Esta acción no se puede deshacer.`
            : undefined
        }
        footer={
          <>
            <Button variant="ghost" onClick={() => setPendingDelete(null)}>
              Cancelar
            </Button>
            <Button
              variant="danger"
              loading={deleteMutation.isPending}
              onClick={() => pendingDelete && deleteMutation.mutate(pendingDelete.id)}
            >
              Eliminar
            </Button>
          </>
        }
      />
    </div>
  )
}
