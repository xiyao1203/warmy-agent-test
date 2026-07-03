import { afterEach, describe, expect, it, vi } from "vitest";

import { subscribeToSession } from "../api";

class EventSourceStub {
  static instance: EventSourceStub | null = null;
  readonly listeners = new Map<string, EventListenerOrEventListenerObject>();
  onerror: (() => void) | null = null;

  constructor(
    readonly url: string | URL,
    readonly options?: EventSourceInit,
  ) {
    EventSourceStub.instance = this;
  }

  addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
    this.listeners.set(type, listener);
  }

  close = vi.fn();
}

describe("test agent event stream", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("subscribes to generation lifecycle events used by cancel and recovery", () => {
    vi.stubGlobal("EventSource", EventSourceStub);

    subscribeToSession("project-1", "session-1", vi.fn());

    expect([...EventSourceStub.instance!.listeners.keys()]).toEqual(
      expect.arrayContaining([
        "generation.started",
        "generation.completed",
        "generation.cancelled",
        "generation.failed",
      ]),
    );
  });
});
