import clsx from 'clsx'
import type { HTMLAttributes } from 'react'

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('plate', className)} {...rest} />
}

export function CardHeader({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('px-6 pt-6 pb-4', className)} {...rest} />
}

export function CardBody({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('px-6 pb-6', className)} {...rest} />
}
