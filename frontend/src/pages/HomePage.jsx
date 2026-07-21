import { useAuth } from "../context/AuthContext";

export default function HomePage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-bg text-text font-body">
      <header className="border-b border-border px-6 py-4 flex justify-between items-center">
        <h1 className="font-display text-xl font-bold text-accent">DevMentor</h1>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-text-muted font-mono">
            {user?.username} {user?.is_admin && <span className="text-accent">(admin)</span>}
          </span>
          <button onClick={logout} className="text-wrong hover:underline">
            Log out
          </button>
        </div>
      </header>
      <main className="p-6">
        <p className="text-text-muted font-mono text-sm">
          Logged in. Problem list goes here next.
        </p>
      </main>
    </div>
  );
}
