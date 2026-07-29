import { useState, useRef, useEffect } from 'react'
import { Upload, CheckCircle2, AlertCircle, Loader2, Download, FolderOpen, Eye, Sparkles, FileImage, X, Camera, ChevronDown, GripVertical } from 'lucide-react'
import ImagePreview from '../components/ImagePreview'
import FolderUploadModal from '../components/FolderUploadModal'
import { useToast } from '../context/ToastContext'
import { compressImage } from '../utils/imageCompressor'

const STEPS = [
  { key: 'idle', label: 'Fotos', desc: 'Seleccionar imágenes' },
  { key: 'analyzing', label: 'Analizar', desc: 'OCR + clasificación' },
  { key: 'review', label: 'Revisar', desc: 'Verificar posiciones' },
  { key: 'done', label: 'Descargar', desc: 'PDF generado' },
] as const

const POSITIONS = [
  { value: '1', label: '1. Formato de inspección', max: 1 },
  { value: '2', label: '2. Frontal', max: 1 },
  { value: '3', label: '3. Frontal lateral', max: 1 },
  { value: '4', label: '4. Lado izquierdo', max: 1 },
  { value: '5', label: '5. Lado derecho', max: 1 },
  { value: '6', label: '6. Trasera', max: 1 },
  { value: '7', label: '7. Lateral trasera', max: 1 },
  { value: '8', label: '8. Conductor', max: 1 },
  { value: '9', label: '9. Kit de carretera', max: 1 },
  { value: '10', label: '10. Gato y llanta de repuesto', max: 2 },
  { value: '11', label: '11. SOAT y documentos', max: 1 },
]

type ImageFile = {
  id: string
  file: File
  preview: string
  assignedPosition: string
  confidence?: 'high' | 'medium' | 'low'
}

type Step = 'idle' | 'analyzing' | 'review' | 'uploading' | 'generating' | 'done' | 'error'

function getActiveWizardStep(step: Step): number {
  if (step === 'idle') return 0
  if (step === 'analyzing') return 1
  if (step === 'review') return 2
  if (step === 'uploading' || step === 'generating' || step === 'done') return 3
  return 0
}

