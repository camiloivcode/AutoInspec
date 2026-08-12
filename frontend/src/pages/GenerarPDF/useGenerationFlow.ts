import { useCallback, useEffect, useRef, useState } from 'react'
import { useToast } from '../../context/ToastContext'
import type { ImageFile } from './useImageQueue'

export type FlowStep = 'upload' | 'analyzing' | 'review' | 'uploading' | 'done' | 'error'

export function getWizardIndex(step: FlowStep): number {
  if (step === 'upload') return 0
  if (step === 'analyzing') return 1
  if (step === 'review') return 2
  return 3
}

type AnalyzeResult = {
  suggestedPlate?: string
  suggestions: Array<{ suggested_position?: string | number; confidence?: 'high' | 'medium' | 'low'; method?: string }>
}

export function pluralize(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`
}

export function useGenerationFlow() {
  const [step, setStep] = useState<FlowStep>('upload')
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const { toast } = useToast()
  const downloadUrlRef = useRef('')

  useEffect(() => {
    downloadUrlRef.current = downloadUrl
  }, [downloadUrl])

  useEffect(
    () => () => {
      if (downloadUrlRef.current) URL.revokeObjectURL(downloadUrlRef.current)
    },
    []
  )

  const analyze = useCallback(
    async (images: ImageFile[]): Promise<AnalyzeResult | null> => {
      if (images.length === 0) {
        setErrorMessage('Debe seleccionar al menos una imagen')
        return null
      }
      setErrorMessage('')
      setStatusText('Analizando imágenes...')
      setStep('analyzing')
      const formData = new FormData()
      for (const img of images) formData.append('images', img.file)
      try {
        const response = await fetch('/api/auto-analyze', { method: 'POST', body: formData })
        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: 'Error al analizar' }))
          throw new Error(err.detail || `Error ${response.status}`)
        }
        const data = await response.json()
        setStep('review')
        setStatusText('')
        toast('success', `Análisis completado para ${pluralize(images.length, 'imagen', 'imágenes')}`)
        return { suggestedPlate: data.suggested_plate, suggestions: data.suggestions ?? [] }
      } catch (err) {
        setStep('upload')
        const message = err instanceof Error ? err.message : 'Error al analizar imágenes'
        setErrorMessage(message)
        setStatusText('')
        toast('error', message)
        return null
      }
    },
    [toast]
  )

  const generate = useCallback(
    (driverName: string, plate: string, images: ImageFile[], onSuccess?: () => void) => {
      setErrorMessage('')
      if (downloadUrlRef.current) {
        URL.revokeObjectURL(downloadUrlRef.current)
        setDownloadUrl('')
      }
      setProgress(0)
      setStep('uploading')
      setStatusText('Subiendo imágenes...')

      const formData = new FormData()
      formData.append('driver_name', driverName.trim())
      formData.append('plate', plate.trim().toUpperCase())
      const sorted = [...images].sort((a, b) => parseInt(a.assignedPosition) - parseInt(b.assignedPosition))
      for (const img of sorted) {
        formData.append('images', img.file)
        formData.append('positions', img.assignedPosition)
        formData.append('suggested_positions', img.suggestedPosition ?? '')
        formData.append('suggested_confidences', img.suggestedConfidence ?? '')
        formData.append('suggested_methods', img.suggestedMethod ?? '')
      }

      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/generate-pdf/auto')

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100)
          setProgress(pct)
          setStatusText(pct < 100 ? `Subiendo imágenes (${pct}%)...` : 'Generando PDF...')
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const url = URL.createObjectURL(xhr.response)
          setDownloadUrl(url)
          setStep('done')
          setStatusText('')
          toast('success', 'PDF generado exitosamente')
          onSuccess?.()
        } else {
          let errMsg = 'Error al generar PDF'
          try {
            const err = JSON.parse(xhr.responseText)
            errMsg = err.detail || errMsg
          } catch {
            /* respuesta no es JSON, se usa el mensaje por defecto */
          }
          setStep('error')
          setErrorMessage(errMsg)
          toast('error', errMsg)
        }
      }

      xhr.onerror = () => {
        setStep('error')
        setErrorMessage('Error de conexión. Verifique su red e intente nuevamente.')
        toast('error', 'Error de conexión al generar PDF')
      }

      xhr.responseType = 'blob'
      xhr.send(formData)
    },
    [toast]
  )

  const goToUpload = useCallback(() => setStep('upload'), [])
  const goToReview = useCallback(() => setStep('review'), [])

  const reset = useCallback(() => {
    setStep('upload')
    setProgress(0)
    setStatusText('')
    setErrorMessage('')
    if (downloadUrlRef.current) URL.revokeObjectURL(downloadUrlRef.current)
    setDownloadUrl('')
  }, [])

  return {
    step,
    progress,
    statusText,
    downloadUrl,
    errorMessage,
    setErrorMessage,
    analyze,
    generate,
    reset,
    goToUpload,
    goToReview,
  }
}
