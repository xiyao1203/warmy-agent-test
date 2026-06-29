import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// Mock the API
vi.mock("../api", () => ({
  submitFeedback: vi.fn().mockResolvedValue({ id: "1" }),
}));

import { FeedbackForm } from "../feedback-form";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

function renderWithQueryClient(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("FeedbackForm", () => {
  it("renders the feedback form", () => {
    renderWithQueryClient(<FeedbackForm />);

    expect(screen.getByText("反馈类型")).toBeInTheDocument();
    expect(screen.getByLabelText("标题")).toBeInTheDocument();
    expect(screen.getByLabelText("详细描述")).toBeInTheDocument();
  });

  it("validates required fields before submitting", async () => {
    renderWithQueryClient(<FeedbackForm />);

    const submitButton = screen.getByRole("button", { name: "提交反馈" });
    fireEvent.click(submitButton);

    // HTML5 validation should prevent submission
    await waitFor(() => {
      expect(screen.queryByText("感谢您的反馈！")).not.toBeInTheDocument();
    });
  });

  it("shows success message after successful submission", async () => {
    const { submitFeedback } = await import("../api");
    renderWithQueryClient(<FeedbackForm />);

    // Fill in the form
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: "测试反馈标题" },
    });
    fireEvent.change(screen.getByLabelText("详细描述"), {
      target: { value: "这是一个测试反馈的详细描述内容" },
    });

    // Submit the form
    const submitButton = screen.getByRole("button", { name: "提交反馈" });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("感谢您的反馈！")).toBeInTheDocument();
    });

    expect(submitFeedback).toHaveBeenCalled();
  });

  it("shows error message when submission fails", async () => {
    const { submitFeedback } = await import("../api");
    vi.mocked(submitFeedback).mockRejectedValueOnce(new Error("Network error"));

    renderWithQueryClient(<FeedbackForm />);

    // Fill in the form
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: "测试反馈标题" },
    });
    fireEvent.change(screen.getByLabelText("详细描述"), {
      target: { value: "这是一个测试反馈的详细描述内容" },
    });

    // Submit the form
    const submitButton = screen.getByRole("button", { name: "提交反馈" });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("提交失败，请稍后重试。")).toBeInTheDocument();
    });
  });
});
