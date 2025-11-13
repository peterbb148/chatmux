import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useWebSocketContext } from '../../contexts/WebSocketContext'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'
import { useAppState } from '../../contexts/AppStateContext'

interface ChatWindowProps {
  id: number
  modelName: string
  provider: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const ChatWindow: React.FC<ChatWindowProps> = React.memo(({ id, modelName }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const windowRef = useRef<HTMLDivElement>(null)
  const { registerShortcut } = useKeyboardShortcutsContext()
  const { streamingMessages } = useWebSocketContext()
  const { focusedWindowId, setFocusedWindowId, registerClearHandler, unregisterClearHandler } = useAppState()

  const isFocused = focusedWindowId === id
  const streamingMessage = streamingMessages[id]

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages.length, streamingMessage?.content])

  useEffect(() => {
    const unsubscribe = registerShortcut({
      key: 'c',
      ctrl: true,
      cmd: true,
      description: `Copy messages from window ${id}`,
      handler: () => {
        if (isFocused && messages.length > 0) {
          const text = messages
            .map(m => `${m.role === 'user' ? 'You' : modelName}: ${m.content}`)
            .join('\n\n')
          navigator.clipboard.writeText(text)
        }
      }
    })

    return unsubscribe
  }, [isFocused, registerShortcut, messages, modelName, id])

  useEffect(() => {
    const handleUserMessage = (event: CustomEvent<{ content: string; targets?: string[] }>) => {
      const isTargeted = !event.detail.targets ||
                        event.detail.targets.length === 0 ||
                        event.detail.targets.includes(String(id))

      if (isTargeted) {
        setMessages(prev => [...prev, {
          role: 'user' as const,
          content: event.detail.content,
          timestamp: new Date()
        }])
      }
    }

    window.addEventListener('userMessageSent' as any, handleUserMessage as any)
    return () => {
      window.removeEventListener('userMessageSent' as any, handleUserMessage as any)
    }
  }, [id])

  useEffect(() => {
    if (streamingMessage && streamingMessage.isComplete && streamingMessage.content) {
      setMessages(prev => [...prev, {
        role: 'assistant' as const,
        content: streamingMessage.content,
        timestamp: new Date()
      }])

      const event = new CustomEvent('clearStreamingMessage', { detail: { modelId: id } })
      window.dispatchEvent(event)
    }
  }, [streamingMessage?.isComplete, streamingMessage?.content, id])

  useEffect(() => {
    const handleClearChat = () => {
      setMessages([])
    }

    registerClearHandler(id, handleClearChat)
    return () => unregisterClearHandler(id)
  }, [id, registerClearHandler, unregisterClearHandler])

  useEffect(() => {
    const handleClearSpecificChat = (event: CustomEvent<{ windowId: number }>) => {
      if (event.detail.windowId === id) {
        setMessages([])
      }
    }

    window.addEventListener('clearSpecificChat' as any, handleClearSpecificChat as any)
    return () => {
      window.removeEventListener('clearSpecificChat' as any, handleClearSpecificChat as any)
    }
  }, [id])

  return (
    <div
      ref={windowRef}
      className="h-full flex flex-col"
      onClick={() => setFocusedWindowId(id)}
      style={{
        backgroundColor: '#ffffff',
        borderRight: '1px solid #e5e5e5',
        borderRadius: '12px',
        margin: '8px',
        overflow: 'hidden',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}
    >
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #e5e5e5',
        backgroundColor: '#fafafa',
        borderTopLeftRadius: '12px',
        borderTopRightRadius: '12px'
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '14px',
          fontWeight: 600,
          color: '#000000'
        }}>{modelName}</h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto" style={{ backgroundColor: '#ffffff' }}>
        {messages.length === 0 && !streamingMessage ? (
          <div style={{
            textAlign: 'center',
            color: '#999',
            padding: '40px 20px',
            fontSize: '14px'
          }}>
            Start a conversation
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                style={{
                  padding: '16px 20px',
                  backgroundColor: 'transparent'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: '12px'
                }}>
                  <div style={{
                    maxWidth: '70%',
                    backgroundColor: message.role === 'user' ? '#007AFF' : '#f0f0f0',
                    color: message.role === 'user' ? 'white' : '#2e2e2e',
                    padding: '10px 16px',
                    borderRadius: '18px',
                    fontSize: '15px',
                    lineHeight: '1.4',
                    wordBreak: 'break-word'
                  }}>
                    {message.role === 'user' ? (
                      <span>{message.content}</span>
                    ) : (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p style={{ margin: '0 0 8px 0' }}>{children}</p>,
                          code: ({ children, className }) => {
                            const isInline = !className
                            return isInline ? (
                              <code style={{
                                backgroundColor: 'rgba(0,0,0,0.05)',
                                color: '#2e2e2e',
                                padding: '2px 4px',
                                borderRadius: '3px',
                                fontSize: '14px'
                              }}>{children}</code>
                            ) : (
                              <pre style={{
                                backgroundColor: '#1e1e1e',
                                padding: '12px',
                                borderRadius: '8px',
                                overflowX: 'auto',
                                margin: '8px 0'
                              }}>
                                <code style={{ fontSize: '13px', color: '#ffffff' }}>{children}</code>
                              </pre>
                            )
                          }
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {streamingMessage && !streamingMessage.isComplete && (
              <div style={{
                padding: '16px 20px',
                backgroundColor: 'transparent'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'flex-start',
                  marginBottom: '12px'
                }}>
                  <div style={{
                    maxWidth: '70%',
                    backgroundColor: '#f0f0f0',
                    color: '#2e2e2e',
                    padding: '10px 16px',
                    borderRadius: '18px',
                    fontSize: '15px',
                    lineHeight: '1.4',
                    wordBreak: 'break-word'
                  }}>
                    <ReactMarkdown>
                      {streamingMessage.content || '●●●'}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  )
})

ChatWindow.displayName = 'ChatWindow'

export default ChatWindow
