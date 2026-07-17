import { describe, expect, it } from "vitest";

import {
  normalizeGeneratedError,
  problemKind,
  problemMessage,
  responseProblem,
} from "../problem";

describe("API problem details", () => {
  it("extracts actionable detail from generated client errors", () => {
    expect(
      problemMessage(
        { detail: "部署未配置 Model Runner", status: 503 },
        "请求失败",
      ),
    ).toBe("部署未配置 Model Runner");
    expect(problemMessage({ status: 503 }, "请求失败")).toBe("请求失败");
  });

  it("turns an RFC 7807 response into an error with status", async () => {
    const error = await responseProblem(
      new Response(
        JSON.stringify({ detail: "Run execution runtime is unavailable" }),
        {
          headers: { "content-type": "application/problem+json" },
          status: 503,
        },
      ),
      "启动运行失败",
    );

    expect(error.message).toBe("Run execution runtime is unavailable");
    expect(error.status).toBe(503);
  });

  it("uses a safe fallback for a non-JSON response", async () => {
    const error = await responseProblem(
      new Response("proxy failure", { status: 502 }),
      "服务暂时不可用",
    );

    expect(error.message).toBe("服务暂时不可用");
    expect(error.status).toBe(502);
  });

  it.each([
    [401, "authentication"],
    [403, "permission"],
    [404, "not-found"],
    [409, "conflict"],
    [422, "validation"],
  ] as const)("normalizes generated status %s", (status, kind) => {
    const error = normalizeGeneratedError({ detail: "API detail" }, status);

    expect(problemKind(error)).toBe(kind);
    expect(problemMessage(error, "请求失败")).toBe("API detail");
  });

  it("does not expose non-JSON generated proxy bodies", () => {
    const error = normalizeGeneratedError("proxy failure", 502);

    expect(problemKind(error)).toBe("service");
    expect(problemMessage(error, "请求失败")).toBe("服务暂时不可用");
  });
});
