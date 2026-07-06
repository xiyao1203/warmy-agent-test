import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReportDownloadButton } from "../report-download-button";

vi.mock("@/lib/api/base-url", () => ({
  CONTROL_API_URL: "",
}));

const fetchMock = vi.fn();
const originalCreateObjectURL = URL.createObjectURL;
const originalRevokeObjectURL = URL.revokeObjectURL;

describe("ReportDownloadButton", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: originalCreateObjectURL,
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: originalRevokeObjectURL,
    });
    fetchMock.mockReset();
  });

  it("downloads reports from the backend export endpoint", async () => {
    const appendChild = vi.spyOn(document.body, "appendChild");
    const removeChild = vi.spyOn(document.body, "removeChild");
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    vi.stubGlobal("fetch", fetchMock);
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:report"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    fetchMock.mockResolvedValue({
      blob: vi.fn().mockResolvedValue(new Blob(["{}"])),
      ok: true,
    });

    render(<ReportDownloadButton projectId="project-1" runId="run-1" />);

    fireEvent.click(screen.getByRole("button", { name: "下载报告" }));
    fireEvent.click(screen.getByRole("button", { name: /JSON/ }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/projects/project-1/runs/run-1/export?format=json",
        { credentials: "include" },
      ),
    );
    expect(appendChild).toHaveBeenCalled();
    expect(click).toHaveBeenCalled();
    expect(removeChild).toHaveBeenCalled();
  });
});
