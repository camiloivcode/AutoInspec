import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Edit2, Trash2, Car } from 'lucide-react'
import { vehicleService } from '../services/api'
import type { Vehicle } from '../types'

export default function Vehicles() {
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Vehicle | null>(null)
  const [form, setForm] = useState({ brand: '', model: '', year: new Date().getFullYear(), plate: '', vin: '', color: '' })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['vehicles', search],
    queryFn: async () => search
      ? { vehicles: await vehicleService.search(search), total: 0, skip: 0, limit: 100 }
      : vehicleService.list(0, 100),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => vehicleService.create(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['vehicles'] }); setShowForm(false); resetForm() },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => vehicleService.update(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['vehicles'] }); setEditing(null); resetForm() },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => vehicleService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['vehicles'] }),
  })

  function resetForm() { setForm({ brand: '', model: '', year: new Date().getFullYear(), plate: '', vin: '', color: '' }) }

  const vehicles = data?.vehicles ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Vehículos</h1>
        <button onClick={() => { setShowForm(true); setEditing(null); resetForm() }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium">
          <Plus className="w-4 h-4" /> Nuevo Vehículo
        </button>
      </div>

      {(showForm || editing) && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{editing ? 'Editar Vehículo' : 'Nuevo Vehículo'}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input placeholder="Marca" value={form.brand} onChange={e => setForm({ ...form, brand: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Modelo" value={form.model} onChange={e => setForm({ ...form, model: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input type="number" placeholder="Año" value={form.year} onChange={e => setForm({ ...form, year: +e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Patente" value={form.plate} onChange={e => setForm({ ...form, plate: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="VIN" value={form.vin} onChange={e => setForm({ ...form, vin: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Color" value={form.color} onChange={e => setForm({ ...form, color: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={() => editing
              ? updateMutation.mutate({ id: editing.id, data: form })
              : createMutation.mutate(form)
            } className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
              disabled={!form.brand || !form.model || !form.plate}>
              {editing ? 'Actualizar' : 'Guardar'}
            </button>
            <button onClick={() => { setShowForm(false); setEditing(null) }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por patente, marca o modelo..."
              className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg w-full max-w-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
        </div>

        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Patente</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Marca / Modelo</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Año</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Color</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {vehicles.map((v: Vehicle) => (
              <tr key={v.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{v.plate}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{v.brand} {v.model}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{v.year}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{v.color || '-'}</td>
                <td className="px-6 py-4 text-sm text-right">
                  <button onClick={() => { setEditing(v); setForm({ brand: v.brand, model: v.model, year: v.year, plate: v.plate, vin: v.vin || '', color: v.color || '' }) }}
                    className="p-1.5 text-gray-400 hover:text-primary-600 mr-1"><Edit2 className="w-4 h-4" /></button>
                  <button onClick={() => { if (confirm('¿Eliminar vehículo?')) deleteMutation.mutate(v.id) }}
                    className="p-1.5 text-gray-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                </td>
              </tr>
            ))}
            {vehicles.length === 0 && !isLoading && (
              <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                <Car className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                No hay vehículos registrados
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
