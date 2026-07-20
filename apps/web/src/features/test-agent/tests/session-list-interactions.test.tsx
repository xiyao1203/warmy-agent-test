import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { SessionList } from "../session-list";

test("confirms deletion in a ChatGPT-style modal", () => {
  render(
    <SessionList
      activeId={null}
      items={[
        {
          session_id: "session-1",
          title: "第一条会话",
          status: "active",
          updated_at: "2026-07-03T00:00:00Z",
        },
        {
          session_id: "session-2",
          title: "第二条会话",
          status: "active",
          updated_at: "2026-07-03T00:00:01Z",
        },
      ]}
      loading={false}
      onCreate={vi.fn()}
      onDelete={vi.fn()}
      onSelect={vi.fn()}
    />,
  );

  expect(
    document.querySelectorAll('[role="tooltip"][data-tooltip="删除"]'),
  ).toHaveLength(2);

  fireEvent.click(screen.getByRole("button", { name: "删除 第一条会话" }));

  expect(screen.getByRole("dialog")).toBeVisible();
  expect(screen.getByRole("heading", { name: "删除对话？" })).toBeVisible();
  expect(
    screen.getByText("此操作将永久删除“第一条会话”，且无法撤销。"),
  ).toBeVisible();
  expect(
    document.querySelector('[aria-label="第二条会话"]'),
  ).toBeInTheDocument();
});
