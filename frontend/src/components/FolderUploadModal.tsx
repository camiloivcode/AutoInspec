import { useEffect } from 'react'
import { FolderOpen, Upload, X, Image } from 'lucide-react'

interface FolderUploadModalProps {
  open: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function FolderUploadModal({ open, onConfirm, onCancel }: FolderUploadModalProps) {
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancel()
    }
    if (open) {
      document.addEventListener('keydown', handleKey)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [open, onCancel])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in p-4"
      onClick={onCancel}
    >
      <div
        className="glass-card p-8 max-w-sm w-full animate-scale-in text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="w-16 h-16 mx-auto mb-5 rounded-2xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
          <FolderOpen className="w-8 h-8 text-primary-600" />
        </div>

        <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
          Subir carpeta
        </h2>

        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
          Se seleccionarán todas las imágenes dentro de la carpeta para la inspección vehicular.
        </p>

        <div className="flex items-center justify-center gap-2 mb-6 text-xs text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-900/50 rounded-xl py-3 px-4">
          <Image className="w-4 h-4" />
          <span>Se aceptan formatos JPG, PNG, WEBP</span>
        </div>

        <div className="flex items-center gap-3">
          <button onClick={onCancel} className="btn-ghost flex-1">
            <X className="w-4 h-4" /> Cancelar
          </button>
          <button onClick={onConfirm} className="btn-primary flex-1">
            <Upload className="w-4 h-4" /> Elegir carpeta
          </button>
        </div>
      </div>
    </div>
  )
}
