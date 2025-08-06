import React, { createContext, useContext } from 'react'
import type { ReactNode } from 'react'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'

interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  cmd?: boolean
  shift?: boolean
  alt?: boolean
  description: string
  handler: () => void
}

interface KeyboardShortcutsContextType {
  registerShortcut: (shortcut: KeyboardShortcut) => () => void
  showHelp: boolean
  setShowHelp: (show: boolean) => void
  shortcuts: KeyboardShortcut[]
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextType | null>(null)

export const KeyboardShortcutsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const keyboardShortcuts = useKeyboardShortcuts()

  return (
    <KeyboardShortcutsContext.Provider value={keyboardShortcuts}>
      {children}
    </KeyboardShortcutsContext.Provider>
  )
}

export const useKeyboardShortcutsContext = () => {
  const context = useContext(KeyboardShortcutsContext)
  if (!context) {
    throw new Error('useKeyboardShortcutsContext must be used within a KeyboardShortcutsProvider')
  }
  return context
}
