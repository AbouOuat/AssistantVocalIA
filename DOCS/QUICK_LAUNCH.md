# 🚀 JARVIS V2 - QUICK LAUNCH GUIDE

## START HERE - Pour les 4 jours

---

## DAY 1 (MERCREDI) - FOUNDATION

### Morning (2-3h): Frontend Scaffold

```bash
# 1. Create Next.js project
npx create-next-app@latest jarvis-v2 --typescript --tailwind --app
cd jarvis-v2

# 2. Install dependencies
npm install framer-motion openai @openai/realtime-sdk

# 3. Create directory structure
mkdir -p app/api app/components app/hooks app/lib app/types

# 4. Setup environment
cp .env.example .env.local
# Fill in: OPENAI_API_KEY, NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Afternoon (1.5-2h): Realtime API Integration

```bash
# Test OpenAI Realtime API connection
npx ts-node scripts/test-realtime.ts

# Should output: "✓ Connected to Realtime API"
# Latency: ~200ms
```

### Evening (1-1.5h): Component Scaffolding

```bash
# Create main components
touch app/components/{Orb,Waveform,VoiceInput,Dashboard}.tsx
touch app/hooks/{useVoice,useMemory}.ts

# Create API routes
touch app/api/{briefing,memory,agent,n8n}/route.ts
```

**Day 1 Goal: ✓ Frontend ready, Voice API connected, < 500ms latency verified**

---

## DAY 2 (JEUDI) - USE CASES

### Morning (2h): USE CASE 1 - Morning Briefing

```typescript
// app/api/briefing/route.ts
export async function POST(req: Request) {
  const { userId } = await req.json()
  
  const [events, emails, weather] = await Promise.all([
    getCalendarEvents(userId),
    getEmails(userId),
    getWeather()
  ])
  
  // Format as voice response
  const briefing = `
    Bonjour. Tu as ${events.length} réunions.
    ${emails.length} emails prioritaires.
    ${weather.temp}°C, ${weather.condition}.
  `
  
  return Response.json({ briefing, events, emails, weather })
}
```

### Midday (1.5h): USE CASE 2 - Smart Agent

```typescript
// app/api/agent/route.ts
export async function POST(req: Request) {
  const { userId, request } = await req.json()
  
  // 1. Get user context from memory
  const memory = await getMemory(userId)
  
  // 2. Analyze with GPT-4
  const analysis = await gpt4_analyze(request, memory)
  
  // 3. Create action items
  const tasks = await create_tasks(userId, analysis)
  
  // 4. Draft email
  const emailDraft = await draft_email(analysis)
  
  return Response.json({ 
    analysis, 
    tasks, 
    emailDraft 
  })
}
```

### Afternoon (1.5h): USE CASE 3 - Memory

```typescript
// app/api/memory/route.ts
export async function POST(req: Request) {
  const { userId, key, value } = await req.json()
  
  // Save to Redis
  await redis.set(`user:${userId}:memory:${key}`, JSON.stringify(value))
  
  // Update system prompt with new context
  const allMemory = await getFullMemory(userId)
  updateSystemPrompt(userId, allMemory)
  
  return Response.json({ success: true })
}

export async function GET(req: Request) {
  const { userId, key } = new URL(req.url).searchParams
  
  const value = await redis.get(`user:${userId}:memory:${key}`)
  
  return Response.json(JSON.parse(value))
}
```

**Day 2 Goal: ✓ All 3 use cases working, tested locally, latency < 1 sec**

---

## DAY 3 (VENDREDI) - DEPLOYMENT & POLISH

### Morning (2h): UI Polish + Animations

```tsx
// components/Orb.tsx - Add Framer Motion
import { motion } from 'framer-motion'

export function Orb({ isListening }: { isListening: boolean }) {
  return (
    <motion.div
      className="orb"
      animate={{
        scale: isListening ? 1.1 : 1,
        opacity: isListening ? 1 : 0.7,
      }}
      transition={{ duration: 0.5, repeat: isListening ? Infinity : 0 }}
    />
  )
}
```

### Midday (1.5h): Deploy to Hostinger

```bash
# 1. Build Docker image
docker build -t jarvis-v2:latest .

# 2. Push to registry
docker tag jarvis-v2:latest your-docker-registry/jarvis-v2:latest
docker push your-docker-registry/jarvis-v2:latest

# 3. SSH to Hostinger
ssh user@your-vps-ip

# 4. Pull and run
cd /app
docker-compose pull
docker-compose up -d

