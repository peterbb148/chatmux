import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
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
  const [windows, setWindows] = useState<ChatWindowModel[]>([])
  const [gridCols, setGridCols] = useState(4)
  const [nextWindowId, setNextWindowId] = useState(5)

  // Fetch models from backend on mount and restore from localStorage
  useEffect(() => {
    // Try to restore windows from localStorage first
    const savedWindows = localStorage.getItem('chatmux_windows')
    const savedNextId = localStorage.getItem('chatmux_next_window_id')
    const savedGridCols = localStorage.getItem('chatmux_grid_cols')

    if (savedWindows) {
      try {
        const windows = JSON.parse(savedWindows)
        setWindows(windows)
        if (savedNextId) {
          setNextWindowId(parseInt(savedNextId))
        }
        if (savedGridCols) {
          setGridCols(parseInt(savedGridCols))
        }
        return
      } catch (err) {
        console.error('Failed to restore windows from localStorage:', err)
      }
    }

    // If no saved state, fetch default models from backend
    fetch('http://localhost:8000/models')
      .then(res => res.json())
      .then(data => {
        setWindows(data.models)
        // Set next window ID to be one more than the highest existing ID
        const maxId = Math.max(...data.models.map((m: ChatWindowModel) => m.id))
        setNextWindowId(maxId + 1)
      })
      .catch(err => {
        console.error('Failed to fetch models:', err)
        // Fallback to default models if backend is unavailable
        setWindows([
          { id: 1, name: 'gpt-4o', provider: 'OpenAI' },
          { id: 2, name: 'claude-3-5-sonnet', provider: 'Anthropic' },
          { id: 3, name: 'gemini-1.5-pro', provider: 'Google' },
          { id: 4, name: 'mistral-large-latest', provider: 'Mistral' },
        ])
      })
  }, [])

  // Save windows to localStorage whenever they change
  useEffect(() => {
    if (windows.length > 0) {
      localStorage.setItem('chatmux_windows', JSON.stringify(windows))
      localStorage.setItem('chatmux_next_window_id', String(nextWindowId))
      localStorage.setItem('chatmux_grid_cols', String(gridCols))
    }
  }, [windows, nextWindowId, gridCols])

  const addWindow = useCallback((modelName: string, provider?: string) => {
    // Auto-detect provider based on model name if not provided
    let detectedProvider = provider || 'Custom'
    if (!provider) {
      const modelLower = modelName.toLowerCase()
      if (modelLower.includes('gpt') || modelLower.includes('davinci') || modelLower.includes('turbo')) {
        detectedProvider = 'OpenAI'
      } else if (modelLower.includes('claude') || modelLower.includes('opus') || modelLower.includes('sonnet') || modelLower.includes('haiku')) {
        detectedProvider = 'Anthropic'
      } else if (modelLower.includes('gemini') || modelLower.includes('bison') || modelLower.includes('palm')) {
        detectedProvider = 'Google'
      } else if (modelLower.includes('mistral') || modelLower.includes('mixtral') || modelLower.includes('magistral') || modelLower.includes('devstral') || modelLower.includes('codestral') || modelLower.includes('pixtral') || modelLower.includes('ministral')) {
        detectedProvider = 'Mistral'
      }
    }

    const newWindow: ChatWindowModel = {
      id: nextWindowId,
      name: modelName,
      provider: detectedProvider
    }
    setWindows(prev => [...prev, newWindow])
    setNextWindowId(prev => prev + 1)

    // Auto-adjust grid columns to match window count
    const newWindowCount = windows.length + 1
    // Increase columns when adding more windows
    if (newWindowCount > gridCols) {
      setGridCols(Math.min(8, newWindowCount))  // Support up to 8 columns
    }
  }, [nextWindowId, windows.length, gridCols])

  const removeWindow = useCallback((id: number) => {
    setWindows(prev => {
      const newWindows = prev.filter(w => w.id !== id)

      // Auto-adjust grid columns when removing windows
      const newWindowCount = newWindows.length
      if (newWindowCount > 0 && newWindowCount < gridCols) {
        setGridCols(Math.max(1, newWindowCount))
      }

      return newWindows
    })
    if (focusedWindowId === id) {
      setFocusedWindowId(null)
    }
    // Clean up handler
    clearChatHandlers.delete(id)
  }, [focusedWindowId, clearChatHandlers, gridCols])

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
