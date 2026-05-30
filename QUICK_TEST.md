# 🚀 Test rapide - 5 minutes

## Avant de commencer
1. Avoir Python 3.11+ installé
2. Avoir Node.js 18+ installé
3. Une clé OpenAI API (gratuit: https://platform.openai.com)

## Step 1: Configuration (1 min)

```bash
cd c:\dev\projet-jarvis

# Créer .env
copy .env.example .env

# Éditer .env et ajouter:
# OPENAI_API_KEY=sk_votre_clé_ici
# SECRET_KEY=votre_clé_secrète_quelconque
```

## Step 2: Backend (2 min)

**Terminal 1:**
```bash
cd c:\dev\projet-jarvis

# Créer environnement virtuel
python -m venv venv
venv\Scripts\activate.bat

# Installer dépendances
pip install -r requirements_backend.txt

# Lancer le serveur
uvicorn backend_main:app --reload --port 8000
```

✅ Vous devriez voir:
```
Uvicorn running on http://127.0.0.1:8000
```

Tester: https://localhost:8000/ dans votre navigateur
→ Réponse: `{"status":"ok","message":"Jarvis is running 🤖"}`

## Step 3: Frontend (2 min)

**Terminal 2 (nouveau):**
```bash
cd c:\dev\projet-jarvis

npm install
npm run dev
```

✅ Vous devriez voir:
```
VITE v5.0.0 ready in XXX ms
➜  Local:   http://localhost:5173/
```

Ouvrir: http://localhost:5173

## Step 4: Tester la communication (1 min)

### Dans le navigateur
```javascript
// Ouvrir console (F12)

const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('✓ Connecté à Jarvis!');
  ws.send(JSON.stringify({
    type: 'test',
    content: 'Bonjour Jarvis'
  }));
};

ws.onmessage = (event) => {
  console.log('📨 Réponse:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('❌ Erreur:', error);
};
```

✅ Vous devriez voir:
```
✓ Connecté à Jarvis!
📨 Réponse: {type: 'response', message: 'Echo: Bonjour Jarvis', ...}
```

## Étapes suivantes - Pour vraiment tester Jarvis

### 1. Conversation avec GPT-4

```python
# Terminal 3
python

from backend_ai_service import chat_completion, ConversationContext
import asyncio

async def test():
    context = ConversationContext("user_test")
    response = await chat_completion("Quel est le résultat de 2+2?", context)
    print(response)

asyncio.run(test())
```

### 2. Transcription vocale (Whisper)

```python
from backend_voice_service import transcribe_audio
import asyncio

async def test():
    # Télécharger un fichier audio WAV de test
    with open("test_audio.wav", "rb") as f:
        audio_data = f.read()
    
    text = await transcribe_audio(audio_data)
    print(f"Transcription: {text}")

asyncio.run(test())
```

### 3. Synthèse vocale (TTS)

```python
from backend_voice_service import text_to_speech
import asyncio

async def test():
    audio = await text_to_speech("Bonjour! Je suis Jarvis!", voice="nova")
    
    with open("response_audio.mp3", "wb") as f:
        f.write(audio)
    
    print("Audio sauvegardé: response_audio.mp3")

asyncio.run(test())
```

### 4. Agents autonomes (LangChain)

```python
from backend_agents_service import execute_agent_task
import asyncio

async def test():
    result = await execute_agent_task("Quel est le résultat de 2+2?")
    print(result)

asyncio.run(test())
```

### 5. Contrôle d'appareils (Domotics)

```python
from backend_domotics_service import init_domotics, control_smart_device
import asyncio

async def test():
    init_domotics("http://localhost:8001")
    
    result = await control_smart_device("light_1", "on")
    print(result)  # Device 'light_1' is now on

asyncio.run(test())
```

## Troubleshooting

### ❌ "Port 8000 already in use"
```bash
# Trouver le PID
netstat -ano | findstr :8000

# Tuer le processus (remplacer PID)
taskkill /PID <PID> /F
```

### ❌ "ModuleNotFoundError: No module named 'openai'"
```bash
# Vérifier que le venv est activé
venv\Scripts\activate.bat

# Réinstaller
pip install -r requirements_backend.txt
```

### ❌ "WebSocket connection failed"
```javascript
// Vérifier dans console du navigateur
// Le backend tourne-t-il? (http://localhost:8000)
// WebSocket utilise ws:// (pas https://)
```

### ❌ "OpenAI API Key invalid"
```bash
# Vérifier dans .env
OPENAI_API_KEY=sk_... # Commence par 'sk_'

# Ou le tester directement
python -c "from openai import OpenAI; c = OpenAI(); print('✓ API Key valide')"
```

## ✨ Que faire ensuite?

1. **Lire la documentation**
   - README.md - Vue d'ensemble
   - ARCHITECTURE.md - Comprendre le design
   - API.md - Tous les endpoints

2. **Développer une fonctionnalité**
   - Implémenter la base de données
   - Ajouter l'authentification
   - Finir le frontend (UI/UX)

3. **Tester avec de vrais appareils**
   - Intégrer avec Home Assistant
   - Connecter des appareils Philips Hue
   - Configurer les automations n8n

4. **Déployer en production**
   - Voir INSTALLATION.md pour Hostinger
   - Configurer HTTPS/SSL
   - Mettre en place monitoring

## 🎉 Succès!

Si vous voyez la réponse Echo → Vous avez maintenant une **base Jarvis entièrement fonctionnelle**!

Prêt pour le hackathon? 🚀

---

**Questions?** Consulter les fichiers de documentation dans le projet.
