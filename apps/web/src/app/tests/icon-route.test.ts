import { describe, expect, it } from "vitest";

import Icon, { alt, contentType, size } from "../icon";

describe("app icon", () => {
  it("serves the 3D Warmy Agent Test brand mark as favicon metadata", () => {
    expect(alt).toBe("Warmy Agent Test 3D logo");
    expect(contentType).toBe("image/png");
    expect(size).toEqual({ height: 32, width: 32 });
    expect(Icon).toEqual(expect.any(Function));
  });
});
