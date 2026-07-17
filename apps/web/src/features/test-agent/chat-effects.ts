export type GenerationStreamFactory<Event> = (
  generationId: string,
  onEvent: (event: Event) => void,
  onError: () => void,
  cursor: number,
) => () => void;

export type GenerationStreamController<Event> = {
  connect: (
    generationId: string,
    onEvent: (event: Event) => void,
    onError?: () => void,
    cursor?: number,
  ) => () => void;
  disconnect: () => void;
  cursor: () => number;
};

type ControllerOptions<Event> = {
  cursorFor?: (event: Event) => number | undefined;
  retryDelayMs?: number;
};

export function createGenerationStreamController<Event>(
  factory: GenerationStreamFactory<Event>,
  options: ControllerOptions<Event> = {},
): GenerationStreamController<Event> {
  const listeners = new Set<(event: Event) => void>();
  const errorListeners = new Set<() => void>();
  let activeGeneration: string | null = null;
  let closeStream: (() => void) | null = null;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  let latestCursor = 0;

  const clearRetry = () => {
    if (retryTimer !== null) clearTimeout(retryTimer);
    retryTimer = null;
  };

  const close = () => {
    closeStream?.();
    closeStream = null;
  };

  const open = () => {
    if (!activeGeneration) return;
    close();
    const generation = activeGeneration;
    closeStream = factory(
      generation,
      (event) => {
        if (generation !== activeGeneration) return;
        const cursor = options.cursorFor?.(event);
        if (cursor !== undefined && Number.isFinite(cursor)) {
          latestCursor = Math.max(latestCursor, cursor);
        }
        for (const listener of listeners) listener(event);
      },
      () => {
        if (generation !== activeGeneration) return;
        close();
        for (const listener of errorListeners) listener();
        clearRetry();
        retryTimer = setTimeout(open, options.retryDelayMs ?? 1000);
      },
      latestCursor,
    );
  };

  const disconnect = () => {
    activeGeneration = null;
    clearRetry();
    close();
    listeners.clear();
    errorListeners.clear();
  };

  return {
    connect(generationId, onEvent, onError = () => undefined, cursor = 0) {
      if (activeGeneration !== generationId) {
        disconnect();
        activeGeneration = generationId;
        latestCursor = cursor;
      } else {
        latestCursor = Math.max(latestCursor, cursor);
      }
      listeners.add(onEvent);
      errorListeners.add(onError);
      if (!closeStream && retryTimer === null) open();
      return () => {
        listeners.delete(onEvent);
        errorListeners.delete(onError);
      };
    },
    disconnect,
    cursor: () => latestCursor,
  };
}
