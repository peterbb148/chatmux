import React, { useState, useRef, forwardRef, useImperativeHandle, useEffect } from 'react'
import type { KeyboardEvent } from 'react'
import { useWebSocketContext } from '../../contexts/WebSocketContext'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'
import { useAppState } from '../../contexts/AppStateContext'
import CommandPalette from '../CommandPalette/CommandPalette'

export interface InputBoxRef {
  focus: () => void
  clear: () => void
}

const InputBox = forwardRef<InputBoxRef>((_, ref) => {
  const [message, setMessage] = useState('')
  const [showCommandPalette, setShowCommandPalette] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { sendMessage, connected } = useWebSocketContext()
  const { registerShortcut } = useKeyboardShortcutsContext()
  const { focusedWindowId, addWindow } = useAppState()

  useImperativeHandle(ref, () => ({
    focus: () => {
      textareaRef.current?.focus()
    },
    clear: () => {
      setMessage('')
      if (textareaRef.current) {
        textareaRef.current.style.height = '52px'
      }
    }
  }))

  useEffect(() => {
    const unsubscribe = registerShortcut({
      key: 'Enter',
      cmd: true,
      ctrl: true,
      description: 'Send message',
      handler: () => {
        if (document.activeElement === textareaRef.current) {
          handleSend()
        }
      }
    })

    return unsubscribe
  }, [message, focusedWindowId])

  const parseTargets = (text: string): string[] => {
    const mentions = text.match(/@(\d+)/g)
    if (!mentions) return []

    return mentions
      .map(m => m.substring(1))
      .filter(n => parseInt(n) >= 1 && parseInt(n) <= 4)
  }

  const stripMentions = (text: string): string => {
    return text.replace(/@(\d+)/g, '').replace(/\s+/g, ' ').trim()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showCommandPalette) {
      // Let CommandPalette handle keyboard events when it's open
      if (e.key === 'Escape') {
        e.preventDefault()
        setShowCommandPalette(false)
        setMessage('')
        return
      }
      // Don't handle Enter here when palette is open - let CommandPalette handle it
      if (e.key === 'Enter' || e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'Tab') {
        return
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()

      // Check if it's a command
      if (message.startsWith('/')) {
        executeCommand(message)
      } else {
        handleSend()
      }
    }
  }

  const executeCommand = (commandText: string) => {
    const parts = commandText.slice(1).split(' ')
    const command = parts[0]
    const args = parts.slice(1)

    switch (command) {
      case 'new':
        if (args.length > 0) {
          addWindow(args.join(' '))
        }
        break
      case 'clear':
        if (args[0] === 'all') {
          window.dispatchEvent(new Event('clearAllChats'))
        }
        break
      // Add more commands as needed
    }

    setMessage('')
    setShowCommandPalette(false)
  }

  const handleSend = () => {
    if (!message.trim()) return

    const mentions = parseTargets(message)
    const cleanedMessage = stripMentions(message)

    if (!cleanedMessage.trim()) return

    const targetIds = mentions.length > 0
      ? mentions
      : (focusedWindowId ? [String(focusedWindowId)] : [])

    window.dispatchEvent(new CustomEvent('userMessageSent', {
      detail: {
        content: cleanedMessage,
        targets: targetIds
      }
    }))

    sendMessage(cleanedMessage, targetIds.map(Number))
    setMessage('')

    if (textareaRef.current) {
      textareaRef.current.style.height = '52px'
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value
    setMessage(text)

    // Show command palette when user types '/'
    if (text.startsWith('/')) {
      setShowCommandPalette(true)
    } else {
      setShowCommandPalette(false)
    }

    if (textareaRef.current) {
      textareaRef.current.style.height = '52px'
      const scrollHeight = textareaRef.current.scrollHeight
      textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`
    }
  }

  const handleCommandSelect = (command: string) => {
    setMessage(command)
    setShowCommandPalette(false)
    textareaRef.current?.focus()
  }

  return (
    <div style={{
      backgroundColor: '#fafafa',
      borderTop: '1px solid #e5e5e5',
      padding: '16px 24px',
      borderTopLeftRadius: '16px',
      borderTopRightRadius: '16px',
      boxShadow: '0 -2px 10px rgba(0,0,0,0.05)'
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', position: 'relative' }}>
        <CommandPalette
          isOpen={showCommandPalette}
          onClose={() => setShowCommandPalette(false)}
          commandText={message}
          onCommandSelect={handleCommandSelect}
        />
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Send a message..."
          disabled={!connected}
          style={{
            width: '100%',
            padding: '12px 16px',
            backgroundColor: '#ffffff',
            border: '1px solid #e0e0e0',
            borderRadius: '24px',
            color: '#2e2e2e',
            fontSize: '15px',
            lineHeight: '1.5',
            resize: 'none',
            outline: 'none',
            minHeight: '48px',
            maxHeight: '200px',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            transition: 'border-color 0.2s, box-shadow 0.2s'
          }}
          rows={1}
        />

      </div>
    </div>
  )
})

InputBox.displayName = 'InputBox'

export default InputBox
