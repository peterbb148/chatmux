import './App.css'
import MainLayout from './components/Layout/MainLayout'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { KeyboardShortcutsProvider } from './contexts/KeyboardShortcutsContext'
import { AppStateProvider } from './contexts/AppStateContext'
import KeyboardShortcutsHelp from './components/UI/KeyboardShortcutsHelp'

function App() {
  return (
    <WebSocketProvider>
      <AppStateProvider>
        <KeyboardShortcutsProvider>
          <MainLayout />
          <KeyboardShortcutsHelp />
        </KeyboardShortcutsProvider>
      </AppStateProvider>
    </WebSocketProvider>
  )
}

export default App
