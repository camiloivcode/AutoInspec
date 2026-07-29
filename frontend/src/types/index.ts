export interface Vehicle {
  id: string
  brand: string
  model: string
  year: number
  plate: string
  vin?: string
  color?: string
  engine_number?: string
  fuel_type?: string
  mileage?: number
  client_id?: string
  notes?: string
  full_name: string
  display_name: string
  created_at?: string
  updated_at?: string
}

export interface VehicleList {
  vehicles: Vehicle[]
  total: number
  skip: number
  limit: number
}

export interface Inspection {
  id: string
  vehicle_id: string
  inspector_id: string
  status: 'draft' | 'in_progress' | 'completed' | 'cancelled'
  title?: string
  description?: string
  location?: string
  notes?: string
  mileage_at_inspection?: number
  scheduled_date?: string
  completed_date?: string
  client_id?: string
  tags: string[]
  items_count: number
  images_count: number
  documents_count: number
  created_at?: string
  updated_at?: string
}

export interface InspectionList {
  inspections: Inspection[]
  total: number
  skip: number
  limit: number
}

export interface InspectionItem {
  id: string
  inspection_id: string
  name: string
  category: string
  status: string
  observation?: string
  score?: number
  is_pass?: boolean
  position: number
  images_count: number
  created_at?: string
  updated_at?: string
}

export interface InspectionImage {
  id: string
  inspection_id: string
  item_id?: string
  filename: string
  original_name: string
  file_url: string
  file_size: number
  mime_type: string
  width?: number
  height?: number
  caption?: string
  is_cover: boolean
  sort_order: number
  created_at?: string
}

export interface Document {
  id: string
  inspection_id: string
  template_id: string
  doc_type: 'word' | 'pdf'
  status: 'pending' | 'generated' | 'error'
  title: string
  file_url?: string
  file_size?: number
  generation_notes?: string
  created_at?: string
  updated_at?: string
}

export interface Template {
  id: string
  name: string
  description?: string
  category: string
  content: string
  variables: Record<string, string>
  is_active: boolean
  version: string
  created_at?: string
  updated_at?: string
}

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  phone?: string
  created_at?: string
  updated_at?: string
}
