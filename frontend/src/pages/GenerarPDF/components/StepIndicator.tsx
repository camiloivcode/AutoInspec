const STEPS = ['Fotos', 'Análisis', 'Revisión', 'PDF']

/**
 * Progress as a run of highway chevrons: on the road a chevron means
 * "keep going this way". Filled = travelled, outlined = ahead.
 */
export default function StepIndicator({ current }: { current: number }) {
  return (
    <ol className="flex items-stretch gap-1" aria-label="Progreso de la generación de PDF">
      {STEPS.map((label, i) => {
        const isDone = current > i
        const isActive = current === i
        return (
          <li
            key={label}
            aria-current={isActive ? 'step' : undefined}
            className={`relative flex flex-1 items-center justify-center overflow-hidden py-2.5 text-[11px] font-bold uppercase tracking-[0.08em] transition-colors duration-200 sm:text-xs ${
              isDone
                ? 'bg-signal-500 text-white'
                : isActive
                  ? 'bg-plate-400 text-black'
                  : 'border-2 border-border-strong bg-surface text-fg-subtle'
            }`}
            style={{
              // Chevron: flat left edge on the first, arrow point on the rest.
              clipPath:
                i === 0
                  ? 'polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%)'
                  : i === STEPS.length - 1
                    ? 'polygon(0 0, 100% 0, 100% 100%, 0 100%, 12px 50%)'
                    : 'polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%, 12px 50%)',
            }}
          >
            <span className="px-1 text-center">
              <span className="font-mono">{String(i + 1).padStart(2, '0')}</span>
              <span className="ml-1.5 hidden sm:inline">{label}</span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}
