import React, { useEffect, useRef } from 'react'
import ChatGrid from '../Chat/ChatGrid'
import InputBox from '../Input/InputBox'
import type { InputBoxRef } from '../Input/InputBox'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'
import { useAppState } from '../../contexts/AppStateContext'

const MainLayout: React.FC = () => {
  const { registerShortcut } = useKeyboardShortcutsContext()
  const { setFocusedWindowId, clearAllChats } = useAppState()
  const inputRef = useRef<InputBoxRef>(null)

  useEffect(() => {
    // Auto-focus input on load with a small delay to ensure component is ready
    const focusTimeout = setTimeout(() => {
      inputRef.current?.focus()
    }, 100)

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
      clearTimeout(focusTimeout)
      unsubscribers.forEach(unsub => unsub())
    }
  }, [registerShortcut, setFocusedWindowId, clearAllChats])

  return (
    <div className="h-screen bg-black p-3">
      <div className="h-full flex flex-col bg-gray-950 text-gray-100 rounded-md shadow-2xl border border-gray-800 overflow-hidden">
        {/* Terminal-style header bar */}
        <div className="bg-gray-900 border-b border-gray-700 px-3 py-1 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
            </div>
            <span className="text-xs font-mono text-gray-500 ml-2">chatmux</span>
          </div>
          <div className="text-xs font-mono text-gray-500">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>

        {/* Chat windows grid - takes up most space */}
        <div className="flex-1 overflow-hidden bg-gradient-to-b from-gray-950 to-gray-900">
          <ChatGrid />
        </div>

        {/* Input area - fixed height at bottom */}
        <div className="border-t-2 border-gray-800 bg-gray-900/50">
          <InputBox ref={inputRef} />
        </div>
      </div>
    </div>
  )
}

export default MainLayout
