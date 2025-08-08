import React, { useEffect, useState } from 'react'
import ChatWindow from './ChatWindow'

interface Model {
  id: number
  name: string
  provider: string
}

const ChatGrid: React.FC = () => {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch model configuration from backend
    fetch('http://localhost:8000/models')
      .then(res => res.json())
      .then(data => {
        setModels(data.models)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch models:', err)
        // Fallback to default models
        setModels([
          { id: 1, name: 'gpt-4o', provider: 'OpenAI' },
          { id: 2, name: 'claude-3-5-sonnet', provider: 'Anthropic' },
          { id: 3, name: 'gemini-1.5-pro', provider: 'Google' },
          { id: 4, name: 'mistral-large-latest', provider: 'Mistral' },
        ])
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-gray-400">Loading models...</p>
      </div>
    )
  }

  return (
    <div className="h-full grid grid-cols-4 gap-2 p-2">
      {models.map((model) => (
        <ChatWindow
          key={model.id}
          id={model.id}
          modelName={model.name}
          provider={model.provider}
        />
      ))}
    </div>
  )
}

export default ChatGrid
