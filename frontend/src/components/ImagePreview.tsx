import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'

interface ImagePreviewProps {
  src: string
  filename: string
  onClose: () => void
}

export default function ImagePreview({ src, filename, onClose }: ImagePreviewProps) {
  return (
    <Dialog.Root open onOpenChange={(next) => !next && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-md animate-fade-in" />
        <Dialog.Content
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 focus:outline-none"
          onClick={onClose}
          aria-describedby={undefined}
        >
          <div
            className="relative flex flex-col max-w-[90vw] max-h-[90vh] animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3 px-1">
              <Dialog.Title asChild>
                <p className="text-white/80 text-sm truncate font-medium">{filename}</p>
              </Dialog.Title>
              <Dialog.Close asChild>
                <button
                  aria-label="Cerrar vista previa"
                  className="p-2 rounded-xl bg-white/10 hover:bg-white/20 transition-colors text-white/80 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </Dialog.Close>
            </div>
            <img
              src={src}
              alt={filename}
              className="max-h-[85vh] max-w-full rounded-plate object-contain"
            />
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
