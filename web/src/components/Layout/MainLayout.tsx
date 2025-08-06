import React from 'react'
import ChatGrid from '../Chat/ChatGrid'
import InputBox from '../Input/InputBox'
import { useWebSocketContext } from '../../contexts/WebSocketContext'

const MainLayout: React.FC = () => {
  const { connected } = useWebSocketContext()

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold">Chatmux</h1>
          <p className="text-sm text-gray-400">Multi-LLM Chat Interface</p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-400">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </header>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Chat windows grid - takes up most space */}
        <div className="flex-1 overflow-hidden">
          <ChatGrid />
        </div>

        {/* Input area - fixed height at bottom */}
        <div className="border-t border-gray-700">
          <InputBox />
        </div>
      </div>
    </div>
  )
}

export default MainLayout
