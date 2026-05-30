# 📚 JARVIS V2 - GUIDE DE RÉFÉRENCE COMPLET

## 1️⃣ LES APIs À UTILISER

### 1.1 OpenAI Realtime API (CRITIQUE!)

**Pourquoi:** Voice fluide < 1 sec latency

```python
# Installation
pip install openai websockets

# Setup
from openai import OpenAI

client = OpenAI(api_key="sk_...")

# Realtime WebSocket
async def realtime_voice():
    async with client.beta.realtime.connect({
        "model": "gpt-4-realtime-preview-20250121",
        "voice": "amber",  # ou nova, shimmer, etc
    }) as connection:
        
        # Recevoir transcription live
        async for event in connection:
            if event.type == "response.text.delta":
                print(f"Transcription: {event.text}")
            if event.type == "response.audio.delta":
                play_audio(event.audio)  # Stream audio
            if event.type == "response.done":
                log_memory(event.full_response)

# Config
REALTIME_CONFIG = {
    "model": "gpt-4-realtime-preview-20250121",
    "instructions": """Tu es Jarvis, assistant IA personnel.
    - Réponds rapidement et naturellement
    - Utilise le contexte de l'utilisateur
    - Sois concis mais utile""",
    "voice": "amber",  # Natural, confident
    "temperature": 0.7,
}
```

**Docs:** https://platform.openai.com/docs/guides/realtime

---

### 1.2 OpenAI Standard APIs

```python
# GPT-4 Chat Completion (pour le backend)
response = await client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Tu es Jarvis..."},
        {"role": "user", "content": "Analyse ces notes"}
    ],
    temperature=0.7,
)

# Embeddings (pour mémoire + recherche)
embedding = await client.embeddings.create(
    input="Mon projet principal est ONZ",
    model="text-embedding-3-small"
)

# Batch API (si beaucoup de requêtes)
batch_job = await client.batches.create(
    input_file_id="file_...",
    endpoint="/v1/chat/completions",
)
```

---

### 1.3 Google Calendar API (Morning Briefing)

```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Setup
credentials = Credentials.from_service_account_file('creds.json')
calendar_service = build('calendar', 'v3', credentials=credentials)

# Fetch events
async def get_today_events():
    events = calendar_service.events().list(
        calendarId='primary',
        timeMin=today_start,
        timeMax=today_end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events.get('items', [])
    # Returns: [{"summary": "Meeting", "start": {...}, ...}]
```

---

### 1.4 Gmail API (Emails)

```python
from google.auth.transport.requests import Request

# Setup
gmail_service = build('gmail', 'v1', credentials=credentials)

# Fetch priority emails
async def get_priority_emails():
    results = gmail_service.users().messages().list(
        userId='me',
        q='is:important OR from:manager@company.com',
        maxResults=5
    ).execute()
    
    messages = []
    for msg in results.get('messages', []):
        msg_data = gmail_service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata'
        ).execute()
        messages.append({
            "from": msg_data['payload']['headers'][...],
            "subject": msg_data['payload']['headers'][...],
        })
    
    return messages
```

---

### 1.5 Redis (Memory System)

```python
import redis
import json

# Setup
redis_client = redis.asyncio.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

# Save user memory
async def save_to_memory(user_id, key, value):
    memory_key = f"user:{user_id}:memory:{key}"
    await redis_client.set(memory_key, json.dumps(value))

# Retrieve
async def get_from_memory(user_id, key):
    memory_key = f"user:{user_id}:memory:{key}"
    data = await redis_client.get(memory_key)
    return json.loads(data) if data else None

# Example
await save_to_memory("user_123", "main_project", {
    "name": "ONZ Transport",
    "description": "Urban communication platform",
    "priority": "high"
})

# Later
project = await get_from_memory("user_123", "main_project")
# Returns: {"name": "ONZ Transport", ...}
```

---

### 1.6 n8n Webhooks (Automations)

```python
import httpx

# Trigger n8n workflow
async def trigger_n8n_workflow(workflow_id, data):
    webhook_url = f"https://your-n8n.com/webhook/{workflow_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            webhook_url,
            json={
                "action": "create_plan",
                "user_id": data.get("user_id"),
                "content": data.get("content"),
                "metadata": data.get("metadata")
            },
            timeout=30.0
        )
    
    return response.json()

# Example
result = await trigger_n8n_workflow(
    "morning_briefing",
    {
        "user_id": "abou",
        "content": "Send summary email",
        "metadata": {"email": "abou@example.com"}
    }
)
```

