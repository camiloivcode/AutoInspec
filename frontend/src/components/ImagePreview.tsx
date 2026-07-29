import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

interface ImagePreviewProps {
  src: string
  filename: string
  onClose: () => void
}

function PreviewContent({ src, filename, onClose }: ImagePreviewProps) {
  useEffect(() => {
    const main = document.querySelector('main')
    const scrollY = main ? main.scrollTop : window.scrollY

    if (main) {
      main.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'hidden'
    }

    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)

    return () => {
      document.removeEventListener('keydown', handleKey)
      if (main) {
        main.style.overflow = ''
        main.scrollTop = scrollY
      } else {
        document.body.style.overflow = ''
        window.scrollTo(0, scrollY)
      }
    }
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative flex flex-col max-w-[90vw] max-h-[90vh] animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3 px-1">
          <p className="text-white/80 text-sm truncate font-medium">{filename}</p>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-white/10 hover:bg-white/20 transition-colors text-white/80 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
        <img
          src={src}
          alt={filename}
          className="max-w-full max-h-[85vh] object-contain rounded-2xl shadow-2xl shadow-black/40"
        />
      </div>
    </div>
  )
}

export default function ImagePreview(props: ImagePreviewProps) {
  return createPortal(<PreviewContent {...props} />, document.body)
}
