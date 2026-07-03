import { render, waitFor } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import HomePage from "../page";

const { replace, useQuery } = vi.hoisted(() => ({
  replace: vi.fn(),
  useQuery: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));
vi.mock("@tanstack/react-query", () => ({ useQuery }));
vi.mock("@/features/auth", () => ({ getCurrentUser: vi.fn() }));

describe("HomePage navigation", () => {
  it("navigates after rendering instead of updating the router during render", async () => {
    useQuery.mockReturnValue({ isError: false, isSuccess: true });
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => undefined);
    let setRoute: (path: string) => void = () => undefined;
    replace.mockImplementation((path: string) => setRoute(path));

    function Harness() {
      const [, updateRoute] = useState("");
      setRoute = updateRoute;
      return <HomePage />;
    }

    render(<Harness />);

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/projects"));
    expect(
      consoleError.mock.calls.some((call) =>
        String(call[0]).includes("Cannot update a component"),
      ),
    ).toBe(false);
    consoleError.mockRestore();
  });
});
