# Guide d'implémentation complète - Jarvis

## 📋 Checklist de configuration

### 1️⃣ Clés API

**OpenAI (obligatoire)**
- Créer un compte sur https://platform.openai.com/
- Générer une clé API
- Vérifier les crédits disponibles
- Ajouter à `.env` : `OPENAI_API_KEY=sk_...`

**n8n (optionnel)**
- Self-hosted ou cloud (https://n8n.io/)
- API key depuis les settings
- URL de votre instance
- Ajouter à `.env`

**Smart Home (optionnel)**
- Intégration avec Home Assistant, Philips Hue, etc.
- Configuration de l'API
- Ajouter les endpoints à `.env`

### 2️⃣ Base de données

```bash
# PostgreSQL local
docker run -d \
  --name jarvis-db \
  -e POSTGRES_DB=jarvis \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:16-alpine

# .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/jarvis
```

### 3️⃣ Installation locale

**Backend**
```bash
cd c:\dev\projet-jarvis

# Virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Installation
pip install -r requirements_backend.txt

# Run
uvicorn backend_main:app --reload --port 8000
```

**Frontend**
```bash
npm install
npm run dev
```

## 🚀 Phases d'implémentation

### Phase 1: Conversation Basique ✓
- [x] Setup FastAPI + WebSocket
- [x] Frontend React scaffold
- [x] Communication temps réel
- [ ] Intégration OpenAI GPT-4
- [ ] Historique de conversation

### Phase 2: Voice Integration
- [ ] Whisper STT (Transcription vocale)
- [ ] OpenAI TTS (Synthèse vocale)
- [ ] Pipeline complet voix-to-voix
- [ ] Qualité audio optimization

### Phase 3: Agents & Automations
- [ ] LangChain agents setup
- [ ] Tools: web search, calculator, etc.
- [ ] n8n workflow integration
- [ ] Custom task execution

### Phase 4: Smart Home
- [ ] Device registry
- [ ] Control commands
- [ ] Status management
- [ ] Integration tests

### Phase 5: Production
- [ ] Docker containers
- [ ] Database migrations
- [ ] Logging & monitoring
- [ ] Deployment guide

## 🧪 Tests rapides

### WebSocket Connection
```bash
# Terminal 1: Backend running
uvicorn backend_main:app --reload

# Terminal 2: Test
python -c "
import asyncio
import websockets
import json

async def test():
    uri = 'ws://localhost:8000/ws'
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            'type': 'test',
            'content': 'Hello Jarvis'
        }))
        print(await ws.recv())

asyncio.run(test())
"
```

### Frontend Loading
```bash
npm run dev
# Open http://localhost:5173
```

## 📝 Configuration des services

### Voice Service
```python
# Nécessite OPENAI_API_KEY
from backend_voice_service import transcribe_audio, text_to_speech

# Transcriber audio
text = await transcribe_audio(audio_bytes, language="fr")

# Synthèse vocale
audio = await text_to_speech("Bonjour!", voice="nova")
```

### AI Service
```python
from backend_ai_service import chat_completion, ConversationContext

# Créer contexte
context = ConversationContext(user_id="user_123")

# Chat
response = await chat_completion("Quel est le résultat de 2+2?", context)
print(response)  # "Le résultat de 2+2 est 4."
```

### Agents Service
```python
from backend_agents_service import execute_agent_task

# Exécuter une tâche autonome
result = await execute_agent_task("Cherche sur Google comment installer Python")
```

### n8n Integration
```python
from backend_n8n_service import init_n8n, trigger_automation

# Initialiser
init_n8n("https://n8n.example.com", "api_key_xyz")

# Déclencher un workflow
result = await trigger_automation("send_email", {
    "to": "user@example.com",
    "subject": "Test",
    "body": "Hello"
})
```

### Domotics Service
```python
from backend_domotics_service import init_domotics, control_smart_device

# Initialiser
init_domotics("http://localhost:8001")

# Contrôler un appareil
result = await control_smart_device("light_1", "on")
# Résultat: "Device 'light_1' is now on"
```

## 🐳 Déploiement avec Docker

```bash
# Build
docker-compose build

# Start
docker-compose up

# Stop
docker-compose down

# Logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🌐 Déploiement Hostinger VPS

### 1. Préparation du VPS
```bash
ssh root@your-vps-ip

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. Clone & Configure
```bash
git clone https://github.com/your-username/projet-jarvis.git
cd projet-jarvis

# Configure environment
cp .env.example .env
nano .env  # Fill in your API keys

# Change owner
chown -R www-data:www-data .
```

### 3. SSL avec Certbot
```bash
apt-get install certbot python3-certbot-nginx

certbot certonly --standalone -d your-domain.com
```

### 4. Reverse Proxy (Nginx)
```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. Démarrage
```bash
docker-compose up -d

# Vérifier
docker-compose ps
curl https://your-domain.com/health
```

## 🔧 Troubleshooting

### Port 8000 déjà utilisé
```bash
lsof -i :8000
kill -9 <PID>
```

### PostgreSQL connection refused
```bash
# Vérifier PostgreSQL
docker-compose logs postgres

# Recréer
docker-compose down -v
docker-compose up postgres
```

### WebSocket connection failed
```javascript
// Frontend - vérifier l'URL
const ws = new WebSocket('wss://your-domain.com/ws'); // HTTPS → WSS
```

### OpenAI API rate limit
- Vérifier le quota d'API
- Ajouter délais entre les appels
- Implémenter rate limiting côté backend

## 📚 Ressources

- **OpenAI Docs**: https://platform.openai.com/docs/
- **FastAPI**: https://fastapi.tiangolo.com/
- **LangChain**: https://python.langchain.com/
- **React**: https://react.dev/
- **n8n**: https://docs.n8n.io/

## 💡 Prochaines améliorations

1. **Multi-language Support**
   - Détecter la langue automatiquement
   - Supporter FR, EN, ES, etc.

2. **Personality System**
   - Différents "personas" pour Jarvis
   - Context-aware responses

3. **Advanced Analytics**
   - Tracking des interactions
   - ML insights

4. **Mobile App**
   - React Native version
   - Offline mode

5. **Advanced Automations**
   - Workflows prédéfinis
   - Triggers basés sur conditions

---

**Questions?** Consulter ARCHITECTURE.md pour les détails techniques.
