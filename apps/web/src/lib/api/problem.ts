type ApiErrorShape = {
  detail?: string;
  status?: number;
  title?: string;
};

export type UiProblem =
  | "authentication"
  | "conflict"
  | "not-found"
  | "permission"
  | "service"
  | "validation";

export function problemKind(error: unknown): UiProblem {
  const problem = error as ApiErrorShape | undefined;

  if (problem?.status === 401) return "authentication";
  if (problem?.status === 403) return "permission";
  if (problem?.status === 404) return "not-found";
  if (problem?.status === 409) return "conflict";
  if (problem?.status === 422) return "validation";
  return "service";
}
