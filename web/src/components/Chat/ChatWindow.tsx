import React, { useEffect, useRef } from 'react'
import { useWebSocketContext } from '../../contexts/WebSocketContext'

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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { getMessageForModel } = useWebSocketContext()

  const streamingMessage = getMessageForModel(id)
  const isStreaming = streamingMessage && !streamingMessage.isComplete

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

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
    <div className="bg-gray-800 rounded-lg border border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="bg-gray-700 px-3 py-2 rounded-t-lg border-b border-gray-600 flex justify-between items-center">
        <div>
          <h3 className="font-semibold flex items-center gap-2">
            <span className="text-sm bg-gray-600 px-2 py-0.5 rounded">{id}</span>
            {modelName}
          </h3>
          <p className="text-xs text-gray-400">{provider}</p>
        </div>
        {isStreaming && (
          <span className="text-xs text-blue-400 animate-pulse">Thinking...</span>
        )}
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
