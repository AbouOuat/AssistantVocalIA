"use client";

export type WsMessageType =
  | "chat"
  | "voice_input"
  | "memory_set"
  | "memory_get"
  | "session_summary";

export type WsResponseType =
  | "stream_chunk"
  | "response"
  | "voice_response"
  | "tts"
  | "memory_ack"
  | "memory_data"
  | "session_summary";

export interface WsMessage {
  type: WsMessageType;
  content?: string;
  audio?: string;
  scope?: string;
  key?: string;
  value?: unknown;
}

export interface WsResponse {
  type: WsResponseType;
  content?: string;
  transcript?: string;
  audio?: string;
  scope?: string;
  key?: string;
  value?: unknown;
  summary?: string;
  voice_origin?: boolean;
}

type MessageHandler = (msg: WsResponse) => void;

const WS_URL_BASE =
  process.env.NEXT_PUBLIC_BACKEND_WS_URL ?? "ws://localhost:8090/ws";

export const BACKEND_HTTP_URL = WS_URL_BASE
  .replace(/^wss:\/\//, "https://")
  .replace(/^ws:\/\//, "http://")
  .replace(/\/ws$/, "");

class JarvisWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  public status: "connecting" | "connected" | "disconnected" = "disconnected";
  private token: string | null = null;

  async fetchToken() {
    try {
      const response = await fetch(`${BACKEND_HTTP_URL}/api/config`);
      const data = await response.json();
      this.token = data.token;
      return this.token;
    } catch (error) {
      console.error("[WS] Failed to fetch token", error);
      return null;
    }
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.status = "connecting";

    // Include token in WebSocket URL
    const wsUrl = this.token ? `${WS_URL_BASE}?token=${this.token}` : WS_URL_BASE;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.status = "connected";
      this.emit({ type: "response", content: "__connected__" } as WsResponse);
    };

    this.ws.onmessage = (event) => {
      try {
        const data: WsResponse = JSON.parse(event.data);
        this.emit(data);
      } catch {
        console.error("[WS] Parse error", event.data);
      }
    };

    this.ws.onclose = () => {
      this.status = "disconnected";
      this.emit({ type: "response", content: "__disconnected__" } as WsResponse);
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      }
    };

    this.ws.onerror = (e) => {
      console.error("[WS] Error", e);
    };
  }

  async ensureConnected() {
    if (!this.token) {
      await this.fetchToken();
    }
    if (this.status !== "connected") {
      this.connect();
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
  }

  send(msg: WsMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    } else {
      console.warn("[WS] Not connected, message dropped");
    }
  }

  on(handler: MessageHandler) {
    this.handlers.add(handler);
    if (this.ws?.readyState === WebSocket.OPEN) {
      handler({ type: "response", content: "__connected__" } as WsResponse);
    }
    return () => this.handlers.delete(handler);
  }

  private emit(msg: WsResponse) {
    this.handlers.forEach((h) => h(msg));
  }
}

// Singleton — une seule connexion pour toute l'app
export const jarvisWS = new JarvisWebSocket();
