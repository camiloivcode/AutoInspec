import { useNavigate } from 'react-router-dom'
import { FileQuestion, ArrowLeft } from 'lucide-react'
import { Card, CardBody } from '../components/ui/Card'
import Button from '../components/ui/Button'

export default function NotFound() {
  const navigate = useNavigate()
  return (
    <div className="flex items-center justify-center h-full px-6">
      <Card className="max-w-md animate-scale-in">
        <CardBody className="pt-12 pb-10 text-center">
          <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-bg-subtle flex items-center justify-center">
            <FileQuestion className="w-10 h-10 text-fg-subtle" />
          </div>
          <h1 className="font-display text-3xl font-bold text-fg mb-2">404</h1>
          <p className="text-fg-muted mb-8">Esta página no existe</p>
          <Button onClick={() => navigate('/')}>
            <ArrowLeft className="w-4 h-4" /> Volver al inicio
          </Button>
        </CardBody>
      </Card>
    </div>
  )
}
