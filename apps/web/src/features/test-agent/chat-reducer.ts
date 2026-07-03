"use client";

import { useCallback, useReducer } from "react";

import type {
  AgentEvent,
  ArtifactLink,
  ChatMessage,
  ChatResponse,
  SessionSummary,
  TimelineItem,
  ActiveGeneration,
} from "./api";

// ── State shape ───────────────────────────────────────────────────

export type ChatState = {
  workspace: "super" | "target";
  sessions: SessionSummary[];
  activeSession: ChatResponse | null;
  messages: ChatMessage[];
  artifacts: ArtifactLink[];
  events: AgentEvent[];
  streamingContent: string;
  reasoningStream: string;
  input: string;
  loadingHistory: boolean;
  loadingSession: boolean;
  sending: boolean;
  streamingActive: boolean;
  error: string | null;
  lastFailedInput: string | null;
  sidebarOpen: boolean;
  sidebarWidth: number;
  isPinned: boolean;
  timeline: TimelineItem[];
  eventCursor: number;
  activeGeneration: ActiveGeneration | null;
  connectionState: "connecting" | "ready" | "reconnecting" | "offline";
};

export function initialHistoryOpen(
  viewportWidth: number,
  storedPreference: string | null,
) {
  return viewportWidth >= 760 && storedPreference !== "false";
}

export function initialChatState(): ChatState {
  return {
    workspace: "super",
    sessions: [],
    activeSession: null,
    messages: [],
    artifacts: [],
    events: [],
    streamingContent: "",
    reasoningStream: "",
    input: "",
    loadingHistory: true,
    loadingSession: false,
    sending: false,
    streamingActive: false,
    error: null,
    lastFailedInput: null,
    sidebarOpen:
      typeof window !== "undefined"
        ? initialHistoryOpen(
            window.innerWidth,
            localStorage.getItem("chat-sidebar-open"),
          )
        : true,
    sidebarWidth:
      typeof window !== "undefined"
        ? Math.max(
            200,
            Math.min(
              480,
              Number(localStorage.getItem("chat-sidebar-width")) || 260,
            ),
          )
        : 260,
    isPinned: true,
    timeline: [],
    eventCursor: 0,
    activeGeneration: null,
    connectionState: "connecting",
  };
}

// ── Actions ──────────────────────────────────────────────────────

export type ChatAction =
  | { type: "SET_SESSIONS"; sessions: SessionSummary[] }
  | { type: "APPLY_SESSION"; session: ChatResponse }
  | { type: "CLEAR_SESSION" }
  | { type: "SET_MESSAGES"; messages: ChatMessage[] }
  | { type: "APPEND_MESSAGE"; message: ChatMessage }
  | { type: "REMOVE_LAST_USER_MESSAGE" }
  | { type: "REMOVE_LAST_ASSISTANT_MESSAGE" }
  | { type: "REPLACE_LAST_USER_MESSAGE"; content: string }
  | { type: "ADD_EVENT"; event: AgentEvent }
  | { type: "CLEAR_EVENTS" }
  | { type: "FILTER_EVENTS"; keepTypes: string[] }
  | { type: "SET_STREAMING"; content: string }
  | { type: "APPEND_STREAMING"; content: string }
  | { type: "CLEAR_STREAMING" }
  | { type: "SET_REASONING"; content: string }
  | { type: "APPEND_REASONING"; content: string }
  | { type: "CLEAR_REASONING" }
  | { type: "SET_INPUT"; value: string }
  | { type: "ADD_ARTIFACT"; artifact: ArtifactLink }
  | { type: "SET_SENDING"; value: boolean }
  | { type: "SET_STREAMING_ACTIVE"; value: boolean }
  | { type: "SET_ERROR"; error: string | null; lastInput?: string | null }
  | { type: "SET_WORKSPACE"; value: "super" | "target" }
  | { type: "SET_LOADING_HISTORY"; value: boolean }
  | { type: "SET_LOADING_SESSION"; value: boolean }
  | { type: "TOGGLE_SIDEBAR" }
  | { type: "SET_SIDEBAR_WIDTH"; width: number }
  | { type: "SET_PINNED"; value: boolean }
  | { type: "SET_CONNECTION"; value: ChatState["connectionState"] }
  | { type: "SET_ACTIVE_GENERATION"; value: ActiveGeneration | null }
  | {
      type: "COMMIT_STREAMING_MESSAGE";
      eventId: number;
      content: string;
      timestamp: string;
    };

