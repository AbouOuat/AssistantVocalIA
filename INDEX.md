# 📑 Index des fichiers du projet Jarvis

## 🎯 Par où commencer?

### Pour les impatients (5 min)
1. Lire: `README.md` (2 min)
2. Exécuter: `QUICK_TEST.md` (3 min)

### Pour comprendre en profondeur (30 min)
1. Lire: `README.md`
2. Lire: `ARCHITECTURE.md`
3. Parcourir: `API.md`
4. Lancer: `QUICK_TEST.md`

### Pour déployer en production (1h)
1. Lire: `INSTALLATION.md`
2. Configurer `.env`
3. Lire: Déploiement Hostinger VPS
4. Exécuter deployment

---

## 📚 Documentation

### README.md
**Objectif**: Vue d'ensemble générale et quick start
**Contenu**:
- Présentation du projet
- Stack technique
- Installation de base
- Usage simple
**Lire si**: Vous découvrez le projet

---

### ARCHITECTURE.md
**Objectif**: Comprendre le design complet
**Contenu**:
- Diagramme architecture
- Flux de communication
- Structure des répertoires
- Decisions de design
- Considérations de performance/sécurité
**Lire si**: Vous développez une nouvelle feature

---

### API.md
**Objectif**: Spécification technique des endpoints
**Contenu**:
- WebSocket messages format
- REST endpoints
- Exemples client (JS, Python)
**Utiliser si**: Vous écrivez un client ou intégrez une API

---

### INSTALLATION.md
**Objectif**: Installation complète et déploiement
**Contenu**:
- Setup local détaillé
- Configuration des services
- Docker setup
- Hostinger VPS deployment
- Nginx reverse proxy
- Troubleshooting
**Suivre si**: Installation ou déploiement

---

### QUICK_TEST.md
**Objectif**: Tester en 5 minutes
**Contenu**:
- Setup minimal
- Lancer backend
- Lancer frontend
- Test WebSocket
- Tests des services
**Suivre si**: Vous voulez voir ça marcher rapidement

---

### PROJECT_SUMMARY.md
**Objectif**: Résumé de ce qui a été livré
**Contenu**:
- Checklist des composants
- Phases de développement
- Points clés à retenir
- Quick start 3 commandes
**Lire si**: Vous voulez un aperçu complet

---

### DELIVERY_SUMMARY.md
**Objectif**: Résumé exécutif complet
**Contenu**:
- Mission accomplies
- Statistiques
- Feuille de route
- FAQ
- Prochaines actions
**Lire si**: Vous êtes le manager/lead

---

## 🐍 Backend Python

### backend_main.py (440 lignes)
**Rôle**: Serveur FastAPI principal + WebSocket
**Contient**:
- Initialisation FastAPI
- CORS middleware
- Endpoints `/` et `/health`
- WebSocket handler `/ws`
**Importer**: `from backend_main import app`

---

### backend_config.py (35 lignes)
**Rôle**: Configuration centralisée
**Contient**:
- Paramètres OpenAI
- Database URL
- JWT settings
- n8n configuration
- Smart home settings
**Importer**: `from backend_config import Settings, get_settings`

---

### backend_voice_service.py (45 lignes)
**Rôle**: Speech-to-Text (Whisper) + Text-to-Speech
**Fonction**:
- `transcribe_audio()` - Convertir audio en texte
- `text_to_speech()` - Convertir texte en audio
- `encode_audio_base64()` - Encoder pour transmission
- `decode_audio_base64()` - Décoder après transmission
**Dépend**: OpenAI API

---

### backend_ai_service.py (120 lignes)
**Rôle**: Conversation GPT-4 avec contexte
**Classe**: `ConversationContext` - Gère l'historique
**Fonction**:
- `chat_completion()` - Réponse GPT-4
- `chat_completion_stream()` - Streaming responses
**Dépend**: OpenAI API

---

### backend_agents_service.py (90 lignes)
**Rôle**: Agents autonomes LangChain
**Contient**: Outils (web_search, calculator, get_time, device_control)
**Fonction**: `execute_agent_task()` - Exécuter une tâche autonome
**Dépend**: LangChain, OpenAI

---

### backend_n8n_service.py (95 lignes)
**Rôle**: Intégration n8n pour automations
**Classe**: `N8nClient` - Client API n8n
**Fonction**: `trigger_automation()` - Déclencher un workflow
**Dépend**: n8n instance + API key

---

### backend_domotics_service.py (145 lignes)
**Rôle**: Contrôle appareils intelligents
**Classe**: `SmartDevice` - Représente un appareil
**Service**: `DomoticsService` - Gère tous les appareils
**Fonction**: `control_smart_device()` - Contrôler un appareil
**Dépend**: Smart home API

---

## ⚛️ Frontend TypeScript

### frontend_App.tsx (65 lignes)
**Rôle**: Composant principal React
**Contient**:
- Gestion WebSocket
- State: messages, isConnected
- Import: VoiceInput, Chat
**Props**: Reçoit voix, affiche chat

---

### frontend_VoiceInput.tsx (70 lignes)
**Rôle**: Capture audio du microphone
**Contient**:
- MediaRecorder API
- Enregistrement audio
- Appel `/api/transcribe`
**Props**: `onTranscript` callback
**Dépend**: Microphone du client

