import React from 'react'
import { useKeyboardShortcutsContext } from '../../contexts/KeyboardShortcutsContext'

const KeyboardShortcutsHelp: React.FC = () => {
  const { showHelp, setShowHelp, shortcuts } = useKeyboardShortcutsContext()

  if (!showHelp) return null

  const formatShortcut = (shortcut: { key: string; ctrl?: boolean; cmd?: boolean; shift?: boolean; alt?: boolean }) => {
    const parts = []

    if (shortcut.ctrl || shortcut.cmd) {
      parts.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl')
    }
    if (shortcut.shift) parts.push('Shift')
    if (shortcut.alt) parts.push('Alt')

    // Format special keys
    let key = shortcut.key
    if (key === 'Enter') key = '↵'
    else if (key === 'Escape') key = 'Esc'
    else if (key === 'ArrowUp') key = '↑'
    else if (key === 'ArrowDown') key = '↓'
    else if (key === 'ArrowLeft') key = '←'
    else if (key === 'ArrowRight') key = '→'

    parts.push(key)

    return parts.join('+')
  }

  // Add default shortcuts that are always available
  const defaultShortcuts = [
    { key: '?', description: 'Toggle this help' }
  ]

  const allShortcuts = [...defaultShortcuts, ...shortcuts]

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        onClick={() => setShowHelp(false)}
      />

      {/* Modal */}
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-800 rounded-lg shadow-2xl z-50 max-w-lg w-full mx-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-gray-100">Keyboard Shortcuts</h2>
            <button
              onClick={() => setShowHelp(false)}
              className="text-gray-400 hover:text-gray-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-2">
            {allShortcuts.map((shortcut, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b border-gray-700 last:border-0">
                <span className="text-base text-gray-300">{shortcut.description}</span>
                <kbd className="px-2 py-1 text-base font-semibold text-gray-100 bg-gray-700 rounded">
                  {formatShortcut(shortcut)}
                </kbd>
              </div>
            ))}
          </div>

          <div className="mt-4 text-base text-gray-500">
            Press Escape or click outside to close
          </div>
        </div>
      </div>
    </>
  )
}

export default KeyboardShortcutsHelp