export default function GenerarPDF() {
  const [driverName, setDriverName] = useState('')
  const [plate, setPlate] = useState('')
  const [images, setImages] = useState<ImageFile[]>([])
  const [step, setStep] = useState<Step>('idle')
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [previewFilename, setPreviewFilename] = useState('')
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [showFolderModal, setShowFolderModal] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const folderInputRef = useRef<HTMLInputElement>(null)
  const dragCounter = useRef(0)
  const generatingRef = useRef(false)
  const { toast } = useToast()

  const wizardStep = getActiveWizardStep(step)

  useEffect(() => {
    function handleDragEnter(e: DragEvent) {
      if (generatingRef.current) return
      if (e.dataTransfer?.types.includes('Files')) {
        dragCounter.current++
        setIsDragging(true)
      }
    }
    function handleDragLeave() {
      dragCounter.current--
      if (dragCounter.current <= 0) {
        dragCounter.current = 0
        setIsDragging(false)
      }
    }
    function handleDragOver(e: DragEvent) { e.preventDefault() }
    async function handleDrop(e: DragEvent) {
      e.preventDefault()
      dragCounter.current = 0
      setIsDragging(false)
      if (generatingRef.current) return
      const rawFiles = Array.from(e.dataTransfer?.files || []).filter((f) => f.type.startsWith('image/'))
      if (rawFiles.length === 0) { toast('info', 'Solo se aceptan imágenes'); return }
      const compressed = await Promise.all(rawFiles.map((f) => compressImage(f)))
      setImages((prev) => [
        ...prev,
        ...compressed.map((file) => ({
          id: crypto.randomUUID(),
          file,
          preview: URL.createObjectURL(file),
          assignedPosition: '',
        })),
      ])
      setDownloadUrl('')
      setErrorMessage('')
      toast('success', `${rawFiles.length} imagen(es) agregada(s)`)
    }

    window.addEventListener('dragenter', handleDragEnter)
    window.addEventListener('dragleave', handleDragLeave)
    window.addEventListener('dragover', handleDragOver)
    window.addEventListener('drop', handleDrop)
    return () => {
      window.removeEventListener('dragenter', handleDragEnter)
      window.removeEventListener('dragleave', handleDragLeave)
      window.removeEventListener('dragover', handleDragOver)
      window.removeEventListener('drop', handleDrop)
    }
  }, [toast])

  function handleSelectImages() { fileInputRef.current?.click() }

  function handleSelectFolder() { setShowFolderModal(true) }

  async function handleFolderConfirm() {
    setShowFolderModal(false)
    if ('showDirectoryPicker' in window) {
      try {
        const dirHandle = await (window as any).showDirectoryPicker()
        const rawFiles: File[] = []
        for await (const entry of dirHandle.values()) {
          if (entry.kind === 'file') {
            const fileHandle = entry as FileSystemFileHandle
            const file = await fileHandle.getFile()
            if (file.type.startsWith('image/')) rawFiles.push(file)
          }
        }
        if (rawFiles.length === 0) { toast('info', 'No se encontraron imágenes en la carpeta'); return }
        const compressed = await Promise.all(rawFiles.map((f) => compressImage(f)))
        setImages((prev) => [
          ...prev,
          ...compressed.map((file) => ({
            id: crypto.randomUUID(),
            file,
            preview: URL.createObjectURL(file),
            assignedPosition: '',
          })),
        ])
        setDownloadUrl('')
        setErrorMessage('')
        toast('success', `${rawFiles.length} imagen(es) cargada(s)`)
      } catch (err: any) {
        if (err.name !== 'AbortError' && err.name !== 'SecurityError') {
          toast('error', 'Error al leer la carpeta')
        }
      }
    } else {
      setTimeout(() => folderInputRef.current?.click(), 100)
    }
  }

  async function handleFilesSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const rawFiles = Array.from(e.target.files || [])
    if (rawFiles.length === 0) return
    const compressed = await Promise.all(rawFiles.map((f) => compressImage(f)))
    setImages((prev) => [
      ...prev,
      ...compressed.map((file) => ({
        id: crypto.randomUUID(),
        file,
        preview: URL.createObjectURL(file),
        assignedPosition: '',
      })),
    ])
    setStep('idle')
    setDownloadUrl('')
    setErrorMessage('')
    if (e.target) e.target.value = ''
  }

  function removeImage(id: string) {
    setImages((prev) => {
      const img = prev.find((i) => i.id === id)
      if (img) URL.revokeObjectURL(img.preview)
      return prev.filter((i) => i.id !== id)
    })
  }

  function assignPosition(imageId: string, position: string) {
    setImages((prev) =>
      prev.map((img) => (img.id === imageId ? { ...img, assignedPosition: position, confidence: undefined } : img))
    )
  }

  function getCountForPosition(pos: string): number {
    return images.filter((img) => img.assignedPosition === pos).length
  }

  function validate(): string | null {
    if (!driverName.trim()) return 'El nombre del conductor es obligatorio'
    if (!plate.trim()) return 'La placa es obligatoria'
    if (images.length === 0) return 'Debe seleccionar al menos una imagen'
    const unassigned = images.filter((img) => !img.assignedPosition)
    if (unassigned.length > 0) return `Falta asignar posición a ${unassigned.length} imagen(es)`
    return null
  }

  async function handleAutoAnalyze() {
    if (images.length === 0) { setErrorMessage('Debe seleccionar al menos una imagen'); return }
    setAnalyzing(true); setErrorMessage(''); setStatusText('Analizando imágenes...'); setStep('analyzing')
    const formData = new FormData()
    for (const img of images) formData.append('images', img.file)
    try {
      const response = await fetch('/api/auto-analyze', { method: 'POST', body: formData })
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Error al analizar' }))
        throw new Error(err.detail || `Error ${response.status}`)
      }
      const data = await response.json()
      if (data.suggested_plate) setPlate(data.suggested_plate)
      setImages((prev) =>
        prev.map((img) => {
          const suggestion = data.suggestions?.find((s: any) => s.filename === img.file.name)
          if (suggestion?.suggested_position) {
            return { ...img, assignedPosition: String(suggestion.suggested_position), confidence: suggestion.confidence }
          }
          return img
        })
      )
      setStep('review'); setStatusText('')
      toast('success', `Análisis completado para ${images.length} imagen(es)`)
    } catch (err: any) {
      setStep('idle'); setErrorMessage(err.message || 'Error al analizar imágenes'); setStatusText('')
      toast('error', err.message || 'Error al analizar imágenes')
    } finally { setAnalyzing(false) }
  }

  function handleGenerate() {
    const error = validate()
    if (error) { setErrorMessage(error); return }
    setErrorMessage(''); setDownloadUrl(''); setProgress(0)
    setStep('uploading'); setStatusText('Subiendo imágenes...')
    generatingRef.current = true

    const formData = new FormData()
    formData.append('driver_name', driverName.trim()); formData.append('plate', plate.trim().toUpperCase())
    const sorted = [...images].sort((a, b) => parseInt(a.assignedPosition) - parseInt(b.assignedPosition))
    for (const img of sorted) { formData.append('images', img.file); formData.append('positions', img.assignedPosition) }

    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/generate-pdf/auto')

    const totalImages = sorted.length
    let imageIndex = 0

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const rawPct = (e.loaded / e.total) * 100
        const imagePct = totalImages > 1 ? (imageIndex / totalImages) * 100 : 0
        const combined = Math.min(Math.round(Math.max(rawPct * 0.7, imagePct)), 70)
        setProgress(combined)
        if (rawPct > 90 && imageIndex < totalImages - 1) {
          imageIndex++
          setStatusText(`Subiendo imagen ${imageIndex + 1} de ${totalImages}...`)
        } else {
          setStatusText(`Subiendo imágenes (${Math.round(rawPct)}%)...`)
        }
      }
    }

    xhr.onload = () => {
      generatingRef.current = false
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgress(70); setStatusText('Exportando PDF...')
        const blob = xhr.response
        setDownloadUrl(URL.createObjectURL(blob)); setProgress(100); setStatusText('¡Terminado!'); setStep('done')
        toast('success', 'PDF generado exitosamente')
      } else {
        let errMsg = 'Error al generar PDF'
        try {
          const err = JSON.parse(xhr.responseText)
          errMsg = err.detail || errMsg
        } catch {}
        setStep('error'); setErrorMessage(errMsg); setStatusText('Error')
        toast('error', errMsg)
      }
    }

    xhr.onerror = () => {
      generatingRef.current = false
      setStep('error'); setErrorMessage('Error de conexión'); setStatusText('Error')
      toast('error', 'Error de conexión al generar PDF')
    }

    xhr.responseType = 'blob'
    xhr.send(formData)
  }

  function handleDragStart(index: number) { setDragIndex(index) }

  function handleDragOver(e: React.DragEvent, index: number) {
    e.preventDefault()
    if (dragIndex === null || dragIndex === index) return
    setImages((prev) => {
      const copy = [...prev]
      const [moved] = copy.splice(dragIndex, 1)
      copy.splice(index, 0, moved)
      return copy
    })
    setDragIndex(index)
  }

  function handleDragEnd() { setDragIndex(null) }

  async function handleDropOnContainer(e: React.DragEvent) {
    e.preventDefault()
    const rawFiles = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith('image/'))
    if (rawFiles.length === 0) { toast('info', 'Solo se aceptan imágenes'); return }
    const compressed = await Promise.all(rawFiles.map((f) => compressImage(f)))
    setImages((prev) => [
      ...prev,
      ...compressed.map((file) => ({
        id: crypto.randomUUID(),
        file,
        preview: URL.createObjectURL(file),
        assignedPosition: '',
      })),
    ])
    setDownloadUrl('')
    setErrorMessage('')
    toast('success', `${rawFiles.length} imagen(es) agregada(s)`)
  }

  function handleDragOverContainer(e: React.DragEvent) { e.preventDefault() }

  const assignedCount = images.filter((img) => img.assignedPosition).length

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8 animate-fade-in">
      {isDragging && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-primary-900/20 backdrop-blur-sm animate-fade-in pointer-events-none">
          <div className="glass-card p-8 text-center animate-scale-in">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
              <Upload className="w-8 h-8 text-primary-600 animate-bounce" />
            </div>
            <p className="font-display text-base font-semibold text-slate-800 dark:text-slate-200">Suelte las imágenes aquí</p>
            <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">Se agregarán a la inspección</p>
          </div>
        </div>
      )}

      {/* Step Wizard */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between">
          {STEPS.map((s, i) => {
            const isActive = wizardStep === i
            const isDone = wizardStep > i
            return (
              <div key={s.key} className="flex items-center flex-1">
                <div className="flex items-center gap-3">
                  <div
                    className={`step-dot ${isDone ? 'bg-emerald-500 text-white' : isActive ? 'bg-primary-600 text-white ring-4 ring-primary-600/20' : 'bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400'}`}
                  >
                    {isDone ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
                  </div>
                  <div className="hidden sm:block">
                    <p className={`text-sm font-medium ${isActive ? 'text-primary-600 dark:text-primary-400' : isDone ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'}`}>
                      {s.label}
                    </p>
                    <p className="text-[11px] text-slate-400 dark:text-slate-500">{s.desc}</p>
                  </div>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`step-line mx-4 ${isDone ? 'bg-emerald-400' : wizardStep > i ? 'bg-primary-400' : 'bg-slate-200 dark:bg-slate-700'}`} />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Driver & Plate */}
      <div className="glass-card p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Conductor</label>
            <div className="relative">
              <input
                value={driverName}
                onChange={(e) => setDriverName(e.target.value)}
                placeholder="Nombre completo"
                className="input-field pl-10"
              />
              <Camera className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Placa
              {plate && step === 'review' && (
                <span className="ml-2 text-[11px] text-emerald-600 dark:text-emerald-400 font-normal">✓ Detectada</span>
              )}
            </label>
            <div className="relative">
              <input
                value={plate}
                onChange={(e) => setPlate(e.target.value.toUpperCase())}
                placeholder="ABC123"
                maxLength={10}
                className="input-field pl-10 uppercase tracking-wider font-mono"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-mono text-slate-400">🇨🇴</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analyzing State */}
      {step === 'analyzing' && (
        <div className="glass-card p-8 text-center animate-scale-in">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <Sparkles className="w-8 h-8 text-primary-600 animate-pulse" />
          </div>
          <p className="font-display text-lg font-semibold text-slate-800 dark:text-slate-200 mb-1">{statusText || 'Analizando imágenes...'}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">OCR + clasificación de posiciones</p>
          <div className="max-w-md mx-auto">
            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-primary-500 to-cyan-500 animate-shimmer" style={{ width: '65%', backgroundSize: '200% 100%' }} />
            </div>
          </div>
        </div>
      )}

      {/* Photos Section */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="font-display text-base font-semibold text-slate-900 dark:text-slate-100">Fotografías</h2>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{images.length} imagen(es) seleccionada(s) · {assignedCount} asignada(s)</p>
          </div>
          <div className="flex items-center gap-2">
            {images.length > 0 && (
              <button onClick={handleAutoAnalyze} disabled={analyzing} className="btn-amber">
                <Sparkles className="w-4 h-4" /> Auto-analizar
              </button>
            )}
            <button onClick={handleSelectImages} className="btn-primary">
              <Upload className="w-4 h-4" /> Añadir
            </button>
            <button onClick={handleSelectFolder} className="btn-ghost hidden sm:flex">
              <FolderOpen className="w-4 h-4" />
            </button>
          </div>
          <input ref={fileInputRef} type="file" accept="image/*" multiple onChange={handleFilesSelected} className="hidden" />
          <input ref={folderInputRef} type="file" accept="image/*" multiple {...({webkitdirectory: ''} as any)} onChange={handleFilesSelected} className="hidden" />
        </div>

        {images.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {images.map((img, i) => {
              const posDef = POSITIONS.find((p) => p.value === img.assignedPosition)
              const isDragging = dragIndex === i
              return (
                <div
                  key={img.id}
                  draggable
                  onDragStart={() => handleDragStart(i)}
                  onDragOver={(e) => handleDragOver(e, i)}
                  onDragEnd={handleDragEnd}
                  className={`group relative bg-slate-50 dark:bg-slate-900/50 rounded-xl border overflow-hidden transition-all duration-200 animate-slide-up ${
                    isDragging
                      ? 'border-primary-400 dark:border-primary-600 shadow-lg shadow-primary-500/20 scale-[1.02] opacity-60'
                      : 'border-slate-200 dark:border-slate-800 hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <button
                    onClick={() => { setPreviewImage(img.preview); setPreviewFilename(img.file.name) }}
                    className="w-full aspect-[4/3] bg-slate-100 dark:bg-slate-800 overflow-hidden cursor-pointer relative group/img"
                  >
                    <img src={img.preview} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover/img:scale-105" />
                    <div className="absolute inset-0 bg-black/0 group-hover/img:bg-black/30 transition-colors flex items-center justify-center">
                      <Eye className="w-6 h-6 text-white opacity-0 group-hover/img:opacity-100 transition-opacity" />
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); removeImage(img.id) }}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/40 hover:bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-all"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                    <div className="absolute top-2 left-2 p-1 rounded-lg bg-black/30 text-white/60 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity">
                      <GripVertical className="w-3.5 h-3.5" />
                    </div>
                  </button>
                  <div className="p-3 space-y-2">
                    <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{img.file.name}</p>
                    <div className="flex items-center gap-2">
                      {img.confidence && (
                        <span className={`badge-${img.confidence === 'high' ? 'high' : img.confidence === 'medium' ? 'medium' : 'low'}`}>
                          {img.confidence === 'high' ? 'Alta' : img.confidence === 'medium' ? 'Media' : 'Auto'}
                        </span>
                      )}
                      <div className="relative flex-1">
                        <select
                          value={img.assignedPosition}
                          onChange={(e) => assignPosition(img.id, e.target.value)}
                          className={`w-full text-xs px-2.5 py-2 rounded-lg border appearance-none cursor-pointer transition-colors ${
                            img.assignedPosition
                              ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800 text-primary-700 dark:text-primary-300 font-medium'
                              : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400'
                          }`}
                        >
                          <option value="">— Posición —</option>
                          {POSITIONS.filter((p) => {
                            const taken = getCountForPosition(p.value)
                            const isOwn = img.assignedPosition === p.value
                            return isOwn || taken < p.max
                          }).map((p) => {
                            const taken = getCountForPosition(p.value)
                            const isOwn = img.assignedPosition === p.value
                            const remaining = p.max - taken + (isOwn ? 1 : 0)
                            return (
                              <option key={p.value} value={p.value}>
                                {p.label}{p.max > 1 ? ` (${remaining} disp.)` : ''}
                              </option>
                            )
                          })}
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div
            onClick={handleSelectImages}
            onDrop={handleDropOnContainer}
            onDragOver={handleDragOverContainer}
            className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl p-14 text-center cursor-pointer hover:border-primary-300 dark:hover:border-primary-700 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-all duration-200 group"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-100 dark:bg-slate-800 group-hover:bg-primary-50 dark:group-hover:bg-primary-900/20 flex items-center justify-center transition-colors">
              <FileImage className="w-8 h-8 text-slate-300 dark:text-slate-600 group-hover:text-primary-400 transition-colors" />
            </div>
            <p className="font-display text-base font-semibold text-slate-600 dark:text-slate-400">Haga clic o arrastre imágenes aquí</p>
            <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">Fotografías de la inspección vehicular</p>
          </div>
        )}

        {step === 'review' && images.length > 0 && (
          <div className="mt-5 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 flex items-start gap-3 animate-fade-in">
            <Sparkles className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
            <div className="text-sm text-amber-800 dark:text-amber-200">
              <p className="font-medium">Análisis completado</p>
              <p className="text-amber-600 dark:text-amber-300 mt-0.5">
                Revise las posiciones. Las etiquetas <span className="font-semibold text-emerald-600">Alta</span> y <span className="font-semibold text-amber-600">Media</span> fueron detectadas automáticamente. Las de <span className="font-semibold text-slate-500">Auto</span> son asignaciones por orden.
              </p>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="mt-5 p-4 rounded-xl bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800/50 flex items-start gap-3 animate-fade-in">
            <AlertCircle className="w-5 h-5 text-rose-500 mt-0.5 shrink-0" />
            <p className="text-sm text-rose-700 dark:text-rose-300">{errorMessage}</p>
          </div>
        )}
      </div>

      {/* Upload/Generate Progress */}
      {(step === 'uploading' || step === 'generating') && (
        <div className="glass-card p-8 text-center animate-scale-in">
          <Loader2 className="w-8 h-8 mx-auto mb-3 text-primary-600 animate-spin" />
          <p className="font-display text-base font-semibold text-slate-800 dark:text-slate-200 mb-1">{statusText}</p>
          <div className="max-w-md mx-auto mt-4">
            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-primary-500 to-cyan-500 transition-all duration-500" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-xs text-slate-400 mt-2">{progress}%</p>
          </div>
        </div>
      )}

      {/* Done */}
      {step === 'done' && downloadUrl && (
        <div className="glass-card p-8 text-center animate-scale-in border-emerald-200 dark:border-emerald-900">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          </div>
          <p className="font-display text-lg font-semibold text-emerald-800 dark:text-emerald-300 mb-1">PDF generado exitosamente</p>
          <p className="text-sm text-emerald-600 dark:text-emerald-400 mb-6">{driverName.trim().replace(/\s+/g, '_')}.pdf</p>
          <a
            href={downloadUrl}
            download={`${driverName.trim().replace(/\s+/g, '_')}.pdf`}
            className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 active:scale-[0.97] transition-all text-sm font-semibold shadow-lg shadow-emerald-600/25"
          >
            <Download className="w-5 h-5" /> Descargar PDF
          </a>
        </div>
      )}

      {/* Bottom Actions */}
      <div className="flex items-center justify-end gap-3">
        {images.length > 0 && step !== 'done' && step !== 'uploading' && step !== 'generating' && (
          <button onClick={handleAutoAnalyze} disabled={analyzing} className="btn-amber">
            {analyzing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Auto-analizar
          </button>
        )}
        <button
          onClick={handleGenerate}
          disabled={step === 'uploading' || step === 'generating' || step === 'analyzing'}
          className="btn-primary"
        >
          {(step === 'uploading' || step === 'generating') ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Upload className="w-4 h-4" />
          )}
          Generar PDF
        </button>
      </div>

      <FolderUploadModal open={showFolderModal} onConfirm={handleFolderConfirm} onCancel={() => setShowFolderModal(false)} />

      {previewImage && (
        <ImagePreview src={previewImage} filename={previewFilename} onClose={() => setPreviewImage(null)} />
      )}
    </div>
  )
}
