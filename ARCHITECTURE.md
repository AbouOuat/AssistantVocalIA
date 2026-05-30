# Architecture de Jarvis

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vite)                    │
│  VoiceInput (🎤) → Chat UI → WebSocket Client              │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket (ws://)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 BACKEND (FastAPI/Python)                    │
├─────────────────────────────────────────────────────────────┤
│ WebSocket Manager                                           │
│ ├─ Message Router                                           │
│ └─ Connection Pool                                          │
├─────────────────────────────────────────────────────────────┤
│ SERVICES LAYER                                              │
│ ├─ Voice Service (STT/TTS)                                  │
│ │  ├─ Whisper (OpenAI STT)                                  │
│ │  └─ TTS (OpenAI Text-to-Speech)                           │
│ │                                                           │
│ ├─ AI Service (Conversation)                                │
│ │  ├─ GPT-4 (LLM)                                           │
│ │  ├─ Context Manager                                       │
│ │  └─ Streaming                                             │
│ │                                                           │
│ ├─ Agents Service (LangChain)                               │
│ │  ├─ Web Search                                            │
│ │  ├─ Calculator                                            │
│ │  ├─ Device Control                                        │
│ │  └─ Custom Tools                                          │
│ │                                                           │
│ ├─ n8n Integration Service                                  │
│ │  ├─ Workflow Trigger                                      │
│ │  ├─ Workflow List                                         │
│ │  └─ Execution Tracking                                    │
│ │                                                           │
│ └─ Domotics Service (Smart Home)                            │
│    ├─ Device Registry                                       │
│    ├─ Control Logic                                         │
│    └─ Status Tracking                                       │
├─────────────────────────────────────────────────────────────┤
│ DATABASE (PostgreSQL)                                        │
│ ├─ Users                                                    │
│ ├─ Conversations                                            │
│ ├─ Messages                                                 │
│ ├─ Devices                                                  │
│ ├─ Automations                                              │
│ └─ Sessions                                                 │
├─────────────────────────────────────────────────────────────┤
│ EXTERNAL SERVICES                                            │
│ ├─ OpenAI (GPT-4, Whisper, TTS)                             │
│ ├─ n8n (Workflows)                                          │
│ └─ Smart Home APIs                                          │
└─────────────────────────────────────────────────────────────┘
```

## Flux de Communication

### 1. Voice Input Flow
```
User speaks
    ↓
VoiceInput.tsx (records audio)
    ↓
WebSocket.send(audio_bytes)
    ↓
Backend.websocket_handler()
    ↓
voice_service.transcribe_audio() [Whisper]
    ↓
ai_service.chat_completion(text) [GPT-4]
    ↓
voice_service.text_to_speech() [TTS]
    ↓
WebSocket.send(response + audio)
    ↓
Frontend displays + plays audio
```

### 2. Agent Task Flow
```
User: "Calculate 2+2"
    ↓
ai_service.chat_completion()
    ↓
LangChain Agent detects task
    ↓
agents_service.execute_agent_task()
    ↓
Tools available:
  - calculator → eval("2+2") → 4
  - web_search
  - get_time
  - device_control
    ↓
GPT-4 formats response
    ↓
Response sent to user
```

### 3. Automation Flow
```
User: "Envoie un email"
    ↓
ai_service.chat_completion()
    ↓
LangChain Agent matches workflow
    ↓
n8n_service.trigger_automation("send_email", params)
    ↓
POST https://n8n-instance/workflows/send_email/execute
    ↓
n8n executes workflow
    ↓
Response returned to user
```

### 4. Device Control Flow
```
User: "Allume la lumière"
    ↓
ai_service.chat_completion()
    ↓
LangChain Agent calls control_smart_device()
    ↓
domotics_service.control_device("light_1", "on")
    ↓
Database updates device status
    ↓
Response: "Lumière du salon allumée"
```

## Directory Structure (Optimized)

```
projet-jarvis/
├── README.md                 # Main documentation
├── API.md                    # API reference
├── ARCHITECTURE.md           # This file
├── .env.example             # Environment template
├── docker-compose.yml       # Docker orchestration
├── Dockerfile.backend       # Backend container
├── Dockerfile.frontend      # Frontend container
│
├── backend_*.py             # Backend modules (organized as needed)
│   ├── backend_main.py      # FastAPI app + WebSocket
│   ├── backend_config.py    # Configuration
│   ├── backend_voice_service.py
│   ├── backend_ai_service.py
│   ├── backend_agents_service.py
│   ├── backend_n8n_service.py
│   └── backend_domotics_service.py
│
├── frontend_*.tsx           # Frontend components (organized as needed)
│   ├── frontend_App.tsx     # Main component
│   ├── frontend_VoiceInput.tsx
│   ├── frontend_Chat.tsx
│   ├── frontend_package.json
│   └── frontend_vite.config.ts
│
└── requirements_backend.txt # Python dependencies
```

## Key Design Decisions

### 1. WebSocket for Real-time Communication
- ✅ Bidirectional communication
- ✅ Low latency
- ✅ Perfect for voice streaming
- ✅ Automatic reconnection handling

### 2. Service-based Architecture
- ✅ Separation of concerns
- ✅ Easy to test
- ✅ Scalable
- ✅ Can replace services independently

### 3. LangChain for Agents
- ✅ Built-in tool management
- ✅ Natural language understanding
- ✅ Easy to add new tools
- ✅ Chain multiple actions

### 4. PostgreSQL for Persistence
- ✅ ACID transactions
- ✅ Reliable for conversation history
- ✅ Good for user/device management
- ✅ Works well with SQLAlchemy

### 5. Docker for Deployment
- ✅ Reproducible environments
- ✅ Easy scaling
- ✅ Compatible with Hostinger VPS
- ✅ Clean separation of services

## Performance Considerations

- **Streaming**: Use streaming responses for better perceived performance
- **Caching**: Cache frequently used information (device list, user context)
- **Async/Await**: All I/O operations are non-blocking
- **Connection Pooling**: Database and HTTP connections reused
- **Rate Limiting**: Implement for API endpoints

## Security Considerations

- **JWT Tokens**: Authentication for REST endpoints
- **WebSocket Auth**: Token validation on WebSocket handshake
- **API Keys**: Stored in .env, never in code
- **Input Validation**: Pydantic models validate all inputs
- **CORS**: Configured for frontend origin
- **HTTPS**: Use in production (configure reverse proxy)

## Deployment to Hostinger VPS

1. Clone repository on VPS
2. Install Docker
3. Configure .env with production keys
4. Build images: `docker-compose build`
5. Start services: `docker-compose up -d`
6. Configure reverse proxy (nginx) for SSL/HTTPS
7. Set up PostgreSQL backup strategy

## Next Steps

- [ ] Implement database models
- [ ] Add REST endpoints for device management
- [ ] Implement authentication/JWT
- [ ] Add comprehensive error handling
- [ ] Set up logging and monitoring
- [ ] Create test suite
- [ ] Document deployment process
