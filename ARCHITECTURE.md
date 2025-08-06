# Chatmux Web UI Architecture

## Overview

Chatmux is transitioning from a terminal-based UI to a modern web-based interface to overcome terminal limitations and provide a better user experience. This document outlines the architecture of the new web UI.

## Design Principles

1. **Simplicity**: Clean, intuitive interface with minimal cognitive load
2. **Real-time**: Streaming responses with WebSocket connections
3. **Responsive**: Works well on different screen sizes
4. **Extensible**: Easy to add new models or features

## UI Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                        Chatmux Header                             │
├────────────────┬────────────────┬────────────────┬────────────────┤
│   OpenAI (1)   │ Anthropic (2)  │   Google (3)   │  Mistral (4)  │
│                │                │                │                │
│ [Chat History] │ [Chat History] │ [Chat History] │ [Chat History] │
│                │                │                │                │
│                │                │                │                │
├────────────────┴────────────────┴────────────────┴────────────────┤
│ Input: Type your message here... (@1-4 to target)         [Send] │
└──────────────────────────────────────────────────────────────────┘
```

## Technical Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS for utility-first styling
- **State Management**: React Context + useReducer for chat state
- **WebSocket Client**: Native WebSocket API with reconnection logic
- **Build Tool**: Vite for fast development and optimized builds

### Backend
- **Framework**: FastAPI for async Python web server
- **WebSocket Server**: FastAPI WebSocket support
- **Model Clients**: Existing model integration code (adapted)
- **Streaming**: Server-Sent Events or WebSocket for real-time updates

## Component Architecture

### Frontend Components

```
App.tsx
├── Layout/
│   ├── Header.tsx
│   └── MainLayout.tsx
├── Chat/
│   ├── ChatGrid.tsx
│   ├── ChatWindow.tsx
│   ├── Message.tsx
│   └── MessageList.tsx
├── Input/
│   ├── InputBox.tsx
│   └── InputParser.ts
└── WebSocket/
    ├── WebSocketProvider.tsx
    └── useWebSocket.ts
```

### Backend Structure

```
chatmux/
├── api/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── websocket.py     # WebSocket handlers
│   └── models.py        # Pydantic models
├── coordinator.py       # Existing coordinator (adapted)
└── models/             # Existing model clients
```

## Data Flow

1. **User Input**:
   - User types in the input box
   - On Enter, input is parsed for @mentions
   - Message sent via WebSocket to backend

2. **Backend Processing**:
   - WebSocket handler receives message
   - Routes to appropriate model(s) based on @mentions
   - Coordinator manages concurrent API calls
   - Streams responses back via WebSocket

3. **Frontend Updates**:
   - WebSocket client receives streaming updates
   - Updates specific chat window(s)
   - Maintains chat history per window

## WebSocket Protocol

### Client → Server Messages
```typescript
interface ClientMessage {
  type: "chat" | "command";
  content: string;
  targets?: number[];  // Window numbers (1-4)
  id: string;         // Unique message ID
}
```

### Server → Client Messages
```typescript
interface ServerMessage {
  type: "stream" | "complete" | "error";
  windowId: number;   // Which window to update
  content?: string;   // Streaming content
  messageId: string;  // Links to client message
  error?: string;     // Error details if applicable
}
```

## State Management

### Frontend State
```typescript
interface AppState {
  windows: {
    [id: number]: {
      model: string;
      messages: Message[];
      isStreaming: boolean;
      error?: string;
    };
  };
  wsStatus: "connecting" | "connected" | "disconnected";
}
```

### Message Format
```typescript
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isComplete: boolean;
}
```

## Implementation Phases

### Phase 1: Basic Infrastructure
- Set up React project with TypeScript
- Create FastAPI backend with WebSocket endpoint
- Implement basic layout with CSS Grid
- Simple message sending (no streaming yet)

### Phase 2: Streaming & Real-time
- Implement WebSocket streaming protocol
- Add streaming UI updates
- Handle connection management
- Error handling and reconnection

### Phase 3: Features & Polish
- Add @mention parsing and routing
- Implement keyboard shortcuts
- Add copy functionality
- Loading states and animations

### Phase 4: Advanced Features
- Conversation history persistence
- Export functionality
- Model configuration UI
- Theme customization

## Security Considerations

1. **API Keys**: Never exposed to frontend
2. **WebSocket**: Implement proper authentication
3. **Input Validation**: Sanitize all user inputs
4. **Rate Limiting**: Prevent abuse of API calls

## Performance Considerations

1. **Virtualization**: For long chat histories
2. **Debouncing**: For input handling
3. **Lazy Loading**: For initial page load
4. **Caching**: For model configurations

## Future Enhancements

1. **Mobile Support**: Responsive design for phones/tablets
2. **More Models**: Easy to add new AI providers
3. **Collaboration**: Share chat sessions
4. **Plugins**: Extensibility system
5. **Themes**: Dark/light mode support