# 5. Verify
curl https://your-domain.com/api/health
```

### Afternoon (1.5h): Fallback Scenarios

```typescript
// lib/fallback.ts
export const FALLBACK_RESPONSES = {
  briefing: {
    text: "Mode offline - voici votre dernier résumé",
    events: [],
    emails: [],
    weather: { temp: 20, condition: "unknown" }
  },
  agent: {
    text: "Mode offline - fonction disponible en ligne",
    tasks: [],
    emailDraft: ""
  },
  error: {
    text: "Désolé, quelque chose a mal tourné. Réessayez."
  }
}

// Use in API routes
try {
  return Response.json(actualData)
} catch (error) {
  return Response.json(FALLBACK_RESPONSES.briefing, { status: 503 })
}
```

**Day 3 Goal: ✓ Live on Hostinger, UI polished, fallback ready**

---

## DAY 4 (SAMEDI) - PRESENTATION DAY

### Morning (1h): Final Checks

```bash
# Test on VPS
curl https://your-domain.com
# Check latency
time curl https://your-domain.com/api/briefing

# Test fallbacks
# (Kill Redis/API, verify graceful fallback)

# Test on phone
# (Responsive design, voice works)

# Verify video backup
# (Exists and plays)
```

### Afternoon: Presentation

**Timeline:**
```
0:00-0:20  HOOK
"Les assistants répondent. Jarvis agit."

0:20-1:30  DÉMO 1: Fluidité
"Jarvis, start my day"
[Shows instant response, dashboard builds]

1:30-2:30  DÉMO 2: Intelligence
"Analyze my notes and create plan"
[Shows agent working, tasks created]

2:30-3:30  DÉMO 3: Mémoire
"Remember my project"
"What's my project?"
[Shows context-aware response]

3:30-4:20  Why it matters
Architecture insight, vision pitch

4:20-5:00  Call to action
GitHub link, thank you
```

---

## 📋 CRITICAL CHECKLIST

Before presentation, verify:

```
Voice & Latency
☐ Voice latency < 1 sec (test 5x)
☐ Fallback text input ready
☐ Offline mode tested
☐ Audio quality good

Demo & Script
☐ Script memorized
☐ Timing exact (4:50)
☐ Transitions smooth
☐ Backup video ready

Technical
☐ All APIs responding
☐ Database queries fast
☐ Memory system working
☐ Animations smooth (60 FPS)

Presentation
☐ Outfit ready
☐ Confidence high
☐ Voice calm
☐ Smile ready
```

---

## 🆘 TROUBLESHOOTING QUICK FIXES

### Latency Too High (> 2 sec)
```
1. Check OpenAI API status (is_online)
2. Test with simple "Hi" → response
3. Check network latency: ping api.openai.com
4. Fallback to text input if needed
```

### Voice Not Working
```
1. Check microphone permissions (browser)
2. Check OpenAI Realtime API key validity
3. Check WebSocket connection: wscat
4. Fallback to text input immediately
```

### Memory Not Persisting
```
1. Check Redis connection: redis-cli ping
2. Check memory key format: user:{id}:memory:{key}
3. Check system prompt includes memory context
4. Fallback to stateless responses if needed
```

### Slow Dashboard Load
```
1. Check calendar API latency
2. Add skeleton loaders
3. Load events in parallel
4. Cache results for 5 minutes
```

---

## 🎯 SUCCESS CRITERIA

After 4 days, you should have:

```
✅ Latency < 1 sec (voice responsive)
✅ 3 use cases fully working
✅ UI premium (not perfect, but pro)
✅ Deployed live on Hostinger
✅ Fallback scenarios ready
✅ Presentation script rehearsed
✅ Backup video prepared
✅ Confidence high
```

---

## 📞 REFERENCE DOCS

During development, refer to:

- `REFERENCE_COMPLETE.md` - APIs, patterns, libraries
- `JARVIS_V2_4DAYS.md` - Timeline and strategy
- `SESSION_PROMPTS.md` - Prompts for new sessions
- `MON_AVIS_HONNETE.md` - Feedback analysis

---

## 🚀 LET'S GO!

**Day 1:** Foundation
**Day 2:** Features  
**Day 3:** Deploy
**Day 4:** Win! 🏆

You've got this! 💪

---

## 💡 FINAL TIPS

1. **Focus**: 1 excellent feature > 5 mediocre features
2. **Latency**: Test obsessively - this is what juges feel
3. **Fallback**: Professional preparation wins trust
4. **Confidence**: You know your code - show it!
5. **Energy**: Smile, speak clearly, believe in it

**Go build something amazing!** 🎉
