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
  const [streamingMessages, setStreamingMessages] = useState<Map<number, StreamingMessage>>(new Map())

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
            setStreamingMessages(prev => {
              const newMap = new Map(prev)
              newMap.set(modelId, {
                modelId: modelId,
                content: '',
                isComplete: false
              })
              return newMap
            })
          }
          break

        case 'stream_chunk':
          if (message.data) {
            setStreamingMessages(prev => {
              const newMap = new Map(prev)
              const existing = newMap.get(message.data!.model_id)
              if (existing) {
                newMap.set(message.data!.model_id, {
                  ...existing,
                  content: existing.content + message.data!.content,
                  isComplete: false
                })
              }
              return newMap
            })
          }
          break

        case 'stream_end':
          if (modelId) {
            setStreamingMessages(prev => {
              const newMap = new Map(prev)
              const existing = newMap.get(modelId)
              if (existing) {
                newMap.set(modelId, {
                  ...existing,
                  isComplete: true
                })
              }
              return newMap
            })
          }
          break

        case 'error':
          if (modelId) {
            setStreamingMessages(prev => {
              const newMap = new Map(prev)
              newMap.set(modelId, {
                modelId: modelId,
                content: '',
                isComplete: true,
                error: message.error
              })
              return newMap
            })
          }
          break
      }
    })

    // Set up connection handler
    const unsubscribeConnection = websocketService.onConnectionChange(setConnected)

    // Cleanup - but don't disconnect the singleton WebSocket
    return () => {
      unsubscribeMessage()
      unsubscribeConnection()
      // Don't disconnect here - let the singleton manage its own lifecycle
    }
  }, [])

  const sendMessage = useCallback((content: string, targets: number[] = []) => {
    // Clear previous messages when sending new one
    setStreamingMessages(new Map())
    websocketService.sendMessage(content, targets)
  }, [])

  const getMessageForModel = useCallback((modelId: number): StreamingMessage | null => {
    return streamingMessages.get(modelId) || null
  }, [streamingMessages])

  const clearMessageForModel = useCallback((modelId: number) => {
    setStreamingMessages(prev => {
      const newMap = new Map(prev)
      newMap.delete(modelId)
      return newMap
    })
  }, [])

  return {
    connected,
    sendMessage,
    getMessageForModel,
    clearMessageForModel,
    streamingMessages
  }
}
