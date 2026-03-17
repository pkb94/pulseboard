/*
  src/app/(auth)/login/page.tsx — simple placeholder login page
*/
export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm p-8 rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm">
        <h1 className="text-xl font-bold text-foreground mb-1">PulseBoard</h1>
        <p className="text-sm text-muted-foreground mb-6">Sign in to your workspace</p>
        <a
          href="/dashboard"
          className="block w-full text-center py-2 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Continue to Dashboard →
        </a>
      </div>
    </div>
  );
}
