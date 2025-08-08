import React, { useState, useEffect, useRef } from 'react'
import { useAppState } from '../../contexts/AppStateContext'

interface Command {
  name: string
  description: string
  syntax: string
  execute: (args: string[]) => void
}

interface ModelSuggestion {
  name: string
  provider: string
  inUse: boolean
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  commandText: string
  onCommandSelect: (command: string) => void
}

const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  commandText,
  onCommandSelect
}) => {
  const { addWindow, removeWindow, setGridCols, clearAllChats, windows } = useAppState()
  const [filteredCommands, setFilteredCommands] = useState<Command[]>([])
  const [modelSuggestions, setModelSuggestions] = useState<ModelSuggestion[]>([])
  const [showModelSuggestions, setShowModelSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const paletteRef = useRef<HTMLDivElement>(null)
  const [availableModels, setAvailableModels] = useState<ModelSuggestion[]>([])

  const commands: Command[] = [
    {
      name: 'new',
      description: 'Open a new chat window',
      syntax: '/new <model-name>',
      execute: (args) => {
        if (args.length > 0) {
          const modelName = args.join(' ')
          addWindow(modelName)
        }
      }
    },
    {
      name: 'close',
      description: 'Close a chat window',
      syntax: '/close <window-id>',
      execute: (args) => {
        if (args.length > 0) {
          const windowId = parseInt(args[0])
          if (!isNaN(windowId)) {
            removeWindow(windowId)
          }
        }
      }
    },
    {
      name: 'clear',
      description: 'Clear chat history',
      syntax: '/clear [all | window-id]',
      execute: (args) => {
        if (args[0] === 'all') {
          clearAllChats()
        } else if (args.length > 0) {
          const windowId = parseInt(args[0])
          if (!isNaN(windowId)) {
            const event = new CustomEvent('clearSpecificChat', { detail: { windowId } })
            window.dispatchEvent(event)
          }
        }
      }
    },
    {
      name: 'layout',
      description: 'Change grid layout',
      syntax: '/layout <columns>',
      execute: (args) => {
        if (args.length > 0) {
          const cols = parseInt(args[0])
          if (!isNaN(cols) && cols >= 1 && cols <= 6) {
            setGridCols(cols)
          }
        }
      }
    },
    {
      name: 'models',
      description: 'List available models',
      syntax: '/models',
      execute: () => {
        const modelList = windows.map(w => `${w.id}: ${w.name}`).join(', ')
        console.log('Active windows:', modelList)
        alert(`Active windows:\n${windows.map(w => `${w.id}: ${w.name}`).join('\n')}`)
      }
    }
  ]

  // Fetch available models
  useEffect(() => {
    // Common model suggestions
    const commonModels: ModelSuggestion[] = [
      // OpenAI models
      { name: 'gpt-5', provider: 'OpenAI', inUse: false },
      { name: 'gpt-4o', provider: 'OpenAI', inUse: false },
      { name: 'gpt-4o-mini', provider: 'OpenAI', inUse: false },
      { name: 'gpt-4-turbo', provider: 'OpenAI', inUse: false },
      { name: 'gpt-3.5-turbo', provider: 'OpenAI', inUse: false },
      // Anthropic models
      { name: 'claude-3-5-sonnet-20241022', provider: 'Anthropic', inUse: false },
      { name: 'claude-3-5-haiku-20241022', provider: 'Anthropic', inUse: false },
      { name: 'claude-3-opus-20240229', provider: 'Anthropic', inUse: false },
      { name: 'claude-3-sonnet-20240229', provider: 'Anthropic', inUse: false },
      { name: 'claude-3-haiku-20240307', provider: 'Anthropic', inUse: false },
      // Google models
      { name: 'gemini-1.5-pro', provider: 'Google', inUse: false },
      { name: 'gemini-1.5-pro-latest', provider: 'Google', inUse: false },
      { name: 'gemini-1.5-flash', provider: 'Google', inUse: false },
      { name: 'gemini-1.0-pro', provider: 'Google', inUse: false },
      // Mistral models
      { name: 'mistral-large-latest', provider: 'Mistral', inUse: false },
      { name: 'mistral-medium-latest', provider: 'Mistral', inUse: false },
      { name: 'mistral-small-latest', provider: 'Mistral', inUse: false },
      { name: 'mixtral-8x7b-instruct', provider: 'Mistral', inUse: false },
    ]

    // Mark models that are already in use
    const modelsWithUsage = commonModels.map(model => ({
      ...model,
      inUse: windows.some(w => w.name === model.name)
    }))

    setAvailableModels(modelsWithUsage)
  }, [windows])

  useEffect(() => {
    if (!isOpen) {
      setSelectedIndex(0)
      setShowModelSuggestions(false)
      return
    }

    const searchTerm = commandText.slice(1).toLowerCase() // Remove the '/' prefix
    const parts = searchTerm.split(' ')
    const commandName = parts[0]
    const args = parts.slice(1).join(' ')

    // Check if we should show model suggestions
    if (commandName === 'new' && searchTerm.includes(' ')) {
      setShowModelSuggestions(true)
      const modelSearch = args.toLowerCase()

      if (modelSearch) {
        const filtered = availableModels.filter(model =>
          model.name.toLowerCase().includes(modelSearch) ||
          model.provider.toLowerCase().includes(modelSearch)
        )
        setModelSuggestions(filtered)
      } else {
        // Show all available models when just "/new " is typed
        setModelSuggestions(availableModels)
      }
      setFilteredCommands([])
    } else {
      setShowModelSuggestions(false)
      if (commandName) {
        const filtered = commands.filter(cmd =>
          cmd.name.toLowerCase().startsWith(commandName)
        )
        setFilteredCommands(filtered)
      } else {
        setFilteredCommands(commands)
      }
    }
  }, [commandText, isOpen, availableModels])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      const items = showModelSuggestions ? modelSuggestions : filteredCommands
      const maxIndex = items.length - 1

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev => prev < maxIndex ? prev + 1 : prev)
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => prev > 0 ? prev - 1 : 0)
          break
        case 'Enter':
          e.preventDefault()
          if (showModelSuggestions && modelSuggestions[selectedIndex]) {
            onCommandSelect(`/new ${modelSuggestions[selectedIndex].name}`)
          } else if (filteredCommands[selectedIndex]) {
            onCommandSelect(filteredCommands[selectedIndex].syntax)
          }
          break
        case 'Tab':
          e.preventDefault()
          if (showModelSuggestions && modelSuggestions[selectedIndex]) {
            onCommandSelect(`/new ${modelSuggestions[selectedIndex].name}`)
          }
          break
        case 'Escape':
          e.preventDefault()
          onClose()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredCommands, modelSuggestions, showModelSuggestions, selectedIndex, onCommandSelect, onClose])

  if (!isOpen) return null

  return (
    <div
      ref={paletteRef}
      style={{
        position: 'absolute',
        bottom: '100%',
        left: 0,
        right: 0,
        marginBottom: '8px',
        backgroundColor: '#ffffff',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        maxHeight: '400px',
        overflowY: 'auto',
        zIndex: 1000
      }}
    >
      {showModelSuggestions ? (
        // Show model suggestions
        modelSuggestions.length === 0 ? (
          <div style={{ padding: '12px 16px', color: '#999' }}>
            No matching models found
          </div>
        ) : (
          <>
            <div style={{
              padding: '8px 16px',
              borderBottom: '1px solid #e0e0e0',
              backgroundColor: '#fafafa',
              fontSize: '12px',
              color: '#666',
              fontWeight: 500
            }}>
              Available Models
            </div>
            {modelSuggestions.map((model, index) => (
              <div
                key={model.name}
                style={{
                  padding: '10px 16px',
                  backgroundColor: index === selectedIndex ? '#f0f0f0' : 'transparent',
                  cursor: 'pointer',
                  borderBottom: index < modelSuggestions.length - 1 ? '1px solid #f0f0f0' : 'none',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
                onMouseEnter={() => setSelectedIndex(index)}
                onClick={() => onCommandSelect(`/new ${model.name}`)}
              >
                <div>
                  <div style={{
                    fontSize: '14px',
                    color: '#2e2e2e',
                    fontWeight: model.inUse ? 400 : 500
                  }}>
                    {model.name}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#666',
                    marginTop: '2px'
                  }}>
                    {model.provider}
                  </div>
                </div>
                {model.inUse && (
                  <span style={{
                    fontSize: '11px',
                    color: '#999',
                    backgroundColor: '#f0f0f0',
                    padding: '2px 6px',
                    borderRadius: '4px'
                  }}>
                    In Use
                  </span>
                )}
              </div>
            ))}
          </>
        )
      ) : (
        // Show regular commands
        filteredCommands.length === 0 ? (
          <div style={{ padding: '12px 16px', color: '#999' }}>
            No matching commands
          </div>
        ) : (
          filteredCommands.map((cmd, index) => (
            <div
              key={cmd.name}
              style={{
                padding: '12px 16px',
                backgroundColor: index === selectedIndex ? '#f0f0f0' : 'transparent',
                cursor: 'pointer',
                borderBottom: index < filteredCommands.length - 1 ? '1px solid #f0f0f0' : 'none'
              }}
              onMouseEnter={() => setSelectedIndex(index)}
              onClick={() => onCommandSelect(cmd.syntax)}
            >
              <div style={{
                fontWeight: 500,
                fontSize: '14px',
                color: '#2e2e2e',
                marginBottom: '4px'
              }}>
                {cmd.syntax}
              </div>
              <div style={{
                fontSize: '12px',
                color: '#666'
              }}>
                {cmd.description}
              </div>
            </div>
          ))
        )
      )}
    </div>
  )
}

export default CommandPalette
