import React, { useEffect, useRef } from 'react'
import { useWebSocketContext } from '../../contexts/WebSocketContext'
import { useAppState } from '../../contexts/AppStateContext'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'

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

const ChatWindow: React.FC<ChatWindowProps> = ({ id, modelName, provider }) => {
  const [messages, setMessages] = React.useState<Message[]>([])
  const [userMessage, setUserMessage] = React.useState<string>('')
  const [isCopied, setIsCopied] = React.useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const windowRef = useRef<HTMLDivElement>(null)
  const { getMessageForModel } = useWebSocketContext()
  const { focusedWindowId, registerClearHandler, unregisterClearHandler } = useAppState()
  const { registerShortcut } = useKeyboardShortcutsContext()

  const isFocused = focusedWindowId === id

  const streamingMessage = getMessageForModel(id)
  const isStreaming = streamingMessage && !streamingMessage.isComplete

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  // Register clear handler
  useEffect(() => {
    const clearMessages = () => {
      setMessages([])
      setUserMessage('')
    }

    registerClearHandler(id, clearMessages)
    return () => unregisterClearHandler(id)
  }, [id, registerClearHandler, unregisterClearHandler])

  // Register copy shortcut when focused
  useEffect(() => {
    if (!isFocused) return

    const unsubscribe = registerShortcut({
      key: 'c',
      ctrl: true,
      cmd: true,
      description: 'Copy focused window content',
      handler: () => {
        const allContent = messages.map(m =>
          `${m.role === 'user' ? 'You' : modelName}: ${m.content}`
        ).join('\n\n')

        const currentStreaming = streamingMessage?.content || ''
        const fullContent = currentStreaming
          ? allContent + (allContent ? '\n\n' : '') + `${modelName}: ${currentStreaming}`
          : allContent

        if (fullContent) {
          navigator.clipboard.writeText(fullContent).then(() => {
            setIsCopied(true)
            setTimeout(() => setIsCopied(false), 2000)
          })
        }
      }
    })

    return unsubscribe
  }, [isFocused, registerShortcut, messages, modelName, streamingMessage])

  // Add user message when streaming starts
  useEffect(() => {
    if (streamingMessage && userMessage) {
      setMessages(prev => [...prev, {
        role: 'user',
        content: userMessage,
        timestamp: new Date()
      }])
      setUserMessage('')
    }
  }, [streamingMessage, userMessage])

  // Store user message temporarily when a new stream starts
  useEffect(() => {
    const handleUserMessage = (event: CustomEvent<{ content: string }>) => {
      setUserMessage(event.detail.content)
    }

    window.addEventListener('userMessageSent' as any, handleUserMessage as any)
    return () => {
      window.removeEventListener('userMessageSent' as any, handleUserMessage as any)
    }
  }, [])

  return (
    <div
      ref={windowRef}
      className={`bg-gray-800 rounded-lg border-2 flex flex-col h-full transition-all ${
        isFocused ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-gray-700'
      }`}
      onClick={() => {
        // Optional: click to focus
      }}
    >
      {/* Header */}
      <div className={`px-3 py-2 rounded-t-lg border-b flex justify-between items-center ${
        isFocused ? 'bg-blue-900/30 border-blue-600' : 'bg-gray-700 border-gray-600'
      }`}>
        <div>
          <h3 className="font-semibold flex items-center gap-2">
            <span className={`text-sm px-2 py-0.5 rounded ${
              isFocused ? 'bg-blue-600' : 'bg-gray-600'
            }`}>{id}</span>
            {modelName}
          </h3>
          <p className="text-xs text-gray-400">{provider}</p>
        </div>
        <div className="flex items-center gap-2">
          {isCopied && (
            <span className="text-xs text-green-400">Copied!</span>
          )}
          {isStreaming && (
            <span className="text-xs text-blue-400 animate-pulse">Thinking...</span>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && !streamingMessage ? (
          <p className="text-gray-500 text-sm text-center mt-4">
            Waiting for messages...
          </p>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`${
                  message.role === 'user'
                    ? 'bg-blue-900/30 ml-8'
                    : 'bg-gray-700/50 mr-8'
                } rounded-lg p-3`}
              >
                <div className="text-xs text-gray-400 mb-1">
                  {message.role === 'user' ? 'You' : modelName}
                </div>
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              </div>
            ))}

            {/* Streaming message */}
            {streamingMessage && (
              <div className="bg-gray-700/50 mr-8 rounded-lg p-3">
                <div className="text-xs text-gray-400 mb-1">{modelName}</div>
                <div className="text-sm whitespace-pre-wrap">
                  {streamingMessage.error ? (
                    <span className="text-red-400">Error: {streamingMessage.error}</span>
                  ) : (
                    <>
                      {streamingMessage.content}
                      {isStreaming && <span className="animate-pulse">▊</span>}
                    </>
                  )}
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

export default ChatWindow
