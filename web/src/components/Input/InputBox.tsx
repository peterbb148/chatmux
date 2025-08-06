import React, { useState, useRef, forwardRef, useImperativeHandle, useEffect } from 'react'
import type { KeyboardEvent } from 'react'
import { useWebSocketContext } from '../../contexts/WebSocketContext'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'

export interface InputBoxRef {
  focus: () => void
  clear: () => void
}

const InputBox = forwardRef<InputBoxRef>((_, ref) => {
  const [message, setMessage] = useState('')
  const [targets, setTargets] = useState<number[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { sendMessage, connected } = useWebSocketContext()
  const { registerShortcut } = useKeyboardShortcutsContext()

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    focus: () => {
      textareaRef.current?.focus()
    },
    clear: () => {
      setMessage('')
      setTargets([])
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }))

  // Register Cmd+Enter shortcut
  useEffect(() => {
    const unsubscribe = registerShortcut({
      key: 'Enter',
      cmd: true,
      ctrl: true,
      description: 'Send message',
      handler: () => {
        // Only handle if textarea is focused
        if (document.activeElement === textareaRef.current) {
          handleSend()
        }
      }
    })

    return unsubscribe
  }, [message]) // Include message in deps so handler has current value

  // Parse @mentions from the message
  const parseTargets = (text: string): number[] => {
    const mentions = text.match(/@(\d+)/g)
    if (!mentions) return []

    return mentions
      .map(m => parseInt(m.substring(1)))
      .filter(n => n >= 1 && n <= 4)
  }

  // Remove @mentions from the message content
  const stripMentions = (text: string): string => {
    return text.replace(/@(\d+)/g, '').replace(/\s+/g, ' ').trim()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd+Enter is handled by the keyboard shortcut, so we only need to prevent default here
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
    }
  }

  const handleSend = () => {
    if (!message.trim()) return

    const targetModels = parseTargets(message)
    const cleanedMessage = stripMentions(message)

    // Don't send if the cleaned message is empty
    if (!cleanedMessage.trim()) return

    // Dispatch custom event for ChatWindow components to capture the original message
    window.dispatchEvent(new CustomEvent('userMessageSent', {
      detail: { content: message }
    }))

    // Send cleaned message (without @mentions) via WebSocket
    sendMessage(cleanedMessage, targetModels)

    setMessage('')
    setTargets([])

    // Auto-resize textarea back to original height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value
    setMessage(text)
    setTargets(parseTargets(text))

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  return (
    <div className="py-4 bg-gray-800 rounded-b-xl">
      <div className="max-w-full mx-auto px-4">
        {/* Connection status */}
        {!connected && (
          <div className="text-base text-red-400 mb-2">
            Disconnected from server. Reconnecting...
          </div>
        )}

        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Enter prompt here"
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg
                     text-base text-gray-100 placeholder:text-base placeholder:text-gray-400 resize-none
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     min-h-[40px] max-h-[200px]"
          rows={1}
          disabled={!connected}
        />
        <div className="mt-3 flex justify-between items-center text-base text-gray-500">
          <div>
            {targets.length > 0
              ? `Sending to: Model${targets.length > 1 ? 's' : ''} ${targets.join(', ')}`
              : 'Sending to: All models'
            }
            <span className="ml-2">
              (Use @1-4 to target specific models)
            </span>
          </div>
          <div>
            Press Cmd+Enter to send, Enter for new line
          </div>
        </div>
      </div>
    </div>
  )
})

InputBox.displayName = 'InputBox'

export default InputBox
