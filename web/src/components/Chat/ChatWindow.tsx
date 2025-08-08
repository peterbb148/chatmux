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
      } else {
      }
    }

    window.addEventListener('userMessageSent' as any, handleUserMessage as any)
    return () => {
      window.removeEventListener('userMessageSent' as any, handleUserMessage as any)
    }
  }, [id, messages.length])

  // Add completed streaming message to messages array
  useEffect(() => {
    if (streamingMessage && streamingMessage.isComplete && streamingMessage.content) {
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
      className={`bg-gray-900 rounded-lg border flex flex-col h-full transition-all overflow-hidden ${
        isFocused ? 'border-blue-500 shadow-xl shadow-blue-500/30 ring-1 ring-blue-400/20' : 'border-gray-700'
      }`}
      onClick={() => {
        // Optional: click to focus
      }}
    >
      {/* Header - TMux Style */}
      <div className={`px-3 py-1.5 border-b flex justify-between items-center flex-shrink-0 font-mono text-sm ${
        isFocused ? 'bg-gradient-to-r from-blue-900/40 to-blue-800/30 border-blue-500/50' : 'bg-gray-800/50 border-gray-700'
      }`}>
        <h3 className="flex items-center gap-1">
          <span className="text-gray-500">┌─[</span>
          <span className={`font-bold px-1 ${
            isFocused ? 'text-blue-400' : 'text-gray-400'
          }`}>{id}</span>
          <span className="text-gray-500">]─</span>
          <span className={`font-medium ${
            isFocused ? 'text-white' : 'text-gray-300'
          }`}>{modelName}</span>
          <span className="text-gray-500">─────</span>
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
      <div className="flex-1 overflow-y-auto px-4 py-3 min-h-0 bg-gradient-to-b from-gray-900 to-gray-900/95">
        {messages.length === 0 && !streamingMessage ? (
          <p className="text-gray-500 text-base text-center mt-4">
            Waiting for messages...
          </p>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-3 animate-fadeIn`}
              >
                <div className={`relative max-w-[70%] group`}>
                  <div
                    className={`px-4 py-2.5 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-2xl rounded-br-sm shadow-lg ml-auto'
                        : 'bg-gray-800 text-gray-100 rounded-2xl rounded-bl-sm border border-gray-700/50 shadow-md'
                    } transition-all duration-200 hover:shadow-xl`}
                  >
                    <div className="text-sm leading-relaxed prose-chat-bubble">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  </div>
                  <div className={`text-xs mt-1 opacity-60 ${
                    message.role === 'user' ? 'text-right pr-1 text-gray-400' : 'pl-1 text-gray-500'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}

            {/* Streaming message */}
            {streamingMessage && (
              <div className="flex justify-start mb-3 animate-fadeIn">
                <div className="relative max-w-[70%]">
                  <div className="px-4 py-2.5 bg-gray-800 text-gray-100 rounded-2xl rounded-bl-sm border border-gray-700/50 shadow-md">
                    <div className="text-sm leading-relaxed prose-chat-bubble">
                      {streamingMessage.error ? (
                        <span className="text-red-400">Error: {streamingMessage.error}</span>
                      ) : (
                        <>
                          <ReactMarkdown>{streamingMessage.content}</ReactMarkdown>
                          {isStreaming && (
                            <span className="inline-flex ml-1">
                              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce mr-0.5" style={{animationDelay: '0ms'}}></span>
                              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce mr-0.5" style={{animationDelay: '150ms'}}></span>
                              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                            </span>
                          )}
                        </>
                      )}
                    </div>
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
