import React, { useState, useRef } from 'react'
import type { KeyboardEvent } from 'react'

const InputBox: React.FC = () => {
  const [message, setMessage] = useState('')
  const [targets, setTargets] = useState<number[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Parse @mentions from the message
  const parseTargets = (text: string): number[] => {
    const mentions = text.match(/@(\d+)/g)
    if (!mentions) return []

    return mentions
      .map(m => parseInt(m.substring(1)))
      .filter(n => n >= 1 && n <= 4)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    if (!message.trim()) return

    const targetModels = parseTargets(message)
    console.log('Sending message:', message)
    console.log('Targets:', targetModels.length > 0 ? targetModels : 'all')

    // TODO: Send message via WebSocket

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
    <div className="p-4 bg-gray-800">
      <div className="max-w-full mx-auto">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <div className="text-xs text-gray-400 mb-1">
              {targets.length > 0
                ? `Sending to: Model${targets.length > 1 ? 's' : ''} ${targets.join(', ')}`
                : 'Sending to: All models'
              }
              <span className="ml-2 text-gray-500">
                (Use @1-4 to target specific models)
              </span>
            </div>
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder="Type your message here..."
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg
                         text-gray-100 placeholder-gray-400 resize-none
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         min-h-[40px] max-h-[200px]"
              rows={1}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!message.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium
                     hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed
                     transition-colors duration-200"
          >
            Send
          </button>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}

export default InputBox
