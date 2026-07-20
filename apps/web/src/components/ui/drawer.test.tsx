import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Drawer, DrawerContent, DrawerTitle, DrawerTrigger } from "./drawer";

describe("Drawer", () => {
  it("uses the shared spatial motion surface", async () => {
    render(
      <Drawer>
        <DrawerTrigger>查看详情</DrawerTrigger>
        <DrawerContent>
          <DrawerTitle>运行详情</DrawerTitle>
        </DrawerContent>
      </Drawer>,
    );

    fireEvent.click(screen.getByRole("button", { name: "查看详情" }));

    expect(await screen.findByRole("dialog")).toHaveClass(
      "precision-drawer-content",
    );
    expect(screen.getByRole("heading", { name: "运行详情" })).toBeVisible();
  });
});
