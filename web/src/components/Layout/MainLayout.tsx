import React from 'react'
import ChatGrid from '../Chat/ChatGrid'
import InputBox from '../Input/InputBox'

const MainLayout: React.FC = () => {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-2">
        <h1 className="text-xl font-bold">Chatmux</h1>
        <p className="text-sm text-gray-400">Multi-LLM Chat Interface</p>
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
