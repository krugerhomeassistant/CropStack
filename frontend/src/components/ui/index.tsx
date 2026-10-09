/**
 * CropStack UI kit (docs/DESIGN.md). Small, dependency-free components over the utilities in index.css.
 * shortcut: Sheet, Toast and Tabs are added with the first screen that needs them (DESIGN.md, Components).
 */
import {
  cloneElement,
  useId,
  type ButtonHTMLAttributes,
  type ReactElement,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router'
import { ArrowLeft, type LucideIcon } from 'lucide-react'
import { t } from '../../i18n'

const join = (...classes: (string | false | null | undefined)[]) => classes.filter(Boolean).join(' ')

// ---------------------------------------------------------------- actions

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
const VARIANT: Record<Variant, string> = {
  primary: 'btn',
  secondary: 'btn-secondary',
  ghost: 'btn-ghost',
  danger: 'btn-danger',
}

export function Button({
  variant = 'primary',
  className,
  type = 'button',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button type={type} className={join(VARIANT[variant], className)} {...props} />
}

export function IconButton({
  icon: Icon,
  label,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { icon: LucideIcon; label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={join(
        'inline-flex size-11 items-center justify-center rounded-xl text-muted transition-colors hover:bg-sunken hover:text-ink',
        className,
      )}
      {...props}
    >
      <Icon className="size-5" aria-hidden />
    </button>
  )
}

// ---------------------------------------------------------------- layout

export function PageHeader({ title, subtitle, back }: { title: string; subtitle?: ReactNode; back?: boolean }) {
  const navigate = useNavigate()
  return (
    <header className="flex items-start gap-2">
      {back && <IconButton icon={ArrowLeft} label={t('Back')} onClick={() => navigate(-1)} className="-ml-3" />}
      <div className="min-w-0">
        <h1 className="text-[1.9375rem] leading-tight font-extrabold">{title}</h1>
        {subtitle && <p className="mt-1 text-muted">{subtitle}</p>}
      </div>
    </header>
  )
}

export function Section({
  title,
  description,
  action,
  children,
  className,
  ...rest
}: {
  title?: string
  description?: ReactNode
  action?: ReactNode
  children?: ReactNode
  className?: string
  'aria-label'?: string
}) {
  const id = useId()
  return (
    <section className={join('card flex flex-col gap-4', className)} aria-labelledby={title ? id : undefined} {...rest}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-3">
          <div>
            {title && (
              <h2 id={id} className="text-xl font-bold">
                {title}
              </h2>
            )}
            {description && <p className="mt-0.5 text-sm text-muted">{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

// ---------------------------------------------------------------- forms

/** Label, hint and error around one input; wires up id, aria-describedby and aria-invalid. */
export function Field({
  label,
  hint,
  error,
  children,
  className,
}: {
  label: string
  hint?: ReactNode
  error?: string
  children: ReactElement<Record<string, unknown>>
  className?: string
}) {
  const id = useId()
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  return (
    <div className={join('field', className)}>
      <label htmlFor={id}>{label}</label>
      {cloneElement(children, {
        id,
        'aria-describedby': [hintId, errorId].filter(Boolean).join(' ') || undefined,
        'aria-invalid': error ? true : undefined,
      })}
      {hint && (
        <span id={hintId} className="text-sm font-normal text-muted">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className="text-sm font-normal text-danger">
          {error}
        </span>
      )}
    </div>
  )
}

export type Option<V extends string | number> = { value: V; label: string; hint?: string }

/** A group of large radio rows: label plus a one-line hint each. */
export function RadioCards<V extends string | number>({
  legend,
  name,
  options,
  value,
  onChange,
  hideLegend = false,
}: {
  legend: string
  name: string
  options: readonly Option<V>[]
  value: V
  onChange: (value: V) => void
  hideLegend?: boolean
}) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className={hideLegend ? 'sr-only' : 'mb-2 text-sm font-semibold'}>{legend}</legend>
      {options.map((o) => (
        <label
          key={o.value}
          className={join(
            'flex cursor-pointer items-start gap-3 rounded-[var(--radius-row)] border p-3 transition-colors',
            value === o.value ? 'border-leaf bg-leaf/8' : 'border-line hover:bg-sunken',
          )}
        >
          <input
            type="radio"
            name={name}
            className="radio mt-0.5"
            checked={value === o.value}
            onChange={() => onChange(o.value)}
          />
          <span>
            <span className="font-semibold">{o.label}</span>
            {o.hint && <span className="block text-sm text-muted">{o.hint}</span>}
          </span>
        </label>
      ))}
    </fieldset>
  )
}

export function Switch({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}) {
  return (
    <input
      type="checkbox"
      role="switch"
      aria-label={label}
      className="switch"
      checked={checked}
      disabled={disabled}
      onChange={(e) => onChange(e.target.checked)}
    />
  )
}

// ---------------------------------------------------------------- status

export function Badge({ children, tone = 'leaf' }: { children: ReactNode; tone?: 'leaf' | 'muted' | 'marigold' }) {
  const tones = {
    leaf: 'bg-leaf/12 text-leaf',
    muted: 'bg-sunken text-muted',
    marigold: 'bg-marigold text-[#18261c]', // ink stays dark on marigold in both themes (contrast 7.3:1)
  }
  return <span className={join('inline-flex rounded-full px-3 py-1 text-sm font-bold', tones[tone])}>{children}</span>
}

export function ErrorMessage({ children }: { children: ReactNode }) {
  return (
    <p className="text-sm text-danger" role="alert">
      {children}
    </p>
  )
}

/** Something failed: say what, and offer the way out. */
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-start gap-3" role="alert">
      <p className="text-sm">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          {t('Try again')}
        </Button>
      )}
    </div>
  )
}

/** Nothing here yet: what will appear, and what to do now. */
export function EmptyState({
  icon: Icon,
  title,
  children,
  action,
}: {
  icon: LucideIcon
  title: string
  children: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-start gap-3 py-2">
      <span className="inline-flex size-12 items-center justify-center rounded-full bg-leaf/12 text-leaf">
        <Icon className="size-6" aria-hidden />
      </span>
      <div>
        <h3 className="text-lg font-bold">{title}</h3>
        <p className="mt-1 max-w-prose text-sm text-muted">{children}</p>
      </div>
      {action}
    </div>
  )
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={join('animate-pulse rounded-[var(--radius-row)] bg-sunken', className)} aria-hidden />
}
