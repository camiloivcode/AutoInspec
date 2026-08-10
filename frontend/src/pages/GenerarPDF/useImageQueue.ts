import { useCallback, useEffect, useRef, useState } from 'react'
import { compressImage } from '../../utils/imageCompressor'

export type Confidence = 'high' | 'medium' | 'low'

export type ImageFile = {
  id: string
  file: File
  preview: string
  assignedPosition: string
  confidence?: Confidence
  // Original classifier suggestion, preserved even after the user corrects
  // assignedPosition, so the correction can be reported as feedback.
  suggestedPosition?: string
  suggestedConfidence?: Confidence
  suggestedMethod?: string
}

export function useImageQueue() {
  const [images, setImages] = useState<ImageFile[]>([])
  const imagesRef = useRef(images)
  imagesRef.current = images

  useEffect(() => {
    return () => {
      imagesRef.current.forEach((img) => URL.revokeObjectURL(img.preview))
    }
  }, [])

  const addFiles = useCallback(async (rawFiles: File[]) => {
    const imageFiles = rawFiles.filter((f) => f.type.startsWith('image/'))
    if (imageFiles.length === 0) return 0
    const compressed = await Promise.all(imageFiles.map((f) => compressImage(f)))
    setImages((prev) => [
      ...prev,
      ...compressed.map((file) => ({
        id: crypto.randomUUID(),
        file,
        preview: URL.createObjectURL(file),
        assignedPosition: '',
      })),
    ])
    return imageFiles.length
  }, [])

  const removeImage = useCallback((id: string) => {
    setImages((prev) => {
      const img = prev.find((i) => i.id === id)
      if (img) URL.revokeObjectURL(img.preview)
      return prev.filter((i) => i.id !== id)
    })
  }, [])

  const assignPosition = useCallback((id: string, position: string) => {
    setImages((prev) =>
      prev.map((img) => (img.id === id ? { ...img, assignedPosition: position, confidence: undefined } : img))
    )
  }, [])

  const applySuggestions = useCallback(
    (
      suggestedPlate: string | undefined,
      suggestions: Array<{ suggested_position?: string | number; confidence?: Confidence; method?: string }>
    ) => {
      setImages((prev) =>
        prev.map((img, i) => {
          const s = suggestions[i]
          if (s?.suggested_position != null) {
            return {
              ...img,
              assignedPosition: String(s.suggested_position),
              confidence: s.confidence,
              suggestedPosition: String(s.suggested_position),
              suggestedConfidence: s.confidence,
              suggestedMethod: s.method,
            }
          }
          return img
        })
      )
      return suggestedPlate
    },
    []
  )

  const getCountForPosition = useCallback(
    (pos: string) => images.filter((img) => img.assignedPosition === pos).length,
    [images]
  )

  return { images, addFiles, removeImage, assignPosition, applySuggestions, getCountForPosition }
}
