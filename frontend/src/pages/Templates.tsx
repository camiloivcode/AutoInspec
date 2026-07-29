import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, LayoutTemplate } from 'lucide-react'
import { templateService } from '../services/api'
import type { Template } from '../types'

export default function Templates() {
  const [editing, setEditing] = useState<Template | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', category: 'general', content: '' })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({ queryKey: ['templates'], queryFn: () => templateService.list(0, 100) })

  const createMutation = useMutation({
    mutationFn: () => templateService.create(form),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['templates'] }); setShowForm(false); setForm({ name: '', description: '', category: 'general', content: '' }) },
  })

  const updateMutation = useMutation({
    mutationFn: () => editing ? templateService.update(editing.id, form) : Promise.reject(),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['templates'] }); setEditing(null); setShowForm(false) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => templateService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['templates'] }),
  })

  const templates = (data as any)?.templates ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Plantillas</h1>
        <button onClick={() => { setShowForm(true); setEditing(null); setForm({ name: '', description: '', category: 'general', content: '' }) }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium">
          <Plus className="w-4 h-4" /> Nueva Plantilla
        </button>
      </div>

      {(showForm || editing) && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{editing ? 'Editar Plantilla' : 'Nueva Plantilla'}</h2>
          <div className="grid grid-cols-1 gap-4">
            <input placeholder="Nombre" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Descripción" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <textarea placeholder="Contenido de la plantilla (usa {{variable}} para variables)" value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} rows={8}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={() => editing ? updateMutation.mutate() : createMutation.mutate()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
              disabled={!form.name}>{editing ? 'Actualizar' : 'Guardar'}</button>
            <button onClick={() => { setShowForm(false); setEditing(null) }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((t: Template) => (
          <div key={t.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-900">{t.name}</h3>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded mt-1 inline-block">{t.category}</span>
              </div>
              <div className="flex gap-1">
                <button onClick={() => { setEditing(t); setForm({ name: t.name, description: t.description || '', category: t.category, content: t.content }); setShowForm(true) }}
                  className="p-1.5 text-gray-400 hover:text-primary-600"><Edit2 className="w-4 h-4" /></button>
                <button onClick={() => { if (confirm('¿Eliminar plantilla?')) deleteMutation.mutate(t.id) }}
                  className="p-1.5 text-gray-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
            <p className="text-sm text-gray-500 mb-2 line-clamp-2">{t.description || 'Sin descripción'}</p>
            <p className="text-xs text-gray-400">v{t.version}</p>
          </div>
        ))}
        {templates.length === 0 && !isLoading && (
          <div className="col-span-full text-center py-12 text-gray-500">
            <LayoutTemplate className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            No hay plantillas creadas
          </div>
        )}
      </div>
    </div>
  )
}
