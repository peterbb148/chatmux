import { useEffect, useState, useCallback } from 'react'
import { websocketService } from '../services/websocket'

interface StreamingMessage {
  modelId: number
  content: string
  isComplete: boolean
  error?: string
}

// Create a flag to track if we've already connected
let isConnected = false

export const useWebSocket = () => {
  const [connected, setConnected] = useState(false)
  const [streamingMessages, setStreamingMessages] = useState<{ [key: number]: StreamingMessage }>({})

  useEffect(() => {
    // Only connect if we haven't already
    if (!isConnected) {
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
      websocketService.connect(wsUrl)
      isConnected = true
    }

    // Set up message handler
    const unsubscribeMessage = websocketService.onMessage((message) => {
      console.log('useWebSocket received message:', message)

      // Handle both direct model_id and nested data.model_id
      const modelId = message.model_id || message.data?.model_id
      if (!modelId && message.type !== 'stream_chunk') return

      switch (message.type) {
        case 'stream_start':
          if (modelId) {
            setStreamingMessages(prev => ({
              ...prev,
              [modelId]: {
                modelId: modelId,
                content: '',
                isComplete: false
              }
            }))
          }
          break

        case 'stream_chunk':
          if (message.data) {
            setStreamingMessages(prev => {
              const existing = prev[message.data!.model_id]
              if (existing) {
                return {
                  ...prev,
                  [message.data!.model_id]: {
                    ...existing,
                    content: existing.content + message.data!.content,
                    isComplete: false
                  }
                }
              }
              return prev
            })
          }
          break

        case 'stream_end':
          if (modelId) {
            setStreamingMessages(prev => {
              const existing = prev[modelId]
              if (existing) {
                return {
                  ...prev,
                  [modelId]: {
                    ...existing,
                    isComplete: true
                  }
                }
              }
              return prev
            })
          }
          break

        case 'error':
          if (modelId) {
            setStreamingMessages(prev => ({
              ...prev,
              [modelId]: {
                modelId: modelId,
                content: '',
                isComplete: true,
                error: message.error
              }
            }))
          }
          break
      }
    })

    // Set up connection handler
    const unsubscribeConnection = websocketService.onConnectionChange(setConnected)

    // Handle clear streaming message events
    const handleClearStreamingMessage = (event: CustomEvent<{ modelId: number }>) => {
      setStreamingMessages(prev => {
        const newMessages = { ...prev }
        delete newMessages[event.detail.modelId]
        return newMessages
      })
    }

    window.addEventListener('clearStreamingMessage' as any, handleClearStreamingMessage as any)

    // Cleanup - but don't disconnect the singleton WebSocket
    return () => {
      unsubscribeMessage()
      unsubscribeConnection()
      window.removeEventListener('clearStreamingMessage' as any, handleClearStreamingMessage as any)
      // Don't disconnect here - let the singleton manage its own lifecycle
    }
  }, [])

  const sendMessage = useCallback((content: string, targets: number[] = []) => {
    // Clear previous messages when sending new one
    setStreamingMessages({})
    websocketService.sendMessage(content, targets)
  }, [])

  return {
    connected,
    sendMessage,
    streamingMessages
  }
}
