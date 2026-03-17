/*
  ROOT PAGE — src/app/page.tsx
  ─────────────────────────────
  LESSON: This renders at the "/" route.
  We immediately redirect to /dashboard (authenticated) or /login.
  
  Using Next.js redirect() from "next/navigation" is the SERVER-side
  way to redirect. Never use window.location on the server.
*/

import { redirect } from "next/navigation";

export default function RootPage() {
  // In a real app you'd check the session cookie server-side here.
  // For now, always redirect to dashboard (demo mode).
  redirect("/dashboard");
}
