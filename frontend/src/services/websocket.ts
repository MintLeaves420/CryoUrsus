type WebSocketEventHandler = (event: { type: string; data: any; timestamp: string }) => void;

export class ShipmentWebSocketClient {
  private ws: WebSocket | null = null;
  private shipmentId: string;
  private listeners: Set<WebSocketEventHandler> = new Set();
  private isIntentionalClose: boolean = false;
  private reconnectTimer: any = null;
  public isConnected: boolean = false;
  private onConnectionChange?: (connected: boolean) => void;

  constructor(shipmentId: string, onConnectionChange?: (connected: boolean) => void) {
    this.shipmentId = shipmentId;
    this.onConnectionChange = onConnectionChange;
  }

  public connect() {
    this.isIntentionalClose = false;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname === 'localhost' ? '127.0.0.1:8000' : window.location.host;
    const url = `${wsProtocol}//${host}/api/ws/shipments/${this.shipmentId}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.onConnectionChange?.(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.listeners.forEach((handler) => handler(payload));
        } catch (e) {
          console.warn('Failed to parse websocket message', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.onConnectionChange?.(false);
        if (!this.isIntentionalClose) {
          // Reconnect with backoff
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = setTimeout(() => this.connect(), 2000);
        }
      };

      this.ws.onerror = () => {
        this.isConnected = false;
        this.onConnectionChange?.(false);
      };
    } catch (e) {
      this.isConnected = false;
      this.onConnectionChange?.(false);
    }
  }

  public subscribe(handler: WebSocketEventHandler) {
    this.listeners.add(handler);
    return () => {
      this.listeners.delete(handler);
    };
  }

  public disconnect() {
    this.isIntentionalClose = true;
    clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.onConnectionChange?.(false);
  }
}
