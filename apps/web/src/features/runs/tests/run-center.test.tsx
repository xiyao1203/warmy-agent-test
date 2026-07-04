import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RunDetailScreen } from "../run-detail-screen";
import { RunCenterScreen } from "../run-center-screen";
import { RunCenter } from "../run-center";
import { RunDetail } from "../run-detail";

const api = vi.hoisted(() => ({
  cancelRun: vi.fn(),
  createRun: vi.fn(),
  getRun: vi.fn(),
  listPublishedPlanVersions: vi.fn(),
  listArtifacts: vi.fn(),
  listRunCases: vi.fn(),
  listRuns: vi.fn(),
  runEventsUrl: vi.fn(),
}));

vi.mock("../api", () => api);

const push = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  push.mockClear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const running = {
  cancelled_cases: 0,
  completed_at: null,
  created_at: "2026-06-26T10:00:00Z",
  error_cases: 0,
  failed_cases: 0,
  id: "run-1",
  passed_cases: 1,
  project_id: "project-1",
  started_at: "2026-06-26T10:00:01Z",
  status: "running",
  test_plan_version_id: "version-1",
  total_cases: 3,
  workflow_id: "run-run-1",
};

function renderWithQueryClient(children: ReactNode) {
  const client = new QueryClient({
    defaultOptions: {
      mutations: { retry: false },
      queries: { retry: false, staleTime: 0 },
    },
  });
  return render(
    <QueryClientProvider client={client}>{children}</QueryClientProvider>,
  );
}

