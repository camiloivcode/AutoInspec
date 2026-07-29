import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Eye, Trash2, ClipboardList } from 'lucide-react'
import { inspectionService } from '../services/api'
import type { Inspection } from '../types'

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-emerald-100 text-emerald-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
}

export default function Inspections() {
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ vehicle_id: '', title: '', description: '', location: '' })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['inspections'],
    queryFn: () => inspectionService.list(0, 100),
  })

  const createMutation = useMutation({
    mutationFn: () => inspectionService.create({ ...form, inspector_id: 'default' }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['inspections'] }); setShowForm(false); setForm({ vehicle_id: '', title: '', description: '', location: '' }) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => inspectionService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inspections'] }),
  })

  const inspections = (data as any)?.inspections ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Inspecciones</h1>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium">
          <Plus className="w-4 h-4" /> Nueva Inspección
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Nueva Inspección</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input placeholder="ID del Vehículo" value={form.vehicle_id} onChange={e => setForm({ ...form, vehicle_id: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Título" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Ubicación" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Descripción" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={() => createMutation.mutate()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
              disabled={!form.vehicle_id}>Crear Inspección</button>
            <button onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Título</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Vehículo</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Estado</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Items</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Imágenes</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {inspections.map((inv: Inspection) => (
              <tr key={inv.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{inv.title || 'Sin título'}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{inv.vehicle_id?.slice(0, 8)}...</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusColors[inv.status] || 'bg-gray-100 text-gray-700'}`}>
                    {inv.status === 'draft' ? 'Borrador' : inv.status === 'in_progress' ? 'En Progreso' : inv.status === 'completed' ? 'Completada' : 'Cancelada'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{inv.items_count}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{inv.images_count}</td>
                <td className="px-6 py-4 text-sm text-right">
                  <button className="p-1.5 text-gray-400 hover:text-primary-600 mr-1"><Eye className="w-4 h-4" /></button>
                  <button onClick={() => { if (confirm('¿Eliminar inspección?')) deleteMutation.mutate(inv.id) }}
                    className="p-1.5 text-gray-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                </td>
              </tr>
            ))}
            {inspections.length === 0 && !isLoading && (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                <ClipboardList className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                No hay inspecciones registradas
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
