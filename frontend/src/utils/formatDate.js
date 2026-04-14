export function formatRelativeDate(dateStr) {
  if (!dateStr) return '';
  // Backend stores UTC times via datetime.now(timezone.utc).isoformat().
  // Ensure we parse it as UTC if no timezone suffix is present.
  let normalized = dateStr;
  if (!normalized.endsWith('Z') && !normalized.includes('+')) {
    normalized += 'Z';
  }
  const date = new Date(normalized);
  const now = new Date();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}
