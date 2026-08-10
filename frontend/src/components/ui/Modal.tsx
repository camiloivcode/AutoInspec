import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import type { ReactNode } from 'react'

type ModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children?: ReactNode
  footer?: ReactNode
}

export default function Modal({ open, onOpenChange, title, description, children, footer }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 animate-fade-in bg-black/60" />
        <Dialog.Content
          className="plate fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 animate-scale-in p-6 focus:outline-none"
        >
          <div className="mb-2 flex items-start justify-between gap-4">
            <Dialog.Title className="font-display text-lg font-bold uppercase tracking-[0.04em] text-fg">
              {title}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                aria-label="Cerrar"
                className="rounded-chip p-1.5 text-fg-subtle transition-colors hover:bg-bg-subtle hover:text-fg"
              >
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>
          {description && (
            <Dialog.Description className="text-sm text-fg-muted mb-4">{description}</Dialog.Description>
          )}
          {children}
          {footer && <div className="mt-6 flex justify-end gap-3">{footer}</div>}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
