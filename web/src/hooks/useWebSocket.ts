import { useEffect, useState, useCallback } from 'react'
import { websocketService } from '../services/websocket'

interface StreamingMessage {
  modelId: number
  content: string
  isComplete: boolean
  error?: string
}

export const useWebSocket = () => {
  const [connected, setConnected] = useState(false)
  const [streamingMessages, setStreamingMessages] = useState<Map<number, StreamingMessage>>(new Map())

  useEffect(() => {
    // Connect to WebSocket
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
    websocketService.connect(wsUrl)

    // Set up message handler
    const unsubscribeMessage = websocketService.onMessage((message) => {
      if (!message.model_id) return

      switch (message.type) {
        case 'stream_start':
          setStreamingMessages(prev => {
            const newMap = new Map(prev)
            newMap.set(message.model_id!, {
              modelId: message.model_id!,
              content: '',
              isComplete: false
            })
            return newMap
          })
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
          setStreamingMessages(prev => {
            const newMap = new Map(prev)
            const existing = newMap.get(message.model_id!)
            if (existing) {
              newMap.set(message.model_id!, {
                ...existing,
                isComplete: true
              })
            }
            return newMap
          })
          break

        case 'error':
          setStreamingMessages(prev => {
            const newMap = new Map(prev)
            newMap.set(message.model_id!, {
              modelId: message.model_id!,
              content: '',
              isComplete: true,
              error: message.error
            })
            return newMap
          })
          break
      }
    })

    // Set up connection handler
    const unsubscribeConnection = websocketService.onConnectionChange(setConnected)

    // Cleanup
    return () => {
      unsubscribeMessage()
      unsubscribeConnection()
      websocketService.disconnect()
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

  return {
    connected,
    sendMessage,
    getMessageForModel,
    streamingMessages
  }
}
