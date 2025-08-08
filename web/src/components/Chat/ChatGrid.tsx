import React from 'react'
import ChatWindow from './ChatWindow'
import { useAppState } from '../../contexts/AppStateContext'

const ChatGrid: React.FC = () => {
  const { windows, gridCols } = useAppState()

  return (
    <div
      className="h-full grid overflow-hidden"
      style={{
        gridTemplateColumns: `repeat(${gridCols}, 1fr)`
      }}
    >
      {windows.map((window) => (
        <ChatWindow
          key={window.id}
          id={window.id}
          modelName={window.name}
          provider={window.provider}
        />
      ))}
    </div>
  )
}

export default ChatGrid