---

### 1.7 Hostinger API (Optional - Deployment)

```python
# Pour automatiser deployment
import httpx

HOSTINGER_API = "https://api.hostinger.com/v1"
API_KEY = "your_hostinger_key"

async def deploy_to_hostinger(app_name, docker_image):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HOSTINGER_API}/applications",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "name": app_name,
                "image": docker_image,
                "environment": {
                    "OPENAI_API_KEY": "...",
                    "REDIS_URL": "redis://...",
                }
            }
        )
    
    return response.json()
```

---

## 2️⃣ DESIGN PATTERNS

### 2.1 Architecture Next.js

```
jarvis/
├── app/
│   ├── layout.tsx           (Root layout)
│   ├── page.tsx             (Home - Main voice UI)
│   ├── dashboard/
│   │   └── page.tsx         (Dashboard - After "start day")
│   ├── api/
│   │   ├── voice/route.ts   (WebSocket for Realtime)
│   │   ├── memory/route.ts  (Get/Save memory)
│   │   ├── briefing/route.ts (Morning briefing)
│   │   ├── agent/route.ts   (Smart agent)
│   │   └── n8n/route.ts     (Trigger automations)
│   └── globals.css
├── components/
│   ├── VoiceInput.tsx       (Mic + waveform)
│   ├── Dashboard.tsx        (Agenda + emails)
│   ├── Orb.tsx             (Central animated orb)
│   ├── Suggestions.tsx      (Floating copilot)
│   └── FallbackUI.tsx       (Offline mode)
├── lib/
│   ├── openai.ts           (API client)
│   ├── redis.ts            (Memory client)
│   ├── calendar.ts         (Google Calendar)
│   ├── gmail.ts            (Gmail)
│   └── n8n.ts              (n8n webhook)
├── hooks/
│   ├── useVoice.ts         (Voice state management)
│   ├── useMemory.ts        (Memory access)
│   └── useDashboard.ts     (Dashboard data)
└── types/
    └── index.ts            (TypeScript types)
```

---

### 2.2 Component Pattern (Voice Input)

```tsx
// components/VoiceInput.tsx
'use client'

import { useVoice } from '@/hooks/useVoice'
import { Orb } from './Orb'
import { Waveform } from './Waveform'
import { LiveTranscript } from './LiveTranscript'

export function VoiceInput() {
  const {
    isListening,
    transcript,
    response,
    audioLevel,
    startVoice,
    stopVoice
  } = useVoice()

  return (
    <div className="voice-container">
      {/* Central Orb - animated based on state */}
      <Orb 
        isListening={isListening}
        audioLevel={audioLevel}
      />
      
      {/* Waveform - real-time audio visualization */}
      <Waveform audioLevel={audioLevel} />
      
      {/* Live Transcript - top right */}
      <LiveTranscript text={transcript} />
      
      {/* Mic Button */}
      <button
        onClick={isListening ? stopVoice : startVoice}
        className="mic-button"
      >
        {isListening ? '🛑 Stop' : '🎤 Speak'}
      </button>
    </div>
  )
}
```

---

### 2.3 Hook Pattern (Voice Management)

```tsx
// hooks/useVoice.ts
'use client'

import { useState, useEffect, useRef } from 'react'

export function useVoice() {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [audioLevel, setAudioLevel] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => console.log('✓ Connected')
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'transcript') {
        setTranscript(data.text)
      }
      if (data.type === 'response') {
        setResponse(data.text)
      }
      if (data.type === 'audio_level') {
        setAudioLevel(data.level)
      }
    }
    
    wsRef.current = ws
    
    return () => ws.close()
  }, [])

  const startVoice = async () => {
    setIsListening(true)
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    // Audio handling...
  }

  const stopVoice = () => {
    setIsListening(false)
    // Send to backend
    wsRef.current?.send(JSON.stringify({
      type: 'voice_complete',
      transcript
    }))
  }

  return { isListening, transcript, response, audioLevel, startVoice, stopVoice }
}
```

---

### 2.4 API Route Pattern (Backend)

