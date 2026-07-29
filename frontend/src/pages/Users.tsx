import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Users as UsersIcon } from 'lucide-react'
import { userService } from '../services/api'
import type { User } from '../types'

export default function UsersPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '', role: 'inspector' })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({ queryKey: ['users'], queryFn: () => userService.list(0, 100) })

  const createMutation = useMutation({
    mutationFn: () => userService.create(form),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['users'] }); setShowForm(false); resetForm() },
  })

  const updateMutation = useMutation({
    mutationFn: () => editing ? userService.update(editing.id, { full_name: form.full_name, email: form.email, role: form.role }) : Promise.reject(),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['users'] }); setEditing(null); setShowForm(false); resetForm() },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => userService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  function resetForm() { setForm({ username: '', email: '', full_name: '', password: '', role: 'inspector' }) }

  const users = (data as any)?.users ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
        <button onClick={() => { setShowForm(true); setEditing(null); resetForm() }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium">
          <Plus className="w-4 h-4" /> Nuevo Usuario
        </button>
      </div>

      {(showForm || editing) && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{editing ? 'Editar Usuario' : 'Nuevo Usuario'}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input placeholder="Usuario" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Nombre Completo" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            <input placeholder="Email" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            {!editing && <input placeholder="Contraseña" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />}
            <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option value="inspector">Inspector</option>
              <option value="admin">Administrador</option>
              <option value="client">Cliente</option>
            </select>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={() => editing ? updateMutation.mutate() : createMutation.mutate()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
              disabled={!form.username || !form.email || (!editing && !form.password)}>
              {editing ? 'Actualizar' : 'Guardar'}
            </button>
            <button onClick={() => { setShowForm(false); setEditing(null) }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Usuario</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Nombre</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Email</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Rol</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map((u: User) => (
              <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{u.username}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{u.full_name}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{u.email}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    u.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                    u.role === 'inspector' ? 'bg-emerald-100 text-emerald-700' : 'bg-sky-100 text-sky-700'
                  }`}>{u.role}</span>
                </td>
                <td className="px-6 py-4 text-sm text-right">
                  <button onClick={() => { setEditing(u); setForm({ username: u.username, email: u.email, full_name: u.full_name, password: '', role: u.role }); setShowForm(true) }}
                    className="p-1.5 text-gray-400 hover:text-primary-600 mr-1"><Edit2 className="w-4 h-4" /></button>
                  <button onClick={() => { if (confirm('¿Eliminar usuario?')) deleteMutation.mutate(u.id) }}
                    className="p-1.5 text-gray-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                </td>
              </tr>
            ))}
            {users.length === 0 && !isLoading && (
              <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                <UsersIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                No hay usuarios registrados
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
