import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Jarvis — Assistant IA Vocal",
  description: "Assistant IA vocal personnel < 1 seconde de latence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark">
      <body className={`${inter.variable} bg-canvas text-body min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
