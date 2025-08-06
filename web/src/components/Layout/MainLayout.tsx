import React, { useEffect, useRef } from 'react'
import ChatGrid from '../Chat/ChatGrid'
import InputBox from '../Input/InputBox'
import type { InputBoxRef } from '../Input/InputBox'
import { useWebSocketContext } from '../../contexts/WebSocketContext'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'
import { useAppState } from '../../contexts/AppStateContext'

const MainLayout: React.FC = () => {
  const { connected } = useWebSocketContext()
  const { registerShortcut } = useKeyboardShortcutsContext()
  const { setFocusedWindowId, clearAllChats } = useAppState()
  const inputRef = useRef<InputBoxRef>(null)

  useEffect(() => {
    // Register window focus shortcuts (Cmd/Ctrl + 1-4)
    const unsubscribers: (() => void)[] = []

    for (let i = 1; i <= 4; i++) {
      unsubscribers.push(
        registerShortcut({
          key: i.toString(),
          ctrl: true,
          cmd: true,
          description: `Focus window ${i}`,
          handler: () => setFocusedWindowId(i)
        })
      )
    }

    // Clear all chats (Cmd/Ctrl + K)
    unsubscribers.push(
      registerShortcut({
        key: 'k',
        ctrl: true,
        cmd: true,
        description: 'Clear all chats',
        handler: () => {
          if (confirm('Clear all chat windows?')) {
            clearAllChats()
          }
        }
      })
    )

    // Escape to clear input
    unsubscribers.push(
      registerShortcut({
        key: 'Escape',
        description: 'Clear input',
        handler: () => {
          inputRef.current?.clear()
        }
      })
    )

    return () => {
      unsubscribers.forEach(unsub => unsub())
    }
  }, [registerShortcut, setFocusedWindowId, clearAllChats])

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold">Chatmux</h1>
          <p className="text-sm text-gray-400">Multi-LLM Chat Interface</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: '?' }))}
          >
            Press ? for help
          </button>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-400">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
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
          <InputBox ref={inputRef} />
        </div>
      </div>
    </div>
  )
}

export default MainLayout
