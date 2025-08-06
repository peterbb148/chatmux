import React, { createContext, useContext, useState, useCallback } from 'react'
import type { ReactNode } from 'react'

interface AppStateContextType {
  focusedWindowId: number | null
  setFocusedWindowId: (id: number | null) => void
  clearAllChats: () => void
  clearChatHandlers: Map<number, () => void>
  registerClearHandler: (id: number, handler: () => void) => void
  unregisterClearHandler: (id: number) => void
}

const AppStateContext = createContext<AppStateContextType | null>(null)

export const AppStateProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [focusedWindowId, setFocusedWindowId] = useState<number | null>(null)
  const [clearChatHandlers] = useState(new Map<number, () => void>())

  const registerClearHandler = useCallback((id: number, handler: () => void) => {
    clearChatHandlers.set(id, handler)
  }, [clearChatHandlers])

  const unregisterClearHandler = useCallback((id: number) => {
    clearChatHandlers.delete(id)
  }, [clearChatHandlers])

  const clearAllChats = useCallback(() => {
    clearChatHandlers.forEach(handler => handler())
  }, [clearChatHandlers])

  return (
    <AppStateContext.Provider
      value={{
        focusedWindowId,
        setFocusedWindowId,
        clearAllChats,
        clearChatHandlers,
        registerClearHandler,
        unregisterClearHandler
      }}
    >
      {children}
    </AppStateContext.Provider>
  )
}

export const useAppState = () => {
  const context = useContext(AppStateContext)
  if (!context) {
    throw new Error('useAppState must be used within an AppStateProvider')
  }
  return context
}
