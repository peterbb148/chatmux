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
    <div className="h-screen bg-gray-100 p-4">
      <div className="h-full flex flex-col bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* Header bar */}
        <div className="bg-gray-50 border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-800">Chatmux</h1>
          <div className="text-sm text-gray-500">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>

        {/* Chat windows grid - takes up most space */}
        <div className="flex-1 overflow-hidden bg-gray-50">
          <ChatGrid />
        </div>

        {/* Input area - fixed height at bottom */}
        <div className="border-t border-gray-200 bg-white">
          <InputBox ref={inputRef} />
        </div>
      </div>
    </div>
  )
}

export default MainLayout
