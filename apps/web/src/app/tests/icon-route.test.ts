import { describe, expect, it } from "vitest";

import Icon, { alt, contentType, size } from "../icon";

describe("app icon", () => {
  it("serves the Warmy Agent Test product mark as favicon metadata", () => {
    expect(alt).toBe("Warmy Agent Test product mark");
    expect(contentType).toBe("image/png");
    expect(size).toEqual({ height: 32, width: 32 });
    expect(Icon).toEqual(expect.any(Function));
  });
});
