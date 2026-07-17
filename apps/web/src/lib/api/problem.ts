type ApiErrorShape = {
  detail?: string;
  status?: number;
  title?: string;
};

export class ApiProblemError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiProblemError";
  }
}

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

export function problemMessage(error: unknown, fallback: string): string {
  const problem = error as ApiErrorShape | undefined;
  if (typeof problem?.detail === "string" && problem.detail.trim()) {
    return problem.detail;
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}

export function normalizeGeneratedError(
  error: unknown,
  status: number,
): ApiErrorShape | ApiProblemError {
  if (error && typeof error === "object" && !(error instanceof Error)) {
    return { ...(error as ApiErrorShape), status };
  }
  if (error instanceof Error && error.message.trim()) {
    return new ApiProblemError(error.message, status);
  }
  return new ApiProblemError("服务暂时不可用", status);
}

export async function responseProblem(
  response: Response,
  fallback: string,
): Promise<ApiProblemError> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = undefined;
  }
  return new ApiProblemError(problemMessage(body, fallback), response.status);
}
