import React, { createContext, useContext, useState, useCallback } from 'react'
import type { ReactNode } from 'react'

export interface ChatWindowModel {
  id: number
  name: string
  provider: string
}

interface AppStateContextType {
  focusedWindowId: number | null
  setFocusedWindowId: (id: number | null) => void
  clearAllChats: () => void
  clearChatHandlers: Map<number, () => void>
  registerClearHandler: (id: number, handler: () => void) => void
  unregisterClearHandler: (id: number) => void
  windows: ChatWindowModel[]
  addWindow: (modelName: string, provider?: string) => void
  removeWindow: (id: number) => void
  gridCols: number
  setGridCols: (cols: number) => void
}

const AppStateContext = createContext<AppStateContextType | null>(null)

export const AppStateProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [focusedWindowId, setFocusedWindowId] = useState<number | null>(null)
  const [clearChatHandlers] = useState(new Map<number, () => void>())
  const [windows, setWindows] = useState<ChatWindowModel[]>([
    { id: 1, name: 'gpt-4o', provider: 'OpenAI' },
    { id: 2, name: 'claude-3-5-sonnet', provider: 'Anthropic' },
    { id: 3, name: 'gemini-1.5-pro', provider: 'Google' },
    { id: 4, name: 'mistral-large-latest', provider: 'Mistral' },
  ])
  const [gridCols, setGridCols] = useState(4)
  const [nextWindowId, setNextWindowId] = useState(5)

  const addWindow = useCallback((modelName: string, provider: string = 'Custom') => {
    const newWindow: ChatWindowModel = {
      id: nextWindowId,
      name: modelName,
      provider
    }
    setWindows(prev => [...prev, newWindow])
    setNextWindowId(prev => prev + 1)

    // Auto-adjust grid columns if needed
    const newWindowCount = windows.length + 1
    if (newWindowCount > gridCols * 2) {
      setGridCols(Math.min(6, gridCols + 1))
    }
  }, [nextWindowId, windows.length, gridCols])

  const removeWindow = useCallback((id: number) => {
    setWindows(prev => prev.filter(w => w.id !== id))
    if (focusedWindowId === id) {
      setFocusedWindowId(null)
    }
    // Clean up handler
    clearChatHandlers.delete(id)
  }, [focusedWindowId, clearChatHandlers])

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
        unregisterClearHandler,
        windows,
        addWindow,
        removeWindow,
        gridCols,
        setGridCols
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
