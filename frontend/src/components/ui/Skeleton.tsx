import clsx from 'clsx'

export default function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse bg-bg-subtle rounded-md', className)} />
}

export function SkeletonCard() {
  return (
    <div className="card p-4 flex items-center gap-4">
      <Skeleton className="w-10 h-10 rounded-lg shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  )
}
