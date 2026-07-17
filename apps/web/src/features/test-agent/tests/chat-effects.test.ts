import { afterEach, describe, expect, it, vi } from "vitest";

import { createGenerationStreamController } from "../chat-effects";

type Event = { id: number; value: string };

describe("generation stream controller", () => {
  afterEach(() => vi.useRealTimers());

  it("opens one stream and closes it when generation changes", () => {
    const closes = [vi.fn(), vi.fn()];
    const factory = vi
      .fn()
      .mockImplementationOnce(() => closes[0])
      .mockImplementationOnce(() => closes[1]);
    const controller = createGenerationStreamController<Event>(factory, {
      cursorFor: (event) => event.id,
    });

    controller.connect("generation-1", vi.fn());
    controller.connect("generation-1", vi.fn());
    expect(factory).toHaveBeenCalledTimes(1);

    controller.connect("generation-2", vi.fn());
    expect(closes[0]).toHaveBeenCalledOnce();
    expect(factory).toHaveBeenCalledTimes(2);
  });

  it("cleans retry timers when disconnected", () => {
    vi.useFakeTimers();
    let fail: (() => void) | undefined;
    const factory = vi.fn((_key, _event, onError) => {
      fail = onError;
      return vi.fn();
    });
    const controller = createGenerationStreamController<Event>(factory, {
      retryDelayMs: 1000,
    });

    controller.connect("generation-1", vi.fn());
    fail?.();
    controller.disconnect();
    vi.advanceTimersByTime(1000);

    expect(factory).toHaveBeenCalledTimes(1);
  });

  it("preserves the latest cursor when reconnecting", () => {
    vi.useFakeTimers();
    let emit: ((event: Event) => void) | undefined;
    let fail: (() => void) | undefined;
    const factory = vi.fn((_key, onEvent, onError) => {
      emit = onEvent;
      fail = onError;
      return vi.fn();
    });
    const controller = createGenerationStreamController<Event>(factory, {
      cursorFor: (event) => event.id,
      retryDelayMs: 10,
    });

    controller.connect("generation-1", vi.fn(), vi.fn(), 4);
    emit?.({ id: 9, value: "delta" });
    fail?.();
    vi.advanceTimersByTime(10);

    expect(factory).toHaveBeenLastCalledWith(
      "generation-1",
      expect.any(Function),
      expect.any(Function),
      9,
    );
  });
});