describe("RunCenter", () => {
  it("creates a run from a published plan version and renders dashboard summary", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(
      <RunCenter
        onCreate={onCreate}
        planVersions={[{ id: "version-1", label: "客服回归 v2" }]}
        projectId="project-1"
        runs={[
          running,
          {
            ...running,
            completed_at: "2026-06-26T10:02:00Z",
            id: "run-2",
            passed_cases: 3,
            status: "passed",
            total_cases: 3,
          },
        ]}
      />,
    );

    expect(screen.getByText("总运行")).toBeVisible();
    expect(screen.getByText("2")).toBeVisible();
    expect(screen.getAllByText("运行中").length).toBeGreaterThan(0);
    expect(screen.getByText("通过率")).toBeVisible();
    expect(screen.getByText("1 / 3")).toBeVisible();
    fireEvent.change(screen.getByLabelText("搜索运行"), {
      target: { value: "run-2" },
    });
    expect(screen.queryByText("Run run-1")).not.toBeInTheDocument();
    expect(screen.getByText("Run run-2")).toBeVisible();
    fireEvent.change(screen.getByLabelText("测试计划版本"), {
      target: { value: "version-1" },
    });
    expect(
      screen.getByRole("link", { name: /1. 发布测试计划/ }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(screen.getByRole("link", { name: "查看结果" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-2",
    );
    fireEvent.click(screen.getByRole("button", { name: "启动测试执行" }));

    await waitFor(() => expect(onCreate).toHaveBeenCalledWith("version-1"));
  });

  it("renders empty and service states", () => {
    const { rerender } = render(
      <RunCenter planVersions={[]} projectId="project-1" runs={[]} />,
    );
    expect(screen.getByText("暂无运行记录")).toBeVisible();
    expect(screen.getByText(/先去测试计划里配置并发布一个版本/)).toBeVisible();
    expect(
      screen.getByRole("link", { name: "去配置测试计划" }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");

    rerender(
      <RunCenter error="service" planVersions={[]} projectId="project-1" />,
    );
    expect(screen.getByText("运行中心暂时不可用")).toBeVisible();
  });

  it("shows an actionable runtime error when creating a run fails", async () => {
    const onCreate = vi.fn().mockRejectedValue({
      detail: "Run execution runtime is unavailable",
      status: 503,
    });
    render(
      <RunCenter
        onCreate={onCreate}
        planVersions={[{ id: "version-1", label: "客服回归 v2" }]}
        projectId="project-1"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "启动测试执行" }));

    expect(
      await screen.findByText(
        "运行服务暂不可用：请确认 Temporal 和 API Runner 已启动后重试。",
      ),
    ).toBeVisible();
  });

  it("navigates to the created run after starting execution", async () => {
    api.listRuns.mockResolvedValue([]);
    api.listPublishedPlanVersions.mockResolvedValue([
      { id: "version-1", label: "客服回归 v2" },
    ]);
    api.createRun.mockResolvedValue({ id: "run-created" });

    renderWithQueryClient(<RunCenterScreen projectId="project-1" />);

    await screen.findByRole("button", { name: "启动测试执行" });
    fireEvent.change(screen.getByLabelText("测试计划版本"), {
      target: { value: "version-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "启动测试执行" }));

    await waitFor(() =>
      expect(push).toHaveBeenCalledWith("/projects/project-1/runs/run-created"),
    );
  });
});

describe("RunDetail", () => {
  it("shows cases, normalized trace, errors and cancellation", async () => {
    const onCancel = vi.fn().mockResolvedValue(undefined);
    render(
      <RunDetail
        artifacts={[]}
        cases={[
          {
            duration_ms: 120,
            error_message: "upstream timed out",
            error_type: "TransientError",
            id: "case-1",
            name: "流式回答",
            output: null,
            status: "error",
            test_case_id: "test-case-1",
            trace: [
              {
                name: "http.request",
                attributes: { "http.response.status_code": 504 },
              },
            ],
          },
        ]}
        onCancel={onCancel}
        projectId="test-project"
        run={running}
      />,
    );

    expect(screen.getAllByText("执行摘要")).toHaveLength(2);
    expect(screen.getByText("实时刷新")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "用例列表" }));
    expect(screen.getByText("TransientError")).toBeVisible();
    expect(screen.getByText("http.request")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "取消运行" }));
    await waitFor(() => expect(onCancel).toHaveBeenCalledTimes(1));
  });
});

describe("RunDetailScreen realtime refresh", () => {
  it("opens run events and refreshes detail data after snapshots", async () => {
    const sources: Array<{
      close: ReturnType<typeof vi.fn>;
      onerror: (() => void) | null;
      onmessage: ((event: MessageEvent) => void) | null;
      url: string;
    }> = [];
    class FakeEventSource {
      close = vi.fn();
      onerror: (() => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;

      constructor(public url: string) {
        sources.push(this);
      }
    }
    vi.stubGlobal("EventSource", FakeEventSource);
    api.getRun.mockResolvedValue(running);
    api.listRunCases.mockResolvedValue([]);
    api.runEventsUrl.mockReturnValue(
      "/api/v1/projects/project-1/runs/run-1/events",
    );

    renderWithQueryClient(
      <RunDetailScreen projectId="project-1" runId="run-1" />,
    );

    await waitFor(() =>
      expect(api.runEventsUrl).toHaveBeenCalledWith("project-1", "run-1"),
    );
    expect(sources[0]?.url).toBe(
      "/api/v1/projects/project-1/runs/run-1/events",
    );

    sources[0]?.onmessage?.(
      new MessageEvent("message", {
        data: JSON.stringify({ ...running, passed_cases: 2 }),
      }),
    );

    await waitFor(() => expect(api.getRun).toHaveBeenCalledTimes(2));
    expect(api.listRunCases).toHaveBeenCalledTimes(2);
  });

  it("closes a broken event stream so polling fallback can continue", async () => {
    const sources: Array<{
      close: ReturnType<typeof vi.fn>;
      onerror: (() => void) | null;
      onmessage: ((event: MessageEvent) => void) | null;
    }> = [];
    class FakeEventSource {
      close = vi.fn();
      onerror: (() => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;

      constructor() {
        sources.push(this);
      }
    }
    vi.stubGlobal("EventSource", FakeEventSource);
    api.getRun.mockResolvedValue(running);
    api.listRunCases.mockResolvedValue([]);
    api.runEventsUrl.mockReturnValue("/events");

    renderWithQueryClient(
      <RunDetailScreen projectId="project-1" runId="run-1" />,
    );

    await waitFor(() => expect(sources).toHaveLength(1));
    sources[0]?.onerror?.();

    await waitFor(() => expect(sources[0]?.close).toHaveBeenCalledTimes(1));
  });

  it("reconnects a broken event stream with exponential backoff", async () => {
    const sources: Array<{
      close: ReturnType<typeof vi.fn>;
      onerror: (() => void) | null;
      onmessage: ((event: MessageEvent) => void) | null;
      url: string;
    }> = [];
    class FakeEventSource {
      close = vi.fn();
      onerror: (() => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;

      constructor(public url: string) {
        sources.push(this);
      }
    }
    vi.stubGlobal("EventSource", FakeEventSource);
    api.getRun.mockResolvedValue(running);
    api.listRunCases.mockResolvedValue([]);
    api.runEventsUrl.mockReturnValue("/events");

    renderWithQueryClient(
      <RunDetailScreen projectId="project-1" runId="run-1" />,
    );

    await waitFor(() => expect(sources).toHaveLength(1));
    vi.useFakeTimers();
    sources[0]?.onerror?.();
    expect(sources[0]?.close).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(999);
    });
    expect(sources).toHaveLength(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(sources).toHaveLength(2);

    sources[1]?.onerror?.();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1999);
    });
    expect(sources).toHaveLength(2);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(sources).toHaveLength(3);
  });
});
