import React from 'react'

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
  const [messages, _setMessages] = React.useState<Message[]>([])
  const [isStreaming, _setIsStreaming] = React.useState(false)

  // TODO: Remove underscore when implementing WebSocket functionality
  // setMessages and setIsStreaming will be used to update state from WebSocket messages

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
        {messages.length === 0 ? (
          <p className="text-gray-500 text-sm text-center mt-4">
            Waiting for messages...
          </p>
        ) : (
          messages.map((message, index) => (
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
          ))
        )}
      </div>
    </div>
  )
}

export default ChatWindow
