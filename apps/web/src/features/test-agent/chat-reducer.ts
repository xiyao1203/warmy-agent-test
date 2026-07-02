"use client";

import { useCallback, useReducer } from "react";

import type {
  AgentEvent,
  ArtifactLink,
  ChatMessage,
  ChatResponse,
  SessionSummary,
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
};

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
        ? localStorage.getItem("chat-sidebar-open") !== "false"
        : true,
    sidebarWidth:
      typeof window !== "undefined"
        ? Math.max(
            200,
            Math.min(480, Number(localStorage.getItem("chat-sidebar-width")) || 272),
          )
        : 272,
    isPinned: true,
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
  | { type: "SET_PINNED"; value: boolean };

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
        events: [],
        sessions: [s, ...state.sessions.filter((i) => i.session_id !== s.session_id)],
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
      };

    case "SET_MESSAGES":
      return { ...state, messages: action.messages };

    case "APPEND_MESSAGE":
      return { ...state, messages: [...state.messages, action.message] };

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
      const exists = state.events.some(
        (e) => e.id === action.event.id && e.type === action.event.type,
      );
      if (exists) return state;
      return { ...state, events: [...state.events, action.event] };
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
      return { ...state, streamingContent: state.streamingContent + action.content };

    case "CLEAR_STREAMING":
      return { ...state, streamingContent: "", reasoningStream: "" };

    case "SET_REASONING":
      return { ...state, reasoningStream: action.content };

    case "APPEND_REASONING":
      return { ...state, reasoningStream: state.reasoningStream + action.content };

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
        lastFailedInput: action.lastInput !== undefined ? action.lastInput : state.lastFailedInput,
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
      if (event.type === "agent.reasoning_delta") {
        dispatch({ type: "APPEND_REASONING", content: String(event.payload.content ?? "") });
      }
      if (event.type === "agent.reasoning") {
        dispatch({ type: "CLEAR_REASONING" });
      }
      if (event.type === "message.delta") {
        dispatch({ type: "APPEND_STREAMING", content: String(event.payload.content ?? "") });
      }
      // 流式完成：不等 POST 返回，立即结束光标闪烁（保留已显示内容）
      if (
        event.type === "message.completed" ||
        event.type === "agent.completed" ||
        event.type === "run.completed"
      ) {
        dispatch({ type: "CLEAR_REASONING" });
        dispatch({ type: "SET_STREAMING_ACTIVE", value: false });
      }
    },
    [dispatch],
  );

  return { state, dispatch, applySession, addSseEvent };
}
