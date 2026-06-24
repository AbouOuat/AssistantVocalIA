"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BACKEND_HTTP_URL } from "@/lib/websocket";

export function WorkflowVersion() {
  const [version, setVersion] = useState<"v1" | "v2">("v1");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${BACKEND_HTTP_URL}/api/settings`)
      .then((r) => r.json())
      .then((d) => { if (d.workflow_version) setVersion(d.workflow_version); })
      .catch(() => {});
  }, []);

  const toggle = async () => {
    const next = version === "v1" ? "v2" : "v1";
    setLoading(true);
    try {
      await fetch(`${BACKEND_HTTP_URL}/api/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflow_version: next }),
      });
      setVersion(next);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.button
      onClick={toggle}
      disabled={loading}
      whileTap={{ scale: 0.95 }}
      aria-label={`Version workflows : ${version}. Cliquer pour basculer.`}
      className="flex items-center gap-1 px-2 py-1 rounded font-mono text-[11px] border transition-colors duration-200
                 border-hairline disabled:opacity-50 cursor-pointer"
      style={{
        background: version === "v2" ? "rgba(79,70,229,0.15)" : "rgba(255,255,255,0.04)",
        color: version === "v2" ? "#4F46E5" : "#6B7280",
        borderColor: version === "v2" ? "#4F46E5" : "rgba(255,255,255,0.08)",
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: version === "v2" ? "#4F46E5" : "#6B7280",
        }}
      />
      {version === "v2" ? "V2 LangChain" : "V1 Classic"}
    </motion.button>
  );
}
