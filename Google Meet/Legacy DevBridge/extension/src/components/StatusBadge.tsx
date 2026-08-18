interface StatusBadgeProps { label: string; tone: "good" | "neutral" | "warning" }

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return <span className={`status status--${tone}`}><span className="status__dot" />{label}</span>;
}
