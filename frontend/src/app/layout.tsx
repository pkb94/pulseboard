/*
  ROOT LAYOUT — src/app/layout.tsx
  ─────────────────────────────────
  LESSON: In Next.js App Router, layout.tsx is the "shell" that
  wraps all child pages. It:
    1. Sets HTML metadata (title, description, viewport)
    2. Applies global CSS
    3. Provides context providers (theme, auth, state)
  
  This file runs on the SERVER by default ("use server" is implicit).
  Only add "use client" when you need browser APIs.
*/

import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

/*
  Inter is loaded via next/font — this zero-runtime font loader:
  - Downloads the font at BUILD TIME (no layout shift)
  - Self-hosts it (no Google tracking)
  - Generates a unique className to scope the font
*/
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

/*
  Metadata is a Next.js concept for SEO & social sharing.
  Defining it as a typed export (not a <Helmet>) is the App Router way.
*/
export const metadata: Metadata = {
  title: {
    default: "PulseBoard",
    template: "%s | PulseBoard",
  },
  description:
    "AI-powered real-time operations intelligence — monitor, detect anomalies, and respond instantly.",
  keywords: ["monitoring", "observability", "anomaly detection", "real-time dashboard"],
  authors: [{ name: "PulseBoard" }],
  openGraph: {
    title: "PulseBoard",
    description: "Real-time operations intelligence platform",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0f172a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    /*
      "dark" class on <html> enables our dark theme CSS variables.
      lang="en" is important for accessibility (screen readers).
    */
    <html lang="en" className={`${inter.variable} dark`} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
