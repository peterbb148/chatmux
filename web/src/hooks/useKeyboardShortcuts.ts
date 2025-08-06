import { useEffect, useCallback, useState } from 'react'

interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  cmd?: boolean
  shift?: boolean
  alt?: boolean
  description: string
  handler: () => void
}

export const useKeyboardShortcuts = () => {
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([])
  const [showHelp, setShowHelp] = useState(false)

  const registerShortcut = useCallback((shortcut: KeyboardShortcut) => {
    setShortcuts(prev => [...prev, shortcut])

    return () => {
      setShortcuts(prev => prev.filter(s => s !== shortcut))
    }
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check for help shortcut (?)
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) {
        // Only trigger if not in an input field
        const target = e.target as HTMLElement
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          e.preventDefault()
          setShowHelp(prev => !prev)
          return
        }
      }

      // Check registered shortcuts
      for (const shortcut of shortcuts) {
        const ctrlOrCmd = shortcut.ctrl || shortcut.cmd
        const isCtrlPressed = e.ctrlKey || e.metaKey

        if (
          e.key.toLowerCase() === shortcut.key.toLowerCase() &&
          (!ctrlOrCmd || isCtrlPressed) &&
          (!shortcut.shift || e.shiftKey) &&
          (!shortcut.alt || e.altKey)
        ) {
          // Don't trigger shortcuts when typing in input fields unless explicitly allowed
          const target = e.target as HTMLElement
          const isInputField = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA'

          // For Cmd+Enter in input fields, trigger the handler
          if (shortcut.key === 'Enter' && isInputField && (shortcut.cmd || shortcut.ctrl)) {
            e.preventDefault()
            shortcut.handler()
            return
          }

          // Skip other shortcuts in input fields
          if (isInputField && shortcut.key !== 'Escape') {
            return
          }

          e.preventDefault()
          shortcut.handler()
          break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])

  return {
    registerShortcut,
    showHelp,
    setShowHelp,
    shortcuts
  }
}
