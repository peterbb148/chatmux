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
    <div className="h-screen w-screen flex flex-col overflow-hidden" style={{ backgroundColor: '#ffffff' }}>
      {/* Chat windows grid - takes up available space */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ChatGrid />
      </div>

      {/* Input box at bottom - always visible */}
      <div className="flex-shrink-0">
        <InputBox ref={inputRef} />
      </div>
    </div>
  )
}

export default MainLayout
