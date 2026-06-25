import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from "./dialog";
import { Input } from "./input";

describe("Dialog", () => {
  it("manages focus when opened and closed", async () => {
    render(
      <Dialog>
        <DialogTrigger>创建用户</DialogTrigger>
        <DialogContent>
          <DialogTitle>创建用户</DialogTitle>
          <Input aria-label="邮箱" autoFocus />
          <DialogClose>取消</DialogClose>
        </DialogContent>
      </Dialog>,
    );

    const trigger = screen.getByRole("button", { name: "创建用户" });
    fireEvent.click(trigger);

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "邮箱" })).toHaveFocus();

    fireEvent.click(screen.getByRole("button", { name: "取消" }));
    await waitFor(() => expect(trigger).toHaveFocus());
  });
});
