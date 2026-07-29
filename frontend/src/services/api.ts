import axios from 'axios'
import type {
  Vehicle, VehicleList, Inspection, InspectionList, InspectionItem,
  InspectionImage, Document, Template, User,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export const vehicleService = {
  list: (skip = 0, limit = 100) =>
    api.get<VehicleList>('/vehicles', { params: { skip, limit } }).then(r => r.data),
  get: (id: string) =>
    api.get<Vehicle>(`/vehicles/${id}`).then(r => r.data),
  create: (data: Partial<Vehicle>) =>
    api.post<Vehicle>('/vehicles', data).then(r => r.data),
  update: (id: string, data: Partial<Vehicle>) =>
    api.put<Vehicle>(`/vehicles/${id}`, data).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/vehicles/${id}`),
  search: (q: string) =>
    api.get<Vehicle[]>('/vehicles/search', { params: { q } }).then(r => r.data),
}

export const inspectionService = {
  list: (skip = 0, limit = 100) =>
    api.get<InspectionList>('/inspections', { params: { skip, limit } }).then(r => r.data),
  get: (id: string) =>
    api.get<Inspection>(`/inspections/${id}`).then(r => r.data),
  create: (data: Partial<Inspection>) =>
    api.post<Inspection>('/inspections', data).then(r => r.data),
  update: (id: string, data: Partial<Inspection>) =>
    api.put<Inspection>(`/inspections/${id}`, data).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/inspections/${id}`),
  complete: (id: string) =>
    api.post<Inspection>(`/inspections/${id}/complete`).then(r => r.data),
  getItems: (id: string) =>
    api.get<InspectionItem[]>(`/inspections/${id}/items`).then(r => r.data),
  createItem: (inspectionId: string, data: Partial<InspectionItem>) =>
    api.post<InspectionItem>(`/inspections/${inspectionId}/items`, data).then(r => r.data),
  updateItem: (inspectionId: string, itemId: string, data: Partial<InspectionItem>) =>
    api.put<InspectionItem>(`/inspections/${inspectionId}/items/${itemId}`, data).then(r => r.data),
  deleteItem: (inspectionId: string, itemId: string) =>
    api.delete(`/inspections/${inspectionId}/items/${itemId}`),
  getImages: (id: string) =>
    api.get<InspectionImage[]>(`/inspections/${id}/images`).then(r => r.data),
  uploadImage: (inspectionId: string, file: File, itemId?: string, caption?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (itemId) form.append('item_id', itemId)
    if (caption) form.append('caption', caption)
    return api.post<InspectionImage>(`/inspections/${inspectionId}/images`, form).then(r => r.data)
  },
  deleteImage: (inspectionId: string, imageId: string) =>
    api.delete(`/inspections/${inspectionId}/images/${imageId}`),
}

export const documentService = {
  list: (skip = 0, limit = 100) =>
    api.get('/documents', { params: { skip, limit } }).then(r => r.data),
  listByInspection: (inspectionId: string) =>
    api.get<Document[]>(`/documents/by-inspection/${inspectionId}`).then(r => r.data),
  get: (id: string) =>
    api.get<Document>(`/documents/${id}`).then(r => r.data),
  create: (data: Partial<Document>) =>
    api.post<Document>('/documents', data).then(r => r.data),
  generate: (id: string) =>
    api.post<Document>(`/documents/${id}/generate`).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/documents/${id}`),
}

export const templateService = {
  list: (skip = 0, limit = 100) =>
    api.get('/templates', { params: { skip, limit } }).then(r => r.data),
  get: (id: string) =>
    api.get<Template>(`/templates/${id}`).then(r => r.data),
  create: (data: Partial<Template>) =>
    api.post<Template>('/templates', data).then(r => r.data),
  update: (id: string, data: Partial<Template>) =>
    api.put<Template>(`/templates/${id}`, data).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/templates/${id}`),
}

export const userService = {
  list: (skip = 0, limit = 100) =>
    api.get('/users', { params: { skip, limit } }).then(r => r.data),
  get: (id: string) =>
    api.get<User>(`/users/${id}`).then(r => r.data),
  create: (data: Partial<User>) =>
    api.post<User>('/users', data).then(r => r.data),
  update: (id: string, data: Partial<User>) =>
    api.put<User>(`/users/${id}`, data).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/users/${id}`),
}