```ts
// app/api/briefing/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getEvents } from '@/lib/calendar'
import { getPriorityEmails } from '@/lib/gmail'
import { getMemory } from '@/lib/redis'

export async function POST(request: NextRequest) {
  try {
    const { userId } = await request.json()

    // Fetch in parallel
    const [events, emails, userMemory] = await Promise.all([
      getEvents(userId),
      getPriorityEmails(userId),
      getMemory(userId, 'preferences')
    ])

    // Format response
    const briefing = {
      calendar: events.slice(0, 3),
      emails: emails.slice(0, 2),
      weather: await getWeather(),
      userContext: userMemory,
      timestamp: new Date().toISOString()
    }

    return NextResponse.json(briefing)
  } catch (error) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    )
  }
}
```

---

## 3️⃣ TESTING AVEC PLAYWRIGHT

### 3.1 Setup Playwright

```bash
npm install -D @playwright/test

# Create config
npx playwright install
```

---

### 3.2 Test Voice Latency

```typescript
// tests/voice-latency.spec.ts
import { test, expect } from '@playwright/test'

test('Voice latency should be < 1 second', async ({ page }) => {
  await page.goto('http://localhost:3000')
  
  const startTime = Date.now()
  
  // Click mic button
  await page.click('[data-testid="mic-button"]')
  
  // Simulate voice input (mock)
  await page.evaluate(() => {
    window.simulateVoiceInput('Bonjour Jarvis')
  })
  
  // Wait for response
  const responseText = await page.locator('[data-testid="response"]')
  await responseText.waitFor({ timeout: 1000 })
  
  const latency = Date.now() - startTime
  
  expect(latency).toBeLessThan(1000) // < 1 sec
  expect(await responseText.textContent()).toContain('Bonjour')
})
```

---

### 3.3 Test Dashboard

```typescript
// tests/dashboard.spec.ts
test('Dashboard loads events correctly', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard')
  
  // Check calendar events
  const events = page.locator('[data-testid="event-card"]')
  const count = await events.count()
  
  expect(count).toBeGreaterThan(0)
  
  // Check emails
  const emails = page.locator('[data-testid="email-item"]')
  expect(await emails.first().textContent()).toContain('important')
})
```

---

### 3.4 Test Fallback

```typescript
// tests/fallback.spec.ts
test('Should handle API failure gracefully', async ({ page }) => {
  // Simulate network error
  await page.context().setOffline(true)
  
  await page.goto('http://localhost:3000')
  
  // Should show offline UI
  const offlineMessage = page.locator('[data-testid="offline-mode"]')
  await expect(offlineMessage).toBeVisible()
  
  // Should allow voice input still
  await page.click('[data-testid="mic-button"]')
  const isMicActive = await page.locator('[data-testid="mic-button"]')
    .evaluate(el => el.classList.contains('listening'))
  
  expect(isMicActive).toBe(true)
})
```

---

## 4️⃣ MCP (Model Context Protocol)

### 4.1 Qu'est-ce que c'est?

MCP = Un standard pour que les LLMs accèdent à des tools/données externes

C'est utilisé par Claude, ChatGPT, etc. pour:
- Lire des fichiers
- Exécuter du code
- Accéder à des APIs
- Utiliser des outils spécialisés

---

### 4.2 MCP Server pour Jarvis

Si tu veux que d'autres LLMs puissent utiliser Jarvis:

```python
# mcp_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("jarvis")

@app.call_tool()
async def get_briefing(userId: str) -> TextContent:
    """Get user's morning briefing"""
    briefing = await get_user_briefing(userId)
    return TextContent(text=f"""
    Briefing for {userId}:
    - Events: {briefing['events']}
    - Emails: {briefing['emails']}
    - Weather: {briefing['weather']}
    """)

@app.call_tool()
async def create_task(userId: str, task: str) -> TextContent:
    """Create a task for user"""
    task_id = await save_task(userId, task)
    return TextContent(text=f"Task created: {task_id}")

@app.call_tool()
async def save_memory(userId: str, key: str, value: str) -> TextContent:
    """Save to user memory"""
    await redis_save(userId, key, value)
    return TextContent(text=f"Saved: {key}")

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000)
```

---

## 5️⃣ SKILLS DISPONIBLES

Tu peux utiliser ces skills dans Copilot:

