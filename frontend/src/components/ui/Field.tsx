import { useId, type InputHTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'

type FieldProps = {
  label: string
  error?: string
  hint?: string
  icon?: ReactNode
} & InputHTMLAttributes<HTMLInputElement>

export default function Field({ label, error, hint, icon, className, id, ...rest }: FieldProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  const hintId = hint ? `${inputId}-hint` : undefined
  const errorId = error ? `${inputId}-error` : undefined

  return (
    <div>
      <label
        htmlFor={inputId}
        className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.1em] text-fg-muted"
      >
        {label}
      </label>
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle pointer-events-none">
            {icon}
          </span>
        )}
        <input
          id={inputId}
          aria-describedby={clsx(hintId, errorId) || undefined}
          aria-invalid={error ? true : undefined}
          className={clsx(
            'w-full rounded-plate border-2 bg-surface px-4 py-2.5 text-sm text-fg placeholder:text-fg-subtle',
            'transition-colors duration-150 focus:outline-none focus:border-signal-500',
            'focus:ring-2 focus:ring-signal-500/30',
            error ? 'border-stop-500' : 'border-border-strong',
            icon && 'pl-10',
            className
          )}
          {...rest}
        />
      </div>
      {hint && !error && (
        <p id={hintId} className="mt-1.5 text-xs text-fg-subtle">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="mt-1.5 text-xs font-semibold text-stop-500">
          {error}
        </p>
      )}
    </div>
  )
}
