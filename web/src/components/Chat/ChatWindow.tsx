import React, { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
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

const ChatWindow: React.FC<ChatWindowProps> = ({ id, modelName }) => {
  const [messages, setMessages] = React.useState<Message[]>([])
  const [isCopied, setIsCopied] = React.useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const windowRef = useRef<HTMLDivElement>(null)
  const { getMessageForModel, clearMessageForModel } = useWebSocketContext()
  const { focusedWindowId, registerClearHandler, unregisterClearHandler } = useAppState()
  const { registerShortcut } = useKeyboardShortcutsContext()

  const isFocused = focusedWindowId === id

  const streamingMessage = getMessageForModel(id)
  const isStreaming = streamingMessage && !streamingMessage.isComplete

  // Debug logging
  useEffect(() => {
    if (streamingMessage) {
      console.log(`ChatWindow ${id} streaming:`, {
        content: streamingMessage.content,
        isComplete: streamingMessage.isComplete,
        error: streamingMessage.error
      })
    }
  }, [streamingMessage, id])

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

  // Add user message immediately when sent
  useEffect(() => {
    const handleUserMessage = (event: CustomEvent<{ content: string }>) => {
      // Add user message to all chat windows immediately
      setMessages(prev => [...prev, {
        role: 'user',
        content: event.detail.content,
        timestamp: new Date()
      }])
    }

    window.addEventListener('userMessageSent' as any, handleUserMessage as any)
    return () => {
      window.removeEventListener('userMessageSent' as any, handleUserMessage as any)
    }
  }, [])

  // Add completed streaming message to messages array
  useEffect(() => {
    console.log(`ChatWindow ${id} - checking completion:`, {
      hasStreamingMessage: !!streamingMessage,
      isComplete: streamingMessage?.isComplete,
      hasContent: !!streamingMessage?.content,
      contentLength: streamingMessage?.content?.length
    })

    if (streamingMessage && streamingMessage.isComplete && streamingMessage.content) {
      console.log(`ChatWindow ${id} - adding completed message to array`)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: streamingMessage.content,
        timestamp: new Date()
      }])
      // Clear the streaming message after adding it to messages
      clearMessageForModel(id)
    }
  }, [streamingMessage?.isComplete, streamingMessage?.content, id, clearMessageForModel])

  return (
    <div
      ref={windowRef}
      className={`bg-gray-800 rounded-lg border-2 flex flex-col h-full transition-all overflow-hidden ${
        isFocused ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-gray-700'
      }`}
      onClick={() => {
        // Optional: click to focus
      }}
    >
      {/* Header - Fixed */}
      <div className={`px-3 py-2 rounded-t-lg border-b flex justify-between items-center flex-shrink-0 ${
        isFocused ? 'bg-blue-900/30 border-blue-600' : 'bg-gray-700 border-gray-600'
      }`}>
        <h3 className="text-base font-semibold flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded ${
            isFocused ? 'bg-blue-600' : 'bg-gray-600'
          }`}>{id}:</span>
          {modelName}
        </h3>
        <div className="flex items-center gap-2">
          {isCopied && (
            <span className="text-base text-green-400">Copied!</span>
          )}
          {isStreaming && (
            <span className="text-base text-blue-400 animate-pulse">Thinking...</span>
          )}
        </div>
      </div>

      {/* Messages area - Scrollable */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 min-h-0">
        {messages.length === 0 && !streamingMessage ? (
          <p className="text-gray-500 text-base text-center mt-4">
            Waiting for messages...
          </p>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-3`}
              >
                <div
                  className={`max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-blue-900/30'
                      : 'bg-gray-700/50'
                  } rounded-lg p-3`}
                >
                  <div className="text-base mb-1" style={{ color: 'black', fontWeight: 'bold' }}>
                    {message.role === 'user' ? 'You' : modelName}
                  </div>
                  <div className="text-base prose-chat">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}

            {/* Streaming message */}
            {streamingMessage && (
              <div className="flex justify-start mb-3">
                <div className="max-w-[80%] bg-gray-700/50 rounded-lg p-3">
                <div className="text-base mb-1" style={{ color: 'black', fontWeight: 'bold' }}>
                  {modelName}
                </div>
                <div className="text-base prose-chat">
                  {streamingMessage.error ? (
                    <span className="text-red-400">Error: {streamingMessage.error}</span>
                  ) : (
                    <>
                      <ReactMarkdown>{streamingMessage.content}</ReactMarkdown>
                      {isStreaming && <span className="animate-pulse">▊</span>}
                    </>
                  )}
                </div>
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
