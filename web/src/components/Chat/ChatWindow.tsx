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
  const [isCopied, setIsCopied] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const windowRef = useRef<HTMLDivElement>(null)
  const { registerShortcut } = useKeyboardShortcutsContext()
  const { streamingMessages } = useWebSocketContext()
  const { focusedWindowId, setFocusedWindowId, clearChat } = useAppState()

  const isFocused = focusedWindowId === id
  const streamingMessage = streamingMessages[id]
  const isStreaming = streamingMessage && !streamingMessage.isComplete

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages.length, streamingMessage?.content])

  // Register keyboard shortcuts for this window
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
          setIsCopied(true)
          setTimeout(() => setIsCopied(false), 2000)
        }
      }
    })

    return unsubscribe
  }, [isFocused, registerShortcut, messages, modelName, id])

  // Add user message immediately when sent
  useEffect(() => {
    const handleUserMessage = (event: CustomEvent<{ content: string; targets?: string[] }>) => {
      // Only add message if this window is targeted (or no specific targets)
      const isTargeted = !event.detail.targets ||
                        event.detail.targets.length === 0 ||
                        event.detail.targets.includes(id)

      if (isTargeted) {
        setMessages(prev => {
          const newMessages = [...prev, {
            role: 'user',
            content: event.detail.content,
            timestamp: new Date()
          }]
          return newMessages
        })
      }
    }

    window.addEventListener('userMessageSent' as any, handleUserMessage as any)
    return () => {
      window.removeEventListener('userMessageSent' as any, handleUserMessage as any)
    }
  }, [id])

  // Add completed streaming message to messages array
  useEffect(() => {
    if (streamingMessage && streamingMessage.isComplete && streamingMessage.content) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: streamingMessage.content,
        timestamp: new Date()
      }])

      // Clear this streaming message from the context
      const event = new CustomEvent('clearStreamingMessage', { detail: { modelId: id } })
      window.dispatchEvent(event)
    }
  }, [streamingMessage?.isComplete, streamingMessage?.content, id])

  // Handle clear chat events
  useEffect(() => {
    const handleClearChat = () => {
      if (focusedWindowId === id || focusedWindowId === null) {
        setMessages([])
      }
    }

    const unsubscribe = clearChat.subscribe(handleClearChat)
    return unsubscribe
  }, [clearChat, focusedWindowId, id])

  return (
    <div
      ref={windowRef}
      className="bg-white rounded-2xl flex flex-col h-full overflow-hidden shadow-sm border border-gray-200"
      onClick={() => setFocusedWindowId(id)}
      style={{
        boxShadow: isFocused ? '0 0 0 2px #007AFF' : '0 1px 3px rgba(0,0,0,0.1)'
      }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-semibold px-2 py-1 rounded-full"
            style={{
              backgroundColor: isFocused ? '#007AFF' : '#E5E5EA',
              color: isFocused ? '#FFFFFF' : '#8E8E93'
            }}
          >
            {id}
          </span>
          <span className="text-sm font-medium text-gray-800">{modelName}</span>
        </div>
        <div className="flex items-center gap-2">
          {isCopied && (
            <span className="text-xs text-green-600">Copied!</span>
          )}
          {isStreaming && (
            <span className="text-xs text-gray-500">Typing...</span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4" style={{ backgroundColor: '#FFFFFF' }}>
        {messages.length === 0 && !streamingMessage ? (
          <div className="text-center text-gray-400 text-sm mt-8">
            No messages yet
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((message, index) => {
              const isLastUserMessage = message.role === 'user' &&
                (index === messages.length - 1 || messages[index + 1]?.role !== 'user')

              return (
                <div
                  key={`${index}-${message.timestamp.getTime()}`}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className="max-w-[70%]">
                    <div
                      className="px-4 py-2 rounded-2xl text-sm break-words"
                      style={{
                        backgroundColor: message.role === 'user' ? '#007AFF' : '#E5E5EA',
                        color: message.role === 'user' ? '#FFFFFF' : '#000000',
                        borderBottomRightRadius: message.role === 'user' && isLastUserMessage ? '4px' : '16px',
                        borderBottomLeftRadius: message.role === 'assistant' && index === messages.length - 1 ? '4px' : '16px',
                        wordBreak: 'break-word',
                        overflowWrap: 'break-word'
                      }}
                    >
                      <ReactMarkdown
                        components={{
                          p: ({children}) => <p style={{margin: 0}}>{children}</p>,
                          code: ({children}) => (
                            <code style={{
                              backgroundColor: 'rgba(0,0,0,0.1)',
                              padding: '2px 4px',
                              borderRadius: '4px',
                              fontSize: '0.9em'
                            }}>{children}</code>
                          )
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                    {isLastUserMessage && (
                      <div className="text-xs text-gray-500 mt-1 text-right pr-1">
                        Delivered
                      </div>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Streaming message */}
            {streamingMessage && (
              <div className="flex justify-start">
                <div className="max-w-[70%]">
                  <div
                    className="px-4 py-2 rounded-2xl text-sm break-words"
                    style={{
                      backgroundColor: '#E5E5EA',
                      color: '#000000',
                      borderBottomLeftRadius: '4px',
                      wordBreak: 'break-word',
                      overflowWrap: 'break-word'
                    }}
                  >
                    {streamingMessage.error ? (
                      <span style={{ color: '#FF3B30' }}>Error: {streamingMessage.error}</span>
                    ) : (
                      <>
                        <ReactMarkdown
                          components={{
                            p: ({children}) => <p style={{margin: 0}}>{children}</p>,
                            code: ({children}) => (
                              <code style={{
                                backgroundColor: 'rgba(0,0,0,0.1)',
                                padding: '2px 4px',
                                borderRadius: '4px',
                                fontSize: '0.9em'
                              }}>{children}</code>
                            )
                          }}
                        >
                          {streamingMessage.content || ''}
                        </ReactMarkdown>
                        {isStreaming && (
                          <span className="inline-block ml-1">
                            <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-pulse mx-0.5"></span>
                            <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-pulse mx-0.5" style={{animationDelay: '200ms'}}></span>
                            <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-pulse mx-0.5" style={{animationDelay: '400ms'}}></span>
                          </span>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
})

export default ChatWindow
