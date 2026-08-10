import { useDropzone } from 'react-dropzone'
import { FileImage, Upload } from 'lucide-react'

type DropZoneProps = {
  onFiles: (files: File[]) => void
  compact?: boolean
}

export default function DropZone({ onFiles, compact }: DropZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'image/*': [] },
    multiple: true,
    onDrop: (accepted) => {
      if (accepted.length > 0) onFiles(accepted)
    },
  })

  if (compact) {
    return (
      <div
        {...getRootProps()}
        className={`flex cursor-pointer items-center justify-center gap-2 rounded-plate border-2 border-dashed px-4 py-3 text-sm font-bold uppercase tracking-[0.06em] transition-colors ${
          isDragActive
            ? 'border-signal-500 bg-signal-50 text-signal-600 dark:bg-signal-900/20'
            : 'border-border-strong text-fg-muted hover:border-signal-400 hover:bg-bg-subtle'
        }`}
      >
        <input {...getInputProps()} aria-label="Añadir más fotografías" />
        <Upload className="w-4 h-4" />
        Añadir más fotos
      </div>
    )
  }

  return (
    <div
      {...getRootProps()}
      className={`group cursor-pointer rounded-plate border-2 border-dashed p-10 text-center transition-colors duration-150 sm:p-14 ${
        isDragActive ? 'border-signal-500 bg-signal-50 dark:bg-signal-900/20' : 'border-border-strong hover:border-signal-400 hover:bg-bg-subtle'
      }`}
    >
      <input {...getInputProps()} aria-label="Seleccionar fotografías de la inspección" />
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-plate bg-signal-500">
        <FileImage className="h-8 w-8 text-white" />
      </div>
      <p className="font-display text-base font-bold uppercase tracking-[0.04em] text-fg">
        {isDragActive ? 'Suelte las imágenes aquí' : 'Toque o arrastre las fotos'}
      </p>
      <p className="mt-1 text-sm text-fg-muted">Fotografías de la inspección vehicular</p>
    </div>
  )
}
