import React from 'react'
import ChatWindow from './ChatWindow'

interface Model {
  id: number
  name: string
  provider: string
}

const models: Model[] = [
  { id: 1, name: 'GPT-4', provider: 'OpenAI' },
  { id: 2, name: 'Claude 3', provider: 'Anthropic' },
  { id: 3, name: 'Gemini Pro', provider: 'Google' },
  { id: 4, name: 'Mistral Large', provider: 'Mistral' },
]

const ChatGrid: React.FC = () => {
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
