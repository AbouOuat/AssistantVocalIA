"use client";

import { useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Message, CRData } from "@/types";

interface ChatProps {
  messages: Message[];
}

function generatePDF(cr: CRData) {
  // Import dynamique pour éviter le SSR
  import("jspdf").then(({ jsPDF }) => {
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const pageW = doc.internal.pageSize.getWidth();
    const pageH = doc.internal.pageSize.getHeight();
    const margin = 20;
    const maxW = pageW - margin * 2;
    let y = 25;

    const checkPage = (needed = 10) => {
      if (y + needed > pageH - 15) {
        doc.addPage();
        y = 20;
      }
    };

    // ── En-tête ────────────────────────────────────────────────────────────
    doc.setFillColor(15, 23, 42);
    doc.rect(0, 0, pageW, 18, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(249, 250, 251);
    doc.text("JARVIS — COMPTE-RENDU DE RÉUNION", margin, 12);
    doc.setTextColor(0, 212, 255);
    doc.text(new Date().toLocaleDateString("fr-FR"), pageW - margin, 12, { align: "right" });

    y = 30;

    // ── Titre ───────────────────────────────────────────────────────────────
    doc.setFont("helvetica", "bold");
    doc.setFontSize(17);
    doc.setTextColor(30, 30, 80);
    const titleLines = doc.splitTextToSize(cr.titre, maxW);
    doc.text(titleLines, margin, y);
    y += titleLines.length * 8 + 2;

    // Ligne de séparation indigo
    doc.setDrawColor(79, 70, 229);
    doc.setLineWidth(0.6);
    doc.line(margin, y, pageW - margin, y);
    y += 7;

    // ── Métadonnées ─────────────────────────────────────────────────────────
    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    doc.setTextColor(60, 60, 60);
    doc.text(`Date : ${cr.date}`, margin, y);
    y += 7;

    if (cr.participants.length > 0) {
      const partText = `Participants : ${cr.participants.join(", ")}`;
      const partLines = doc.splitTextToSize(partText, maxW);
      doc.text(partLines, margin, y);
      y += partLines.length * 6 + 5;
    } else {
      y += 3;
    }

    // ── Section helper ──────────────────────────────────────────────────────
    const addSection = (icon: string, title: string, items: string[]) => {
      checkPage(16);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.setTextColor(79, 70, 229);
      doc.text(`${icon}  ${title}`, margin, y);
      y += 7;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(10.5);
      doc.setTextColor(40, 40, 40);

      if (items.length === 0) {
        doc.setTextColor(130, 130, 130);
        doc.text("  • Aucun élément", margin + 2, y);
        y += 6;
      } else {
        for (const item of items) {
          const lines = doc.splitTextToSize(`• ${item}`, maxW - 6);
          checkPage(lines.length * 5.5 + 3);
          doc.text(lines, margin + 4, y);
          y += lines.length * 5.5 + 2;
        }
      }
      y += 6;
    };

    addSection("📋", "Points discutés", cr.points_discutes);
    addSection("✅", "Décisions prises", cr.decisions);
    addSection("🎯", "Actions à suivre", cr.actions);

    // ── Pied de page ────────────────────────────────────────────────────────
    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setDrawColor(220, 220, 220);
      doc.setLineWidth(0.3);
      doc.line(margin, pageH - 12, pageW - margin, pageH - 12);
      doc.setFont("helvetica", "italic");
      doc.setFontSize(8);
      doc.setTextColor(160, 160, 160);
      doc.text("Généré par Jarvis IA", margin, pageH - 7);
      doc.text(`Page ${i} / ${totalPages}`, pageW - margin, pageH - 7, { align: "right" });
    }

    const filename = `CR_${cr.titre.replace(/[^a-z0-9àâéèêëîïôùûüç]/gi, "_").slice(0, 40)}.pdf`;
    doc.save(filename);
  });
}

export function Chat({ messages }: ChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleDownload = useCallback((crData: CRData) => {
    generatePDF(crData);
  }, []);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted text-sm font-mono">
          Parle ou tape quelque chose pour démarrer…
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
      <AnimatePresence initial={false}>
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            data-testid={`msg-${msg.role}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`rounded-lg px-4 py-3 text-[15px] leading-[1.6] whitespace-pre-wrap ${
                msg.role === "user"
                  ? "max-w-[75%] bg-primary text-on-primary"
                  : "max-w-[85%] bg-surface-card text-body border border-hairline"
              }`}
            >
              {msg.content}
              {msg.isStreaming && (
                <motion.span
                  className="inline-block w-[2px] h-[15px] bg-muted ml-1 align-middle"
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
              )}
            </div>

            {/* Bouton téléchargement PDF — uniquement sur les messages avec compte-rendu */}
            {msg.crData && !msg.isStreaming && (
              <motion.button
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                onClick={() => handleDownload(msg.crData!)}
                className="mt-2 flex items-center gap-2 px-3 py-1.5 rounded-md
                           bg-surface-elevated border border-primary/40 text-primary
                           text-[12px] font-medium hover:bg-primary/10
                           transition-colors duration-150 cursor-pointer"
                aria-label="Télécharger le compte-rendu en PDF"
              >
                <span aria-hidden="true">📥</span>
                Télécharger le PDF
              </motion.button>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
}
