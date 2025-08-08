import React, { useState, useEffect, useRef } from 'react'
import { useAppState } from '../../contexts/AppStateContext'

interface Command {
  name: string
  description: string
  syntax: string
  execute: (args: string[]) => void
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
  const [selectedIndex, setSelectedIndex] = useState(0)
  const paletteRef = useRef<HTMLDivElement>(null)

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

  useEffect(() => {
    if (!isOpen) {
      setSelectedIndex(0)
      return
    }

    const searchTerm = commandText.slice(1).toLowerCase() // Remove the '/' prefix
    const parts = searchTerm.split(' ')
    const commandName = parts[0]

    if (commandName) {
      const filtered = commands.filter(cmd =>
        cmd.name.toLowerCase().startsWith(commandName)
      )
      setFilteredCommands(filtered)
    } else {
      setFilteredCommands(commands)
    }
  }, [commandText, isOpen])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev =>
            prev < filteredCommands.length - 1 ? prev + 1 : prev
          )
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => prev > 0 ? prev - 1 : 0)
          break
        case 'Enter':
          e.preventDefault()
          if (filteredCommands[selectedIndex]) {
            onCommandSelect(filteredCommands[selectedIndex].syntax)
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
  }, [isOpen, filteredCommands, selectedIndex, onCommandSelect, onClose])

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
        maxHeight: '300px',
        overflowY: 'auto',
        zIndex: 1000
      }}
    >
      {filteredCommands.length === 0 ? (
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
      )}
    </div>
  )
}

export default CommandPalette
