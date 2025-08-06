interface WebSocketMessage {
  type: 'stream_start' | 'stream_chunk' | 'stream_end' | 'error'
  model_id?: number
  model_name?: string
  provider?: string
  timestamp?: string
  data?: {
    model_id: number
    model_name: string
    provider: string
    content: string
    is_complete: boolean
    timestamp: string
  }
  error?: string
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectInterval = 5000
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  private messageHandlers: ((message: WebSocketMessage) => void)[] = []
  private connectionHandlers: ((connected: boolean) => void)[] = []

  connect(url: string) {
    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout)
          this.reconnectTimeout = null
        }
        this.notifyConnectionHandlers(true)
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.notifyMessageHandlers(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.notifyConnectionHandlers(false)
        this.scheduleReconnect(url)
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
      this.scheduleReconnect(url)
    }
  }

  private scheduleReconnect(url: string) {
    if (this.reconnectTimeout) return

    this.reconnectTimeout = setTimeout(() => {
      console.log('Attempting to reconnect...')
      this.connect(url)
    }, this.reconnectInterval)
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  sendMessage(content: string, targets: number[] = []) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected')
      return
    }

    const message = {
      content,
      targets,
      user_id: 'web-user'
    }

    this.ws.send(JSON.stringify(message))
  }

  onMessage(handler: (message: WebSocketMessage) => void) {
    this.messageHandlers.push(handler)

    // Return unsubscribe function
    return () => {
      const index = this.messageHandlers.indexOf(handler)
      if (index > -1) {
        this.messageHandlers.splice(index, 1)
      }
    }
  }

  onConnectionChange(handler: (connected: boolean) => void) {
    this.connectionHandlers.push(handler)

    // Return unsubscribe function
    return () => {
      const index = this.connectionHandlers.indexOf(handler)
      if (index > -1) {
        this.connectionHandlers.splice(index, 1)
      }
    }
  }

  private notifyMessageHandlers(message: WebSocketMessage) {
    this.messageHandlers.forEach(handler => handler(message))
  }

  private notifyConnectionHandlers(connected: boolean) {
    this.connectionHandlers.forEach(handler => handler(connected))
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

// Create singleton instance
export const websocketService = new WebSocketService()
