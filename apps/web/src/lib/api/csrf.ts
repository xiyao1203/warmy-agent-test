export function readCookie(
  name: string,
  source = typeof document === "undefined" ? "" : document.cookie,
) {
  const prefix = `${encodeURIComponent(name)}=`;
  const value = source
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix))
    ?.slice(prefix.length);

  return value ? decodeURIComponent(value) : undefined;
}

export function csrfHeaders(token = readCookie("csrf_token")) {
  return token ? { "x-csrf-token": token } : {};
}
