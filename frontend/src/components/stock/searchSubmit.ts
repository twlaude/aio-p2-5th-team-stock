export function normalizeQuery(raw: string): string {
  return raw.trim().replace(/\s+/g, " ");
}

export function handleSearchSubmit(raw: string, submit: (query: string) => void): boolean {
  const normalized = normalizeQuery(raw);
  if (!normalized) {
    return false;
  }

  submit(normalized);
  return true;
}
