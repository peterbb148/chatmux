import React, { useState, useRef, forwardRef, useImperativeHandle, useEffect } from 'react'
import type { KeyboardEvent } from 'react'
import { useWebSocketContext } from '../../contexts/WebSocketContext'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'
import { useAppState } from '../../contexts/AppStateContext'

export interface InputBoxRef {
  focus: () => void
  clear: () => void
}

const InputBox = forwardRef<InputBoxRef>((_, ref) => {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { sendMessage, connected } = useWebSocketContext()
  const { registerShortcut } = useKeyboardShortcutsContext()
  const { focusedWindowId } = useAppState()

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
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
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

    if (textareaRef.current) {
      textareaRef.current.style.height = '52px'
      const scrollHeight = textareaRef.current.scrollHeight
      textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`
    }
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
