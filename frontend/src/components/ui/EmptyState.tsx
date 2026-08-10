import type { ComponentType, ReactNode } from 'react'

type EmptyStateProps = {
  icon: ComponentType<{ className?: string }>
  title: string
  description?: string
  action?: ReactNode
}

export default function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="w-14 h-14 rounded-full bg-bg-subtle flex items-center justify-center mb-4">
        <Icon className="w-6 h-6 text-fg-subtle" />
      </div>
      <h3 className="font-display font-semibold text-fg mb-1">{title}</h3>
      {description && <p className="text-sm text-fg-muted max-w-sm mb-4">{description}</p>}
      {action}
    </div>
  )
}
