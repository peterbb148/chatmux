import './App.css'
import MainLayout from './components/Layout/MainLayout'
import { WebSocketProvider } from './contexts/WebSocketContext'

function App() {
  return (
    <WebSocketProvider>
      <MainLayout />
    </WebSocketProvider>
  )
}

export default App