// ── Reducer ──────────────────────────────────────────────────────

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "SET_SESSIONS":
      return { ...state, sessions: action.sessions };

    case "APPLY_SESSION": {
      const s = action.session;
      return {
        ...state,
        activeSession: s,
        messages: s.messages,
        artifacts: s.artifacts,
        streamingContent: "",
        reasoningStream: "",
        streamingActive: false,
        events: (s.timeline ?? [])
          .filter((item) => item.kind === "event")
          .map((item) => ({
            id: item.event_sequence,
            type: item.event_type,
            payload: item.payload,
          })),
        timeline:
          s.timeline ??
          s.messages.map((message, index) => ({
            kind: "message" as const,
            id: message.message_id ?? `message-${index}-${message.timestamp}`,
            timestamp: message.timestamp,
            role: message.role,
            content: message.content,
            sequence: message.sequence ?? index + 1,
          })),
        eventCursor: s.event_cursor ?? 0,
        activeGeneration: s.active_generation ?? null,
        sessions: [
          s,
          ...state.sessions.filter((i) => i.session_id !== s.session_id),
        ],
      };
    }

    case "CLEAR_SESSION":
      return {
        ...state,
        activeSession: null,
        messages: [],
        artifacts: [],
        events: [],
        streamingContent: "",
        reasoningStream: "",
        timeline: [],
        eventCursor: 0,
        activeGeneration: null,
      };

    case "SET_MESSAGES":
      return { ...state, messages: action.messages };

    case "APPEND_MESSAGE":
      return {
        ...state,
        messages: [...state.messages, action.message],
        timeline: [
          ...state.timeline,
          {
            kind: "message",
            id:
              action.message.message_id ??
              `message-${state.timeline.length}-${action.message.timestamp}`,
            timestamp: action.message.timestamp,
            role: action.message.role,
            content: action.message.content,
            sequence: action.message.sequence ?? state.messages.length + 1,
          },
        ],
      };

    case "REMOVE_LAST_USER_MESSAGE": {
      const msgs = [...state.messages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === "user") {
          msgs.splice(i, 1);
          // Also remove subsequent assistant reply
          if (i < msgs.length && msgs[i].role === "assistant") {
            msgs.splice(i, 1);
          }
          break;
        }
      }
      return { ...state, messages: msgs };
    }

    case "REMOVE_LAST_ASSISTANT_MESSAGE": {
      const msgs = [...state.messages];
      if (msgs.length > 0 && msgs[msgs.length - 1].role === "assistant") {
        msgs.pop();
      }
      return { ...state, messages: msgs };
    }

    case "REPLACE_LAST_USER_MESSAGE": {
      const msgs = [...state.messages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === "user") {
          msgs[i] = { ...msgs[i], content: action.content };
          break;
        }
      }
      return { ...state, messages: msgs };
    }

    case "ADD_EVENT": {
      if (action.event.id > 0 && action.event.id <= state.eventCursor)
        return state;
      const exists = state.events.some(
        (e) => e.id === action.event.id && e.type === action.event.type,
      );
      if (exists) return state;
      const replayable = ![
        "message.delta",
        "agent.reasoning_delta",
        "stream.ready",
      ].includes(action.event.type);
      return {
        ...state,
        events: [...state.events, action.event],
        timeline: replayable
          ? [
              ...state.timeline,
              {
                kind: "event",
                id: `event-${action.event.id}`,
                timestamp: new Date().toISOString(),
                event_type: action.event.type,
                event_sequence: action.event.id,
                generation_id:
                  String(action.event.payload.generation_id ?? "") || null,
                payload: action.event.payload,
              },
            ]
          : state.timeline,
        eventCursor: Math.max(state.eventCursor, action.event.id),
      };
    }

    case "CLEAR_EVENTS":
      return { ...state, events: [] };

    case "FILTER_EVENTS":
      return {
        ...state,
        events: state.events.filter((e) => action.keepTypes.includes(e.type)),
      };

    case "SET_STREAMING":
      return { ...state, streamingContent: action.content };

    case "APPEND_STREAMING":
      return {
        ...state,
        streamingContent: state.streamingContent + action.content,
      };

    case "CLEAR_STREAMING":
      return { ...state, streamingContent: "", reasoningStream: "" };

    case "SET_REASONING":
      return { ...state, reasoningStream: action.content };

    case "APPEND_REASONING":
      return {
        ...state,
        reasoningStream: state.reasoningStream + action.content,
      };

    case "CLEAR_REASONING":
      return { ...state, reasoningStream: "" };

    case "SET_INPUT":
      return { ...state, input: action.value };

    case "ADD_ARTIFACT": {
      const exists = state.artifacts.some(
        (a) => a.type === action.artifact.type && a.id === action.artifact.id,
      );
      if (exists) return state;
      return { ...state, artifacts: [...state.artifacts, action.artifact] };
    }

    case "SET_SENDING":
      return { ...state, sending: action.value };

    case "SET_STREAMING_ACTIVE":
      return { ...state, streamingActive: action.value };

    case "SET_ERROR":
      return {
        ...state,
        error: action.error,
        lastFailedInput:
          action.lastInput !== undefined
            ? action.lastInput
            : state.lastFailedInput,
      };

    case "SET_WORKSPACE":
      return { ...state, workspace: action.value };

    case "SET_LOADING_HISTORY":
      return { ...state, loadingHistory: action.value };

    case "SET_LOADING_SESSION":
      return { ...state, loadingSession: action.value };

    case "TOGGLE_SIDEBAR": {
      const next = !state.sidebarOpen;
      if (typeof window !== "undefined") {
        localStorage.setItem("chat-sidebar-open", String(next));
      }
      return { ...state, sidebarOpen: next };
    }

    case "SET_SIDEBAR_WIDTH": {
      if (typeof window !== "undefined") {
        localStorage.setItem("chat-sidebar-width", String(action.width));
      }
      return { ...state, sidebarWidth: action.width };
    }

    case "SET_PINNED":
      return { ...state, isPinned: action.value };

    case "SET_CONNECTION":
      return { ...state, connectionState: action.value };

    case "SET_ACTIVE_GENERATION":
      return { ...state, activeGeneration: action.value };

    case "COMMIT_STREAMING_MESSAGE": {
      const id = `message-event-${action.eventId}`;
      if (state.timeline.some((item) => item.id === id)) return state;
      const content = action.content.trim();
      if (!content) {
        return {
          ...state,
          streamingContent: "",
          streamingActive: false,
        };
      }
      const lastMessage = state.messages[state.messages.length - 1];
      if (
        lastMessage?.role === "assistant" &&
        lastMessage.content.trim() === content &&
        state.streamingContent === ""
      ) {
        return {
          ...state,
          streamingActive: false,
        };
      }
      const message: ChatMessage = {
        role: "assistant",
        content,
        timestamp: action.timestamp,
      };
      return {
        ...state,
        messages: [...state.messages, message],
        timeline: [
          ...state.timeline,
          {
            kind: "message",
            id,
            timestamp: action.timestamp,
            role: "assistant",
            content,
            sequence: state.messages.length + 1,
          },
        ],
        streamingContent: "",
        streamingActive: false,
      };
    }

    default:
      return state;
  }
}

