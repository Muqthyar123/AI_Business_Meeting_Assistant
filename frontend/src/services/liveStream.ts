import { ENV } from '../config/environment';

export interface LiveStreamSegment {
  type: 'speech_segment' | 'pong' | string;
  text: string;
  timestamp?: string;
  mode?: 'meeting' | 'dictation' | string;
  segment_id?: number;
  received_at?: string;
}

export class LiveStreamClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: any = null;
  private isExplicitlyClosed = false;
  private listeners: Set<(segment: LiveStreamSegment) => void> = new Set();
  private statusListeners: Set<(connected: boolean) => void> = new Set();

  constructor() {
    this.connect();
  }

  public getWsUrl(): string {
    const base = ENV.API_BASE_URL.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://');
    return `${base}/api/stream/ws`;
  }

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    const url = this.getWsUrl();

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.notifyStatus(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data: LiveStreamSegment = JSON.parse(event.data);
          if (data && data.text) {
            this.listeners.forEach((listener) => {
              try {
                listener(data);
              } catch (err) {
                console.error('Error in live stream listener:', err);
              }
            });
          }
        } catch {
          // ignore non-json messages
        }
      };

      this.ws.onclose = () => {
        this.notifyStatus(false);
        this.ws = null;
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = () => {
        this.notifyStatus(false);
      };
    } catch {
      this.notifyStatus(false);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      if (!this.isExplicitlyClosed) {
        this.connect();
      }
    }, 3000);
  }

  private notifyStatus(connected: boolean): void {
    this.statusListeners.forEach((fn) => {
      try {
        fn(connected);
      } catch (err) {
        console.error('Error in live stream status listener:', err);
      }
    });
  }

  public subscribe(
    onSegment: (segment: LiveStreamSegment) => void,
    onStatusChange?: (connected: boolean) => void
  ): () => void {
    this.listeners.add(onSegment);
    if (onStatusChange) {
      this.statusListeners.add(onStatusChange);
      // Immediately report current status
      onStatusChange(this.isConnected());
    }

    return () => {
      this.listeners.delete(onSegment);
      if (onStatusChange) {
        this.statusListeners.delete(onStatusChange);
      }
    };
  }

  public isConnected(): boolean {
    return Boolean(this.ws && this.ws.readyState === WebSocket.OPEN);
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.notifyStatus(false);
  }
}

export const liveStreamClient = new LiveStreamClient();
