import { useQuery } from '@tanstack/react-query'
import { Car, ClipboardList, FileText, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { vehicleService, inspectionService, documentService } from '../services/api'

function StatCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value ?? '...'}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: vehicles } = useQuery({ queryKey: ['vehicles'], queryFn: () => vehicleService.list(0, 1) })
  const { data: inspections } = useQuery({ queryKey: ['inspections'], queryFn: () => inspectionService.list(0, 1) })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: () => documentService.list(0, 1) })

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard icon={Car} label="Vehículos Registrados" value={vehicles?.total ?? 0} color="bg-emerald-600" />
        <StatCard icon={ClipboardList} label="Inspecciones Totales" value={inspections?.total ?? 0} color="bg-purple-600" />
        <StatCard icon={CheckCircle} label="Completadas" value="0" color="bg-green-600" />
        <StatCard icon={FileText} label="Documentos Generados" value={documents?.total ?? 0} color="bg-amber-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Actividad Reciente</h2>
          <p className="text-gray-500 text-sm">No hay actividad reciente. Comience creando un vehículo o inspección.</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Inspecciones Pendientes</h2>
          <p className="text-gray-500 text-sm">No hay inspecciones pendientes.</p>
        </div>
      </div>
    </div>
  )
}
