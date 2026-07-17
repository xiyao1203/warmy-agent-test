import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useCreateIntent } from "./use-create-intent";

const navigation = vi.hoisted(() => ({
  query: "",
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects/project-1/datasets",
  useRouter: () => ({ replace: navigation.replace }),
  useSearchParams: () => new URLSearchParams(navigation.query),
}));

function Harness() {
  const [open, setOpen] = useCreateIntent("dataset");
  return (
    <div>
      <span>{open ? "open" : "closed"}</span>
      <button onClick={() => setOpen(false)} type="button">
        close
      </button>
    </div>
  );
}

describe("useCreateIntent", () => {
  beforeEach(() => {
    navigation.query = "";
    navigation.replace.mockClear();
  });

  it("reacts to a same-route query update and consumes it when closed", async () => {
    const view = render(<Harness />);
    expect(screen.getByText("closed")).toBeInTheDocument();

    navigation.query = "create=dataset";
    view.rerender(<Harness />);
    await waitFor(() => expect(screen.getByText("open")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "close" }));
    expect(navigation.replace).toHaveBeenCalledWith(
      "/projects/project-1/datasets",
      { scroll: false },
    );
  });
});
