import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfirmationCard } from "../confirmation-card";

const { decideConfirmation } = vi.hoisted(() => ({
  decideConfirmation: vi.fn(),
}));

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  decideConfirmation,
}));

const event = {
  id: 7,
  type: "tool.confirmation_required",
  payload: {
    confirmation_id: "confirmation-1",
    generation_id: "generation-1",
    preview: {
      child_agent: "execution",
      capability: "run_plan",
      risk: "DRAFT_WRITE",
      arguments: { project_id: "project-1" },
    },
  },
};

describe("ConfirmationCard", () => {
  it("keeps operation parameters collapsed until requested", () => {
    render(
      <ConfirmationCard
        event={event}
        onDecided={vi.fn()}
        projectId="project-1"
        sessionId="session-1"
      />,
    );

    expect(screen.queryByText("project_id")).not.toBeInTheDocument();
    const disclosure = screen.getByRole("button", { name: "查看参数" });
    expect(disclosure).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(disclosure);

    expect(disclosure).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("project_id")).toBeVisible();
  });

  it("shows which confirmation decision is in progress", async () => {
    let resolve!: () => void;
    decideConfirmation.mockReturnValueOnce(
      new Promise<void>((done) => {
        resolve = done;
      }),
    );
    render(
      <ConfirmationCard
        event={event}
        onDecided={vi.fn()}
        projectId="project-1"
        sessionId="session-1"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "拒绝" }));

    expect(screen.getByRole("button", { name: "正在拒绝" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "确认执行" })).toBeDisabled();
    resolve();
    await waitFor(() => expect(decideConfirmation).toHaveBeenCalled());
  });
});
