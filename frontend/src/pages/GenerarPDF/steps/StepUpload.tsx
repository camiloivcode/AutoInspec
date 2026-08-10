import { useRef } from 'react'
import { FolderOpen, User } from 'lucide-react'
import { Card, CardBody } from '../../../components/ui/Card'
import Field from '../../../components/ui/Field'
import Button from '../../../components/ui/Button'
import DropZone from '../components/DropZone'
import PhotoCard from '../components/PhotoCard'
import type { ImageFile } from '../useImageQueue'
import { pluralize } from '../useGenerationFlow'

// iOS Safari is the only target without directory upload; everywhere else
// webkitdirectory works over plain HTTP too, unlike showDirectoryPicker.
const supportsFolderUpload =
  typeof HTMLInputElement !== 'undefined' && 'webkitdirectory' in HTMLInputElement.prototype

type StepUploadProps = {
  driverName: string
  onDriverNameChange: (value: string) => void
  plate: string
  onPlateChange: (value: string) => void
  images: ImageFile[]
  onAddFiles: (files: File[]) => void
  onFolderFiles: (files: File[]) => void
  onRemoveImage: (id: string) => void
  onPreview: (preview: string, filename: string) => void
}

export default function StepUpload({
  driverName,
  onDriverNameChange,
  plate,
  onPlateChange,
  images,
  onAddFiles,
  onFolderFiles,
  onRemoveImage,
  onPreview,
}: StepUploadProps) {
  const folderInputRef = useRef<HTMLInputElement>(null)

  function handleFolderChange(e: React.ChangeEvent<HTMLInputElement>) {
    onFolderFiles(Array.from(e.target.files ?? []))
    e.target.value = ''
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardBody className="pt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field
            label="Conductor"
            value={driverName}
            onChange={(e) => onDriverNameChange(e.target.value)}
            placeholder="Nombre completo"
            icon={<User className="w-4 h-4" />}
          />
          <Field
            label="Placa"
            value={plate}
            onChange={(e) => onPlateChange(e.target.value.toUpperCase())}
            placeholder="ABC123"
            maxLength={10}
            hint={plate.trim() ? undefined : 'Se completa sola tras el análisis'}
            className="border-plate-500 bg-plate-400 font-mono font-bold uppercase tracking-[0.15em] text-black placeholder:text-black/40 focus:border-plate-600"
          />
        </CardBody>
      </Card>

      <Card>
        <CardBody className="pt-6">
          <div className="flex items-center justify-between gap-3 mb-5">
            <div>
              <h2 className="font-display text-base font-semibold text-fg">Fotografías</h2>
              <p className="text-xs text-fg-subtle mt-0.5">
                {images.length === 0 ? 'Ninguna imagen seleccionada' : pluralize(images.length, 'imagen seleccionada', 'imágenes seleccionadas')}
              </p>
            </div>
            {supportsFolderUpload && (
              <>
                <Button variant="secondary" size="sm" onClick={() => folderInputRef.current?.click()}>
                  <FolderOpen className="w-4 h-4" /> Subir carpeta
                </Button>
                <input
                  ref={folderInputRef}
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleFolderChange}
                  className="hidden"
                  {...({ webkitdirectory: '', directory: '' } as Record<string, string>)}
                />
              </>
            )}
          </div>

          {images.length === 0 ? (
            <DropZone onFiles={onAddFiles} />
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {images.map((img) => (
                  <PhotoCard
                    key={img.id}
                    image={img}
                    onPreview={() => onPreview(img.preview, img.file.name)}
                    onRemove={() => onRemoveImage(img.id)}
                  />
                ))}
              </div>
              <DropZone onFiles={onAddFiles} compact />
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
