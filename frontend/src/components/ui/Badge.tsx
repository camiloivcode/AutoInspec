import clsx from 'clsx'
import type { ReactNode } from 'react'

type Tone = 'success' | 'warning' | 'neutral'

const toneClass: Record<Tone, string> = {
  success: 'badge-signal',
  warning: 'badge-plate',
  neutral: 'badge-neutral',
}

export default function Badge({ tone, children }: { tone: Tone; children: ReactNode }) {
  return <span className={clsx(toneClass[tone])}>{children}</span>
}
