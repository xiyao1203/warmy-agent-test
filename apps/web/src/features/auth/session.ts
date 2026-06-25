export function safeReturnTo(value: string | null | undefined) {
  if (!value?.startsWith("/") || value.startsWith("//")) {
    return "/";
  }
  return value;
}
