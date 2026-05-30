"use client";

// PCM16 AudioWorklet — converti Float32 → Int16 avant envoi WebSocket
const WORKLET_CODE = `
class PCM16Processor extends AudioWorkletProcessor {
  process(inputs) {
    const ch = inputs[0]?.[0];
    if (!ch) return true;
    const pcm16 = new Int16Array(ch.length);
    for (let i = 0; i < ch.length; i++) {
      const s = Math.max(-1, Math.min(1, ch[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
    return true;
  }
}
try {
  registerProcessor('pcm16-processor', PCM16Processor);
} catch (e) {
  // Déjà enregistré (React StrictMode)
}
`;

const SAMPLE_RATE = 24_000;

export type RTEventType =
  | "connected"
  | "disconnected"
  | "rt_ready"
  | "rt_audio_delta"
  | "rt_transcript_delta"
  | "rt_user_transcript"
  | "rt_done"
  | "rt_error";

export interface RTEvent {
  type: RTEventType;
  audio?: string;
  text?: string;
  message?: string;
}

type RTHandler = (event: RTEvent) => void;

export class JarvisRealtime {
  private ws: WebSocket | null = null;
  private audioCtx: AudioContext | null = null;
  private workletNode: AudioWorkletNode | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private silentGain: GainNode | null = null;
  private stream: MediaStream | null = null;
  private handlers = new Set<RTHandler>();

  // Playback
  private queue: ArrayBuffer[] = [];
  private playing = false;

  // ── Connexion WebSocket ──────────────────────────────────────────────────
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const base = (process.env.NEXT_PUBLIC_BACKEND_WS_URL ?? "ws://localhost:8000/ws")
      .replace(/\/ws$/, "");
    this.ws = new WebSocket(`${base}/ws/realtime`);

    this.ws.onopen = () => this.emit({ type: "connected" });
    this.ws.onclose = () => this.emit({ type: "disconnected" });
    this.ws.onerror = () => this.emit({ type: "disconnected" });

    this.ws.onmessage = (e: MessageEvent<string>) => {
      const event = JSON.parse(e.data) as RTEvent;
      if (event.type === "rt_audio_delta" && event.audio) {
        this.enqueueAudio(event.audio);
      }
      this.emit(event);
    };
  }

  disconnect(): void {
    this.stopCapture();
    this.ws?.close();
    this.ws = null;
    this.audioCtx?.close();
    this.audioCtx = null;
  }

  // ── Capture voix ─────────────────────────────────────────────────────────
  async startCapture(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: SAMPLE_RATE, channelCount: 1, echoCancellation: true, noiseSuppression: true },
    });

    if (!this.audioCtx || this.audioCtx.state === "closed") {
      this.audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
    }
    if (this.audioCtx.state === "suspended") {
      await this.audioCtx.resume();
    }

    const blob = new Blob([WORKLET_CODE], { type: "application/javascript" });
    const url = URL.createObjectURL(blob);
    await this.audioCtx.audioWorklet.addModule(url);
    URL.revokeObjectURL(url);

    this.workletNode = new AudioWorkletNode(this.audioCtx, "pcm16-processor");
    this.sourceNode = this.audioCtx.createMediaStreamSource(this.stream);

    // Gain nul pour éviter l'écho — le nœud doit être dans le graphe pour traiter
    this.silentGain = this.audioCtx.createGain();
    this.silentGain.gain.value = 0;
    this.sourceNode.connect(this.workletNode);
    this.workletNode.connect(this.silentGain);
    this.silentGain.connect(this.audioCtx.destination);

    this.workletNode.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
      if (this.ws?.readyState !== WebSocket.OPEN) return;
      this.ws.send(JSON.stringify({
        type: "rt_audio_append",
        audio: this.arrayBufferToBase64(e.data),
      }));
    };
  }

  stopCapture(): void {
    this.workletNode?.disconnect();
    this.sourceNode?.disconnect();
    this.silentGain?.disconnect();
    this.stream?.getTracks().forEach((t) => t.stop());
    this.workletNode = null;
    this.sourceNode = null;
    this.silentGain = null;
    this.stream = null;
  }

  interrupt(): void {
    this.queue = [];
    this.playing = false;
    this.ws?.send(JSON.stringify({ type: "rt_interrupt" }));
  }

  // ── Event handlers ───────────────────────────────────────────────────────
  on(handler: RTHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  private emit(event: RTEvent): void {
    this.handlers.forEach((h) => h(event));
  }

  // ── Playback PCM16 ───────────────────────────────────────────────────────
  private enqueueAudio(b64: string): void {
    this.queue.push(this.base64ToArrayBuffer(b64));
    if (!this.playing) this.playNext();
  }

  private async playNext(): Promise<void> {
    if (!this.queue.length) {
      this.playing = false;
      return;
    }
    this.playing = true;

    if (!this.audioCtx || this.audioCtx.state === "closed") {
      this.audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
    }
    if (this.audioCtx.state === "suspended") {
      await this.audioCtx.resume();
    }

    const chunk = this.queue.shift()!;
    const pcm16 = new Int16Array(chunk);
    const float32 = new Float32Array(pcm16.length);
    for (let i = 0; i < pcm16.length; i++) {
      float32[i] = pcm16[i] / 0x8000;
    }

    const buf = this.audioCtx.createBuffer(1, float32.length, SAMPLE_RATE);
    buf.copyToChannel(float32, 0);

    const src = this.audioCtx.createBufferSource();
    src.buffer = buf;
    src.connect(this.audioCtx.destination);
    src.onended = () => this.playNext();
    src.start();
  }

  // ── Utils ────────────────────────────────────────────────────────────────
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(b64: string): ArrayBuffer {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }
}

export const jarvisRT = new JarvisRealtime();
