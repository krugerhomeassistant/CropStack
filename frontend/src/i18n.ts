/**
 * Translation layer (Bloomery pattern). Every user-visible string goes through t() from the start, so adding a
 * language later is a dictionary, not a rewrite. Keys are the English text with {name} placeholders.
 * shortcut: English only; add src/locales/<lang>.ts, a language switch and the CI missing-string check
 * (Bloomery's i18n-check.mjs) together with the first translation (PLAN Phase 14).
 */
const CATALOG: Record<string, string> = {}

export function t(text: string, vars?: Record<string, string | number | null | undefined>): string {
  const s = CATALOG[text] ?? text
  return vars ? s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : s
}

/** Marks a module-level constant for translation; render it with t(). */
export const N_ = (text: string) => text