// ── Hook ─────────────────────────────────────────────────────────

export function useChatReducer() {
  const [state, dispatch] = useReducer(chatReducer, null, initialChatState);

  const applySession = useCallback(
    (session: ChatResponse) => {
      dispatch({ type: "APPLY_SESSION", session });
      if (typeof window !== "undefined") {
        window.history.replaceState(
          {},
          "",
          `${window.location.pathname}?session=${session.session_id}`,
        );
      }
    },
    [dispatch],
  );

  const addSseEvent = useCallback(
    (event: AgentEvent) => {
      dispatch({ type: "ADD_EVENT", event });
      if (event.type === "asset.created") {
        dispatch({
          type: "ADD_ARTIFACT",
          artifact: {
            type: String(event.payload.type),
            id: String(event.payload.id),
            relation: String(event.payload.relation ?? "created"),
          },
        });
      }
      if (event.type === "message.started") {
        dispatch({ type: "CLEAR_STREAMING" });
      }
      if (event.type === "generation.started") {
        dispatch({
          type: "SET_ACTIVE_GENERATION",
          value: {
            generation_id: String(event.payload.generation_id ?? ""),
            status: "running",
            partial_content: "",
            workflow_id: String(event.payload.workflow_id ?? "") || null,
          },
        });
      }
      if (event.type === "agent.reasoning_delta") {
        dispatch({
          type: "APPEND_REASONING",
          content: String(event.payload.content ?? ""),
        });
      }
      if (event.type === "agent.reasoning") {
        dispatch({ type: "CLEAR_REASONING" });
      }
      if (event.type === "message.delta") {
        dispatch({
          type: "APPEND_STREAMING",
          content: String(event.payload.content ?? ""),
        });
      }
      // 流式完成：不等 POST 返回，立即结束光标闪烁（保留已显示内容）
      if (
        event.type === "message.completed" ||
        event.type === "agent.completed" ||
        event.type === "run.completed"
      ) {
        dispatch({ type: "SET_STREAMING_ACTIVE", value: false });
      }
      if (event.type === "message.completed") {
        dispatch({
          type: "COMMIT_STREAMING_MESSAGE",
          eventId: event.id,
          content: String(event.payload.content ?? ""),
          timestamp: new Date().toISOString(),
        });
      }
      if (
        event.type === "generation.completed" ||
        event.type === "generation.cancelled" ||
        event.type === "generation.failed"
      ) {
        dispatch({ type: "SET_ACTIVE_GENERATION", value: null });
      }
    },
    [dispatch],
  );

  return { state, dispatch, applySession, addSseEvent };
}