---

### frontend_Chat.tsx (50 lignes)
**Rôle**: Affichage de la conversation
**Contient**:
- Boucle des messages
- Avatar user/assistant
- Auto-scroll down
**Props**: `messages` array

---

### frontend_package.json
**Rôle**: Dépendances Node.js
**Contient**: React, TypeScript, Vite
**Scripts**: `dev`, `build`, `lint`, `preview`

---

### frontend_vite.config.ts
**Rôle**: Configuration Vite (bundler)
**Contient**:
- Proxy `/api` vers backend
- Proxy `/ws` pour WebSocket
- Port 5173

---

## 🐳 Configuration & Infrastructure

### docker-compose.yml
**Rôle**: Orchestrer tous les services
**Services**:
- PostgreSQL (database)
- Backend (FastAPI)
- Frontend (React)
**Commandes**:
- `docker-compose up` - Lancer
- `docker-compose down` - Arrêter

---

### Dockerfile.backend
**Rôle**: Container pour le backend Python
**Basé sur**: Python 3.11-slim
**Installe**: Dépendances Python
**Expose**: Port 8000

---

### Dockerfile.frontend
**Rôle**: Container pour le frontend React
**Basé sur**: Node.js 20-alpine
**Installe**: npm dependencies
**Expose**: Port 5173

---

### requirements_backend.txt
**Rôle**: Dépendances Python
**Contient**:
- FastAPI, Uvicorn
- OpenAI, LangChain
- SQLAlchemy, Psycopg2
- JWT, WebSockets
**Installer**: `pip install -r requirements_backend.txt`

---

### .env.example
**Rôle**: Template pour variables d'environnement
**Variables**:
- OPENAI_API_KEY (obligatoire)
- DATABASE_URL
- SECRET_KEY
- N8N_API_URL, N8N_API_KEY
- SMART_HOME_API
**Copier**: `cp .env.example .env`

---

## 🚀 Guides d'utilisation

### QUICKSTART.sh
**Rôle**: Script d'initialisation Linux/Mac
**Fait**:
- Crée .env
- Installe dépendances
- Affiche instructions

---

### QUICKSTART.bat
**Rôle**: Script d'initialisation Windows
**Fait**:
- Crée .env
- Venv + installation
- Instructions de démarrage

---

## 📊 Autres fichiers

### plan.md (Session workspace)
**Rôle**: Plan détaillé du projet
**Contient**: Architecture, todos, notes
**Emplacement**: `.copilot/session-state/.../plan.md`

---

## 🔍 Comment naviguer les fichiers?

### Je veux...

**...démarrer rapidement**
1. `QUICK_TEST.md` (5 min)
2. `frontend_App.tsx` (voir structure)

**...comprendre le design**
1. `ARCHITECTURE.md` (diagrammes)
2. `backend_main.py` (voir WebSocket)
3. `backend_ai_service.py` (voir AI flow)

**...ajouter une feature**
1. `ARCHITECTURE.md` (flux pertinent)
2. Créer nouveau fichier `backend_xxxxx.py`
3. Importer dans `backend_main.py`
4. Ajouter endpoint/handler

**...déployer**
1. `INSTALLATION.md` (Hostinger VPS)
2. `docker-compose.yml` (orchestration)
3. Dockerfile files (containers)

**...déboguer**
1. `QUICK_TEST.md` (troubleshooting)
2. `INSTALLATION.md` (FAQ)
3. Console du navigateur (F12)

---

## 📦 Structure de fichiers résumée

```
26 fichiers
├── Documentation (8)
│   ├── README.md ⭐
│   ├── ARCHITECTURE.md ⭐
│   ├── API.md
│   ├── INSTALLATION.md
│   ├── QUICK_TEST.md
│   ├── PROJECT_SUMMARY.md
│   ├── DELIVERY_SUMMARY.md
│   └── INDEX.md (ce fichier)
├── Backend (7 fichiers .py)
│   ├── backend_main.py ⭐
│   ├── backend_config.py
│   ├── backend_voice_service.py
│   ├── backend_ai_service.py
│   ├── backend_agents_service.py
│   ├── backend_n8n_service.py
│   └── backend_domotics_service.py
├── Frontend (5 fichiers)
│   ├── frontend_App.tsx ⭐
│   ├── frontend_VoiceInput.tsx
│   ├── frontend_Chat.tsx
│   ├── frontend_package.json
│   └── frontend_vite.config.ts
├── Configuration (5 fichiers)
│   ├── docker-compose.yml ⭐
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── requirements_backend.txt
│   └── .env.example
└── Guides (2 fichiers scripts)
    ├── QUICKSTART.sh
    └── QUICKSTART.bat

⭐ = Fichiers clés à comprendre en priorité
```

---

## 🎯 Checklist de compréhension

- [ ] J'ai lu `README.md`
- [ ] J'ai lu `ARCHITECTURE.md`
- [ ] J'ai lancé `QUICK_TEST.md`
- [ ] Je comprends le flux WebSocket
- [ ] Je peux identifier où ajouter une feature
- [ ] Je sais configurer .env
- [ ] Je peux lancer localement
- [ ] Je sais déployer sur Hostinger

---

**Prêt? Commencez par `README.md`** 🚀
