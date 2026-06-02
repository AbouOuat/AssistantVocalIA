# Jarvis V2 - Agent Instructions

You are helping build **Jarvis V2**, an AI voice assistant winning a hackathon in 4 days.

## CONTEXT

**Project:** Jarvis - Personal OS conversational vocal en temps réel
**Hackathon:** 4 days remaining
**Goal:** Build a winning demo that's also commercially viable
**Stack:** Next.js + FastAPI + OpenAI Realtime API

## CRITICAL SUCCESS FACTORS

1. **Latency < 1 second** (judges FEEL this)
   - Use OpenAI Realtime API (not Whisper chain)
   - This is the differentiator

2. **3 Sharp Demos** (not 15 generic features)
   - Morning Briefing: "Start my day"
   - Smart Agent: "Analyze notes"
   - Memory: "Remember X"

3. **Premium UI** (not perfect, but professional)
   - Dark theme: #0B1020, #4F46E5, #60A5FA
   - Framer Motion animations
   - Smooth transitions

4. **Fallback Scenarios** (professional preparation)
   - Offline mode ready
   - API failure handling
   - Text input alternative

5. **Deployed Live** (not localhost)
   - Hostinger VPS
   - Docker + nginx
   - HTTPS ready

## WHAT WINS VS WHAT LOSES

✅ WINS:
- Latency < 1 sec verified 5x
- Zero errors in demo
- Smooth animations
- Confident presenter
- Video backup ready

❌ LOSES:
- Latency > 2 sec
- Broken features
- Ugly UI
- Nervous speaker
- No fallback plan

## ARCHITECTURE

```
Frontend:    Next.js 14 (App Router)
             TypeScript
             Tailwind + Framer Motion
             
Backend:     FastAPI
             OpenAI Realtime API (WebSocket)
             PostgreSQL + Redis
             
APIs:        Google Calendar/Gmail
             n8n webhooks (optional)
             
Deploy:      Docker
             Hostinger VPS
             nginx reverse proxy
```

## DOCS LOCATION

All documentation is in: `./DOCS/`

Key files:
- **DOCS/TL_DR.md** - 2-min overview
- **DOCS/QUICK_LAUNCH.md** - Day-by-day execution
- **DOCS/REFERENCE_COMPLETE.md** - APIs + code patterns
- **DOCS/SESSION_PROMPTS.md** - Prompts for Copilot sessions
- **DOCS/JARVIS_V2_4DAYS.md** - Full strategy
- **DOCS/MON_AVIS_HONNETE.md** - Why this approach

## HOW TO USE THESE INSTRUCTIONS

When helping:

1. **Understand the 4-day constraint** - No overengineering
2. **Prioritize latency** - Test obsessively
3. **Suggest pragmatic solutions** - Copy-paste ready code
4. **Think about fallbacks** - Always have Plan B
5. **Remember the 3 use cases** - Not 15 features

## WHEN YOU SUGGEST FEATURES

Ask: "Does this help win the hackathon?"
- If YES: Suggest it
- If NO: Don't suggest it

Example:
- ❌ "Add RBAC user management" (overscope)
- ✅ "Add memory system" (shows personalization)

## KEY DECISIONS

✅ OpenAI Realtime API (fast)
✅ Next.js (faster than React)
✅ 3 focused demos (not 15 scattered)
✅ Hostinger deployment (requirement)
✅ Fallback ready (professional)
❌ Complex auth (waste of time)
❌ Advanced analytics (not for demo)
❌ Microservices (overengineering)

## TESTING MINDSET

Before any feature → Test latency:
```
Time total:      User perception
< 500ms  → "instant"
< 1000ms → "responsive"
< 2000ms → "acceptable"
> 2000ms → "dead" (lose hackathon)
```

## PRESENTATION TIPS

- Script: Word-perfect (memorized, not read)
- Timing: Exactly 4:50 (practice with timer)
- Fallback: Video backup ready
- Confidence: High (you know your code)
- Energy: Present like you mean it

## SUCCESS METRIC

After 4 days, you should have:

```
✅ Latency < 1 sec (verified)
✅ 3 demos working (no errors)
✅ UI premium (smooth animations)
✅ Deployed live (Hostinger)
✅ Fallback ready (offline mode)
✅ Script rehearsed (5-10 times)
✅ Video backup (prepared)
✅ Confidence 10/10 (ready to win)
```

---

**Version:** V2 Strategy
**Last Updated:** 2026-05-28
**Status:** Ready to code
