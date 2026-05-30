# Jarvis API Documentation

## WebSocket Connection

```javascript
// Client-side
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => console.log('Connected');

ws.send(JSON.stringify({
  type: 'voice_input',
  content: 'Bonjour Jarvis'
}));
```

## Message Types

### Voice Input
```json
{
  "type": "voice_input",
  "content": "transcribed text",
  "language": "fr"
}
```

### Agent Task
```json
{
  "type": "agent_task",
  "task": "calculate 2+2",
  "context": {}
}
```

### Automation Request
```json
{
  "type": "automation",
  "workflow": "send_email",
  "params": {
    "to": "user@example.com",
    "subject": "Hello"
  }
}
```

### Device Control
```json
{
  "type": "device_control",
  "device_id": "light_1",
  "command": "on",
  "value": null
}
```

## REST Endpoints (optional)

### Health Check
```bash
GET /health
```

### Transcribe Audio
```bash
POST /api/transcribe
Content-Type: multipart/form-data

file: <audio_file>
language: fr
```

### Get Smart Devices
```bash
GET /api/devices
Authorization: Bearer <token>
```

### Control Device
```bash
POST /api/devices/{device_id}/control
Content-Type: application/json
Authorization: Bearer <token>

{
  "command": "on",
  "value": null
}
```

### Trigger Automation
```bash
POST /api/automations/trigger
Content-Type: application/json
Authorization: Bearer <token>

{
  "workflow": "workflow_name",
  "params": {}
}
```

## Response Format

### Success
```json
{
  "type": "response",
  "message": "Response text",
  "data": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Error
```json
{
  "type": "error",
  "message": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Voice Response
```json
{
  "type": "voice_response",
  "text": "Response text",
  "audio": "base64_encoded_audio",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Examples

### JavaScript Client
```javascript
class JarvisClient {
  constructor(url = 'ws://localhost:8000/ws') {
    this.ws = new WebSocket(url);
    this.ws.onmessage = (event) => this.handleMessage(event);
  }

  send(type, data) {
    this.ws.send(JSON.stringify({ type, ...data }));
  }

  handleMessage(event) {
    const message = JSON.parse(event.data);
    console.log('Jarvis:', message);
  }
}

const jarvis = new JarvisClient();
jarvis.send('voice_input', { content: 'Allume la lumière' });
```

### Python Client
```python
import asyncio
import websockets
import json

async def main():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "type": "voice_input",
            "content": "Quel est le résultat de 2+2?"
        }))
        
        response = await ws.recv()
        print("Jarvis:", json.loads(response))

asyncio.run(main())
```
