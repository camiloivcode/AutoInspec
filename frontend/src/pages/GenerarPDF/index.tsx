import { useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, Loader2, ScanLine, Upload } from 'lucide-react'
import ImagePreview from '../../components/ImagePreview'
import Button from '../../components/ui/Button'
import { useToast } from '../../context/ToastContext'
import { useImageQueue } from './useImageQueue'
import { useGenerationFlow, getWizardIndex, pluralize } from './useGenerationFlow'
import StepIndicator from './components/StepIndicator'
import StepUpload from './steps/StepUpload'
import StepAnalyzing from './steps/StepAnalyzing'
import StepReview from './steps/StepReview'
import StepDone from './steps/StepDone'

export default function GenerarPDF() {
  const [driverName, setDriverName] = useState('')
  const [plate, setPlate] = useState('')
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [previewFilename, setPreviewFilename] = useState('')
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { images, addFiles, removeImage, assignPosition, applySuggestions, getCountForPosition } = useImageQueue()
  const { step, progress, statusText, downloadUrl, errorMessage, setErrorMessage, analyze, generate, reset, goToUpload } =
    useGenerationFlow()

  const wizardStep = getWizardIndex(step)

  const handlePreview = useCallback((preview: string, filename: string) => {
    setPreviewImage(preview)
    setPreviewFilename(filename)
  }, [])

  async function handleAddFiles(files: File[]) {
    const count = await addFiles(files)
    if (count > 0) {
      setErrorMessage('')
      toast('success', `${pluralize(count, 'imagen agregada', 'imágenes agregadas')}`)
    }
  }

  async function handleFolderFiles(files: File[]) {
    const images = files.filter((f) => f.type.startsWith('image/'))
    if (images.length === 0) {
      toast('info', 'No se encontraron imágenes en esa carpeta. Elija una carpeta con fotos .jpg o .png.')
      return
    }
    await handleAddFiles(images)
  }

  async function handleAnalyze() {
    if (!driverName.trim()) {
      setErrorMessage('El nombre del conductor es obligatorio')
      return
    }
    if (!plate.trim()) {
      setErrorMessage('La placa es obligatoria')
      return
    }
    const result = await analyze(images)
    if (result) {
      const suggestedPlate = applySuggestions(result.suggestedPlate, result.suggestions)
      if (suggestedPlate) setPlate(suggestedPlate)
    }
  }

  function handleGenerate() {
    const unassigned = images.filter((img) => !img.assignedPosition)
    if (unassigned.length > 0) {
      setErrorMessage(`Falta asignar posición a ${pluralize(unassigned.length, 'imagen', 'imágenes')}`)
      return
    }
    generate(driverName, plate, images, () => queryClient.invalidateQueries({ queryKey: ['history'] }))
  }

  function handleReset() {
    reset()
    setDriverName('')
    setPlate('')
  }

  const canAnalyze = driverName.trim() && plate.trim() && images.length > 0
  const showFooterNav = step === 'upload' || step === 'review'

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      <StepIndicator current={wizardStep} />

      {step === 'upload' && (
        <StepUpload
          driverName={driverName}
          onDriverNameChange={setDriverName}
          plate={plate}
          onPlateChange={setPlate}
          images={images}
          onAddFiles={handleAddFiles}
          onFolderFiles={handleFolderFiles}
          onRemoveImage={removeImage}
          onPreview={handlePreview}
        />
      )}

      {step === 'analyzing' && <StepAnalyzing statusText={statusText} />}

      {step === 'review' && (
        <StepReview
          images={images}
          onAssign={assignPosition}
          onRemove={removeImage}
          getCountForPosition={getCountForPosition}
          onPreview={handlePreview}
          errorMessage={errorMessage}
        />
      )}

      {(step === 'uploading' || step === 'done' || step === 'error') && (
        <StepDone
          step={step}
          progress={progress}
          statusText={statusText}
          downloadUrl={downloadUrl}
          errorMessage={errorMessage}
          driverName={driverName}
          onRetry={handleGenerate}
          onReset={handleReset}
        />
      )}

      {step === 'upload' && errorMessage && (
        <p role="alert" className="text-center text-sm font-semibold text-stop-500">
          {errorMessage}
        </p>
      )}

      {showFooterNav && (
        <div className="flex items-center justify-between gap-3">
          <div>
            {step === 'review' && (
              <Button variant="ghost" onClick={goToUpload}>
                <ArrowLeft className="w-4 h-4" /> Atrás
              </Button>
            )}
          </div>
          <div>
            {step === 'upload' && (
              <Button onClick={handleAnalyze} disabled={!canAnalyze}>
                <ScanLine className="h-4 w-4" /> Analizar fotos
              </Button>
            )}
            {step === 'review' && (
              <Button onClick={handleGenerate}>
                <Upload className="w-4 h-4" /> Generar PDF
                <ArrowRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      )}

      {step === 'analyzing' && (
        <div className="flex justify-center">
          <Button variant="ghost" disabled>
            <Loader2 className="w-4 h-4 animate-spin" /> Analizando…
          </Button>
        </div>
      )}

      {previewImage && <ImagePreview src={previewImage} filename={previewFilename} onClose={() => setPreviewImage(null)} />}
    </div>
  )
}
