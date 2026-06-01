"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { VoiceOrb } from "@/components/VoiceOrb";
import { Waveform } from "@/components/Waveform";
import { LiveTranscript } from "@/components/LiveTranscript";
import { Chat } from "@/components/Chat";
import { QuickActions } from "@/components/QuickActions";
import { jarvisWS, BACKEND_HTTP_URL } from "@/lib/websocket";
import { jarvisRT } from "@/lib/realtime";
import type { RTEvent } from "@/lib/realtime";
import type { Message, OrbState } from "@/types";

export default function Home() {
  const [orbState, setOrbState] = useState<OrbState>("idle");
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [inputText, setInputText] = useState("");
  const [realtimeMode, setRealtimeMode] = useState(false);
  const [progressMessage, setProgressMessage] = useState<string | null>(null);
  const streamingIdRef = useRef<string | null>(null);
  const rtAssistantIdRef = useRef<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // ── WebSocket ─────────────────────────────────────────────────────────────
  useEffect(() => {
    jarvisWS.ensureConnected();

    const unsub = jarvisWS.on((msg) => {
      if (msg.type === "response" && msg.content === "__connected__") {
        setConnected(true);
        return;
      }
      if (msg.type === "response" && msg.content === "__disconnected__") {
        setConnected(false);
        toast.warning("Connexion perdue — reconnexion en cours...");
        return;
      }

      // Streaming token par token
      if (msg.type === "stream_chunk" && msg.content) {
        setMessages((prev) => {
          const sid = streamingIdRef.current;
          if (!sid) return prev;
          return prev.map((m) =>
            m.id === sid ? { ...m, content: m.content + msg.content } : m
          );
        });
        return;
      }

      // Message de progression pendant un appel n8n long
      if (msg.type === "progress" && msg.message) {
        setProgressMessage(msg.message);
        setOrbState("speaking");
        return;
      }

      // Erreur backend → toast + reset état
      if (msg.type === "error" && msg.message) {
        toast.error(msg.message);
        setProgressMessage(null);
        setOrbState("idle");
        return;
      }

      // Réponse complète texte
      if (msg.type === "response" && msg.content) {
        // Lire + clear le ref EN DEHORS de setMessages — React StrictMode
        // double-invoque les updaters, ce qui créerait une 2e bulle si on
        // mutait le ref à l'intérieur.
        const sid = streamingIdRef.current;
        streamingIdRef.current = null;
        setMessages((prev) => {
          if (sid) {
            return prev.map((m) =>
              m.id === sid ? { ...m, content: msg.content!, isStreaming: false } : m
            );
          }
          return [
            ...prev,
            { id: Date.now().toString(), role: "assistant", content: msg.content!, timestamp: new Date() },
          ];
        });
        // voice_origin=true : la réponse vient d'une commande vocale,
        // l'audio est déjà géré par voice_response ou tts — ne pas toucher l'orb
        setProgressMessage(null);
        if (!msg.voice_origin) setOrbState("idle");
        return;
      }

      // Audio TTS synthétisé après une commande n8n (texte ou voix)
      if (msg.type === "tts" && msg.audio) {
        const audio = new Audio(`data:audio/mp3;base64,${msg.audio}`);
        setOrbState("speaking");
        audio.play().catch(() => { /* autoplay bloqué → silencieux */ });
        audio.onended = () => setOrbState("idle");
        return;
      }

      // Réponse vocale
      if (msg.type === "voice_response") {
        if (msg.transcript) setLiveTranscript(msg.transcript);
        if (msg.audio) {
          const audio = new Audio(`data:audio/mp3;base64,${msg.audio}`);
          setOrbState("speaking");
          audio.play();
          audio.onended = () => {
            setOrbState("idle");
            setLiveTranscript("");
          };
        }
        if (msg.transcript) {
          setMessages((prev) => [
            ...prev,
            { id: Date.now().toString(), role: "user", content: msg.transcript!, timestamp: new Date() },
          ]);
        }
      }
    });

    return () => {
      unsub();
      jarvisWS.disconnect();
    };
  }, []);

  // Realtime API — activé si le backend confirme l'accès
  useEffect(() => {
    fetch(`${BACKEND_HTTP_URL}/api/config`)
      .then((r) => r.json())
      .then((data) => {
        if (!data.realtime_mode) return;
        setRealtimeMode(true);
        jarvisRT.connect();

        const unsub = jarvisRT.on((event: RTEvent) => {
          switch (event.type) {
            case "connected":
              setConnected(true);
              break;

            case "rt_user_transcript":
              // Transcription de ce que l'utilisateur a dit
              if (event.text) {
                setLiveTranscript(event.text);
                setMessages((prev) => [
                  ...prev,
                  { id: Date.now().toString(), role: "user", content: event.text!, timestamp: new Date() },
                ]);
              }
              break;

            case "rt_transcript_delta":
              // Transcription de ce que Jarvis dit (stream)
              if (event.text) {
                if (!rtAssistantIdRef.current) {
                  const aid = `rt-${Date.now()}`;
                  rtAssistantIdRef.current = aid;
                  setMessages((prev) => [
                    ...prev,
                    { id: aid, role: "assistant", content: event.text!, timestamp: new Date(), isStreaming: true },
                  ]);
                } else {
                  const aid = rtAssistantIdRef.current;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === aid ? { ...m, content: m.content + event.text! } : m
                    )
                  );
                }
              }
              break;

            case "rt_audio_delta":
              // Audio joué par jarvisRT en interne — on met juste l'orb en speaking
              setOrbState("speaking");
              break;

            case "rt_done":
              // Réponse terminée — finaliser le message + rester en écoute
              setOrbState("listening");
              setLiveTranscript("");
              if (rtAssistantIdRef.current) {
                const aid = rtAssistantIdRef.current;
                rtAssistantIdRef.current = null;
                setMessages((prev) =>
                  prev.map((m) => (m.id === aid ? { ...m, isStreaming: false } : m))
                );
              }
              break;

            case "rt_error":
              console.error("[RT]", event.message);
              setOrbState("idle");
              break;

            case "disconnected":
              setRealtimeMode(false);
              setConnected(false);
              break;
          }
        });

        return () => {
          unsub();
          jarvisRT.disconnect();
        };
      })
      .catch(() => { /* RT non disponible — fallback Whisper */ });
  }, []);

  // ── Envoi texte ───────────────────────────────────────────────────────────
  const sendText = useCallback(
    (text: string) => {
      if (!text.trim() || !connected) return;
      const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);

      const streamId = (Date.now() + 1).toString();
      streamingIdRef.current = streamId;
      setMessages((prev) => [
        ...prev,
        { id: streamId, role: "assistant", content: "", timestamp: new Date(), isStreaming: true },
      ]);

      setOrbState("speaking");
      jarvisWS.send({ type: "chat", content: text });
      setInputText("");
    },
    [connected]
  );

  // ── Capture voix ─────────────────────────────────────────────────────────
  const toggleListening = useCallback(async () => {
    if (orbState === "listening") {
      if (realtimeMode) {
        jarvisRT.stopCapture();
        setOrbState("idle");
      } else {
        mediaRecorderRef.current?.stop();
        setOrbState("idle");
      }
      return;
    }

    // Mode Realtime — streaming audio temps réel vers OpenAI
    if (realtimeMode) {
      try {
        await jarvisRT.startCapture();
        setOrbState("listening");
      } catch {
        toast.error("Micro inaccessible — vérifie les permissions du navigateur.");
        setOrbState("idle");
      }
      return;
    }

    // Mode Whisper fallback — enregistrement → transcription
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        stream.getTracks().forEach((t) => t.stop());
        const reader = new FileReader();
        reader.onloadend = () => {
          const b64 = (reader.result as string).split(",")[1];
          jarvisWS.send({ type: "voice_input", audio: b64 });
          setOrbState("speaking");
        };
        reader.readAsDataURL(blob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setOrbState("listening");
    } catch {
      toast.error("Micro inaccessible — vérifie les permissions du navigateur.");
      setOrbState("idle");
    }
  }, [orbState, realtimeMode]);

  return (
    <main className="flex flex-col items-center h-screen overflow-hidden bg-canvas">
      {/* Header */}
      <header className="w-full max-w-2xl flex items-center justify-between px-4 py-4">
        <h1 className="text-ink font-semibold text-[18px]">Jarvis</h1>
        <span
          data-testid="connection-status"
          className={`text-[12px] font-mono ${connected ? "text-[#34D399]" : "text-muted"}`}
        >
          {connected ? "● Connected" : "○ Disconnected"}
        </span>
      </header>

      {/* Zone orb + waveform */}
      <section className="flex flex-col items-center gap-4 py-8">
        <VoiceOrb state={orbState} onClick={toggleListening} />
        <Waveform active={orbState === "speaking"} />
        <AnimatePresence>
          {progressMessage && (
            <motion.p
              key="progress"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: [0.6, 1, 0.6] }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
              className="text-[13px] font-mono text-voice-active text-center px-4"
            >
              {progressMessage}
            </motion.p>
          )}
        </AnimatePresence>
        <LiveTranscript text={liveTranscript} visible={orbState !== "idle" && !progressMessage} />
      </section>

      {/* Chat */}
      <section
        className="w-full max-w-2xl flex-1 flex flex-col"
        style={{ height: "calc(100vh - 380px)", minHeight: "200px" }}
      >
        <Chat messages={messages} />
      </section>

      {/* Quick Actions + Input */}
      <footer className="w-full max-w-2xl px-4 pb-6 flex flex-col gap-3">
        <QuickActions onAction={sendText} disabled={!connected} />

        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendText(inputText);
          }}
          className="flex gap-2"
        >
          <input
            data-testid="text-input"
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ou tape un message…"
            disabled={!connected}
            className="flex-1 bg-surface-input text-ink rounded-lg px-4 py-2.5 text-[16px]
                       border border-hairline placeholder:text-muted-soft
                       focus:outline-none focus:border-primary
                       disabled:opacity-40"
          />
          <motion.button
            type="submit"
            disabled={!connected || !inputText.trim()}
            className="px-5 py-2.5 bg-primary text-on-primary rounded-lg text-[14px] font-medium
                       hover:bg-primary-active disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
            whileTap={{ scale: 0.97 }}
          >
            Envoyer
          </motion.button>
        </form>
      </footer>
    </main>
  );
}
