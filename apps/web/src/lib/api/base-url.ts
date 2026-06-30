type PublicRuntimeEnvironment = {
  NODE_ENV?: string;
  NEXT_PUBLIC_CONTROL_API_URL?: string;
};

export function resolveControlApiUrl(environment: PublicRuntimeEnvironment) {
  const configured = environment.NEXT_PUBLIC_CONTROL_API_URL?.trim();
  if (configured) return configured.replace(/\/+$/, "");
  if (environment.NODE_ENV === "production") return "";
  return "http://localhost:8181";
}

export const CONTROL_API_URL = resolveControlApiUrl({
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_CONTROL_API_URL: process.env.NEXT_PUBLIC_CONTROL_API_URL,
});
