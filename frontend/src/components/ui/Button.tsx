import { forwardRef, type ButtonHTMLAttributes } from 'react'
import clsx from 'clsx'
import Spinner from './Spinner'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

const variantClasses: Record<Variant, string> = {
  primary: 'plate-signal hover:bg-signal-600 active:bg-signal-700',
  secondary: 'bg-surface border-2 border-fg text-fg hover:bg-bg-subtle active:bg-bg-subtle',
  ghost: 'border-2 border-transparent text-fg-muted hover:bg-bg-subtle active:bg-bg-subtle',
  danger: 'bg-stop-500 border-2 border-stop-700 text-white hover:bg-stop-600 active:bg-stop-700',
}

const sizeClasses: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-5 py-2.5 text-sm gap-2',
  lg: 'px-6 py-3 text-base gap-2',
}

type BaseProps = {
  variant?: Variant
  size?: Size
  loading?: boolean
  children?: React.ReactNode
} & ButtonHTMLAttributes<HTMLButtonElement>

type IconOnlyProps = BaseProps & {
  iconOnly: true
  'aria-label': string
}

type RegularProps = BaseProps & {
  iconOnly?: false
}

export type ButtonProps = IconOnlyProps | RegularProps

const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading, iconOnly, className, children, disabled, ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center justify-center rounded-plate font-bold uppercase tracking-[0.06em]',
        'transition-all duration-150 active:translate-y-px',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-500 focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
        'disabled:opacity-45 disabled:cursor-not-allowed disabled:active:translate-y-0',
        variantClasses[variant],
        iconOnly ? 'p-2.5' : sizeClasses[size],
        className
      )}
      {...rest}
    >
      {loading ? (
        <Spinner size="sm" className={variant === 'primary' || variant === 'danger' ? 'border-white border-t-transparent' : undefined} />
      ) : (
        children
      )}
    </button>
  )
})

export default Button
