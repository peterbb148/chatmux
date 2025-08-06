import React, { createContext, useContext } from 'react'
import type { ReactNode } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'

interface StreamingMessage {
  modelId: number
  content: string
  isComplete: boolean
  error?: string
}

interface WebSocketContextType {
  connected: boolean
  sendMessage: (content: string, targets?: number[]) => void
  getMessageForModel: (modelId: number) => StreamingMessage | null
}

const WebSocketContext = createContext<WebSocketContextType | null>(null)

export const WebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const websocket = useWebSocket()

  return (
    <WebSocketContext.Provider value={websocket}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  }
  return context
}
