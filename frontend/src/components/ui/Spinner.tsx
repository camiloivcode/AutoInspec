import clsx from 'clsx'

const sizes = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-2',
}

export default function Spinner({ size = 'md', className }: { size?: keyof typeof sizes; className?: string }) {
  return (
    <div
      role="status"
      aria-label="Cargando"
      className={clsx('animate-spin rounded-full border-signal-500 border-t-transparent', sizes[size], className)}
    />
  )
}
