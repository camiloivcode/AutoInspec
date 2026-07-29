import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Download, Trash2, RefreshCw } from 'lucide-react'
import { documentService } from '../services/api'
import type { Document } from '../types'

export default function Documents() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['documents'], queryFn: () => documentService.list(0, 100) })

  const generateMutation = useMutation({
    mutationFn: (id: string) => documentService.generate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  })

  const documents = (data as any)?.documents ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Documentos</h1>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Título</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Tipo</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Estado</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Tamaño</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {documents.map((doc: Document) => (
              <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{doc.title}</td>
                <td className="px-6 py-4 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-medium uppercase ${doc.doc_type === 'pdf' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>
                    {doc.doc_type}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    doc.status === 'generated' ? 'bg-green-100 text-green-700' :
                    doc.status === 'error' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>{doc.status}</span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-right">
                  <button onClick={() => generateMutation.mutate(doc.id)}
                    className="p-1.5 text-gray-400 hover:text-primary-600 mr-1" title="Generar">
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  {doc.file_url && (
                    <a href={doc.file_url} download className="p-1.5 text-gray-400 hover:text-green-600 mr-1 inline-block">
                      <Download className="w-4 h-4" />
                    </a>
                  )}
                  <button onClick={() => { if (confirm('¿Eliminar documento?')) deleteMutation.mutate(doc.id) }}
                    className="p-1.5 text-gray-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                </td>
              </tr>
            ))}
            {documents.length === 0 && !isLoading && (
              <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                No hay documentos generados
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