### 5.1 Agent Customization
```
/skill agent-customization

Permet de créer/modifier des fichiers .instructions.md
Utile pour: Instructions personnalisées, troubleshooting
```

### 5.2 Chronicle
```
/skill chronicle

Analyse ta session history
Utile pour: Standup reports, usage tips
```

### 5.3 Troubleshoot
```
/skill troubleshoot

Debug logs et behavior analysis
Utile pour: Debugger pourquoi quelquechose ne marche pas
```

### 5.4 Update Skills
```
/skill update-skills

Créer/updater des repository skills
Utile pour: Documenter patterns découverts
```

---

## 6️⃣ AUTRES OUTILS UTILES

### 6.1 GitHub Actions (CI/CD)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Hostinger

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t jarvis:latest .
      - name: Push to registry
        run: docker push your-registry/jarvis:latest
      - name: Deploy to Hostinger
        run: |
          ssh user@hostinger "cd /app && docker-compose pull && docker-compose up -d"
```

---

### 6.2 Docker Compose (Local Dev)

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: jarvis
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://postgres:password@postgres:5432/jarvis
    depends_on:
      - redis
      - postgres

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

---

### 6.3 Environment Variables (.env)

```bash
# .env.local (never commit!)
OPENAI_API_KEY=sk_...
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost:5432/jarvis

# APIs
GOOGLE_CALENDAR_KEY=...
GOOGLE_CALENDAR_SECRET=...
GMAIL_CREDENTIALS=...

# n8n
N8N_WEBHOOK_URL=https://your-n8n.com/webhook

# Hostinger
HOSTINGER_API_KEY=...
HOSTINGER_DOMAIN=your-domain.com

# Development
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### 6.4 TypeScript Types

```typescript
// types/index.ts

export interface UserMemory {
  userId: string
  projects: Array<{
    name: string
    description: string
    priority: 'high' | 'medium' | 'low'
  }>
  preferences: {
    timezone: string
    language: string
    voice: string
  }
  contacts: Record<string, string>
  lastSession: Date
}

export interface BriefingData {
  calendar: Array<{
    summary: string
    start: Date
    end: Date
    location?: string
  }>
  emails: Array<{
    from: string
    subject: string
    priority: boolean
  }>
  weather: {
    temperature: number
    condition: string
    location: string
  }
  tasks?: string[]
}

export interface VoiceEvent {
  type: 'transcript' | 'response' | 'audio_level' | 'error'
  data: unknown
  timestamp: Date
}
```

---

## 7️⃣ CHECKLIST AVANT DÉMARRAGE V2

```
Infrastructure:
☐ OpenAI API key ready
☐ Google Calendar API setup
☐ Gmail API setup
☐ Redis instance running
☐ PostgreSQL database ready

Development:
☐ Node.js 18+ installed
☐ Next.js project created
☐ Tailwind CSS configured
☐ Framer Motion installed

Testing:
☐ Playwright installed
☐ Test files created
☐ Mock APIs ready

Deployment:
☐ Docker installed
☐ Hostinger account ready
☐ Domain configured
☐ SSL certificate ready

Documentation:
☐ API endpoints documented
☐ Deployment guide created
☐ Fallback scenarios defined
☐ Presentation script written
```

---

## 8️⃣ LIENS IMPORTANTS

```
Documentation:
- OpenAI: https://platform.openai.com/docs
- Next.js: https://nextjs.org/docs
- Playwright: https://playwright.dev
- Redis: https://redis.io/docs
- n8n: https://docs.n8n.io

APIs:
- Google Calendar: https://developers.google.com/calendar
- Gmail: https://developers.google.com/gmail/api
- Hostinger: https://support.hostinger.com/en/articles/4291385

Libraries:
- OpenAI SDK: https://github.com/openai/openai-python
- Framer Motion: https://www.framer.com/motion
- Tailwind CSS: https://tailwindcss.com
```

---

## 🎯 RÉSUMÉ POUR LANCER V2

```
APIs principales: OpenAI Realtime, Google Calendar, Gmail, Redis
Design: Next.js 14, Tailwind, Framer Motion, TypeScript
Testing: Playwright pour latency + fallback tests
Deployment: Docker + Hostinger VPS
Structure: 3 use cases sharp, fallback scenarios, professional
```
