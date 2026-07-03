import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { SessionList } from "../session-list";

test("uses an inline confirmation row instead of covering adjacent sessions", () => {
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

  fireEvent.click(screen.getByRole("button", { name: "删除 第一条会话" }));

  const confirmation = screen.getByRole("group", {
    name: "确认删除第一条会话",
  });
  expect(confirmation).toBeVisible();
  expect(confirmation.className).not.toContain("absolute");
  expect(screen.getByRole("button", { name: "第二条会话" })).toBeVisible();
});
