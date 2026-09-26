import type { MacroSource } from '../types/recipe'

const LABELS: Record<MacroSource, string> = {
  usda_verified: 'Verified',
  llm_estimated: 'Estimated',
  mixed: 'Mixed',
}

export function MacroBadge({ source }: { source: MacroSource }) {
  return <span className={`macro-badge macro-badge--${source}`}>{LABELS[source]}</span>
}
