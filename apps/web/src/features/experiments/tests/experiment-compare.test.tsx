import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { DegradationHighlight } from "../degradation-highlight";
import { AggregationView } from "../aggregation-view";
import { ExperimentCompare } from "../experiment-compare";

describe("DegradationHighlight", () => {
  const mockDegradations = [
    {
      case_id: "tc1",
      metric: "score",
      baseline: 0.9,
      current: 0.5,
      change: -0.44,
    },
    {
      case_id: "tc2",
      metric: "status",
      baseline: "passed",
      current: "failed",
      change: -1.0,
    },
  ];

  it("renders degradation list", () => {
    render(<DegradationHighlight degradations={mockDegradations} />);
    expect(screen.getByText("tc1")).toBeInTheDocument();
    expect(screen.getByText("tc2")).toBeInTheDocument();
  });

  it("shows metric type", () => {
    render(<DegradationHighlight degradations={mockDegradations} />);
    expect(screen.getByText("score")).toBeInTheDocument();
    expect(screen.getByText("status")).toBeInTheDocument();
  });

  it("shows baseline and current values", () => {
    render(<DegradationHighlight degradations={mockDegradations} />);
    // 使用 getAllByText 因为值可能在多处出现
    const values09 = screen.getAllByText((content) => content.includes("0.9"));
    expect(values09.length).toBeGreaterThanOrEqual(1);
    const values05 = screen.getAllByText((content) => content.includes("0.5"));
    expect(values05.length).toBeGreaterThanOrEqual(1);
  });

  it("renders empty state when no degradations", () => {
    render(<DegradationHighlight degradations={[]} />);
    expect(screen.getByText("无退化项")).toBeInTheDocument();
  });
});

describe("AggregationView", () => {
  const mockStats = {
    total_cases: 10,
    passed: 8,
    failed: 2,
    pass_rate: 0.8,
    latency: {
      avg: 1200,
      p50: 1000,
      p95: 2500,
      std_dev: 300,
      min_val: 500,
      max_val: 3000,
    },
    score: {
      avg: 0.82,
      p50: 0.85,
      p95: 0.65,
      std_dev: 0.12,
      min_val: 0.5,
      max_val: 1.0,
    },
    cost: {
      avg: 0.05,
      p50: 0.04,
      p95: 0.12,
      std_dev: 0.02,
      min_val: 0.01,
      max_val: 0.15,
    },
  };

  it("renders statistics cards", () => {
    render(<AggregationView statistics={mockStats} />);
    expect(screen.getByText("总计")).toBeInTheDocument();
    expect(screen.getByText("通过")).toBeInTheDocument();
    expect(screen.getByText("失败")).toBeInTheDocument();
  });

  it("shows pass rate", () => {
    render(<AggregationView statistics={mockStats} />);
    expect(screen.getByText("80%")).toBeInTheDocument();
  });

  it("shows latency P50/P95", () => {
    render(<AggregationView statistics={mockStats} />);
    // P50/P95 在多个指标卡片中重复出现
    const p50Elements = screen.getAllByText("P50");
    expect(p50Elements.length).toBeGreaterThanOrEqual(1);
    const p95Elements = screen.getAllByText("P95");
    expect(p95Elements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders total cases count", () => {
    render(<AggregationView statistics={mockStats} />);
    expect(screen.getByText("10")).toBeInTheDocument();
  });
});

describe("ExperimentCompare", () => {
  const mockProps = {
    experimentId: "exp-1",
    runA: {
      id: "run-a",
      statistics: {
        total_cases: 10,
        passed: 8,
        failed: 2,
        pass_rate: 0.8,
        latency: {
          avg: 1200,
          p50: 1000,
          p95: 2500,
          std_dev: 300,
          min_val: 500,
          max_val: 3000,
        },
        score: {
          avg: 0.82,
          p50: 0.85,
          p95: 0.65,
          std_dev: 0.12,
          min_val: 0.5,
          max_val: 1.0,
        },
        cost: {
          avg: 0.05,
          p50: 0.04,
          p95: 0.12,
          std_dev: 0.02,
          min_val: 0.01,
          max_val: 0.15,
        },
      },
    },
    runB: {
      id: "run-b",
      statistics: {
        total_cases: 10,
        passed: 7,
        failed: 3,
        pass_rate: 0.7,
        latency: {
          avg: 1500,
          p50: 1200,
          p95: 3000,
          std_dev: 400,
          min_val: 600,
          max_val: 4000,
        },
        score: {
          avg: 0.75,
          p50: 0.78,
          p95: 0.55,
          std_dev: 0.15,
          min_val: 0.4,
          max_val: 1.0,
        },
        cost: {
          avg: 0.06,
          p50: 0.05,
          p95: 0.15,
          std_dev: 0.03,
          min_val: 0.02,
          max_val: 0.2,
        },
      },
    },
    degradations: [
      {
        case_id: "tc1",
        metric: "score",
        baseline: 0.9,
        current: 0.5,
        change: -0.44,
      },
    ],
  };

  it("renders experiment title", () => {
    render(<ExperimentCompare {...mockProps} />);
    expect(screen.getByText("实验对比结果")).toBeInTheDocument();
  });

  it("shows run IDs", () => {
    render(<ExperimentCompare {...mockProps} />);
    expect(screen.getByText("run-a")).toBeInTheDocument();
    expect(screen.getByText("run-b")).toBeInTheDocument();
  });

  it("renders degradation section", () => {
    render(<ExperimentCompare {...mockProps} />);
    expect(screen.getByText("退化项")).toBeInTheDocument();
  });

  it("links comparison result to runs and release gates", () => {
    render(<ExperimentCompare {...mockProps} projectId="project-1" />);
    expect(screen.getByRole("link", { name: "查看运行结果" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
    expect(screen.getByRole("link", { name: "配置发布门禁" })).toHaveAttribute(
      "href",
      "/projects/project-1/gates",
    );
  });
});
