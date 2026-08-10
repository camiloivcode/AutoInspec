import * as RadixSelect from '@radix-ui/react-select'
import { Check, ChevronDown } from 'lucide-react'
import clsx from 'clsx'

export type SelectOption = {
  value: string
  label: string
  disabled?: boolean
}

type SelectProps = {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  'aria-label'?: string
  className?: string
}

export default function Select({ value, onChange, options, placeholder, className, ...rest }: SelectProps) {
  return (
    <RadixSelect.Root value={value} onValueChange={onChange}>
      <RadixSelect.Trigger
        className={clsx(
          'inline-flex w-full items-center justify-between gap-2 rounded-plate border-2 border-border-strong bg-surface px-4 py-2.5 text-sm text-fg',
          'transition-colors duration-150 focus:outline-none focus:border-signal-500 focus:ring-2 focus:ring-signal-500/30',
          className
        )}
        {...rest}
      >
        <RadixSelect.Value placeholder={placeholder} />
        <RadixSelect.Icon>
          <ChevronDown className="w-4 h-4 text-fg-subtle" />
        </RadixSelect.Icon>
      </RadixSelect.Trigger>
      <RadixSelect.Portal>
        <RadixSelect.Content
          className="z-50 overflow-hidden rounded-plate border-2 border-border-strong bg-surface"
          position="popper"
          sideOffset={4}
        >
          <RadixSelect.Viewport className="p-1 max-h-72">
            {options.map((opt) => (
              <RadixSelect.Item
                key={opt.value}
                value={opt.value}
                disabled={opt.disabled}
                className={clsx(
                  'relative flex cursor-pointer select-none items-center rounded-chip px-3 py-2 pr-8 text-sm',
                  'text-fg data-[highlighted]:bg-signal-500 data-[highlighted]:text-white data-[highlighted]:outline-none',
                  'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-40'
                )}
              >
                <RadixSelect.ItemText>{opt.label}</RadixSelect.ItemText>
                <RadixSelect.ItemIndicator className="absolute right-2 inline-flex items-center">
                  <Check className="h-4 w-4" />
                </RadixSelect.ItemIndicator>
              </RadixSelect.Item>
            ))}
          </RadixSelect.Viewport>
        </RadixSelect.Content>
      </RadixSelect.Portal>
    </RadixSelect.Root>
  )
}
