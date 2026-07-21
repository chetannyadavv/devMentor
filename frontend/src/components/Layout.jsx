import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children }) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-bg text-text font-body">
      <header className="border-b border-border px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <Link to="/" className="font-display text-xl font-bold text-accent">
            DevMentor
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link to="/" className="text-text-muted hover:text-text">
              Problems
            </Link>
            <Link to="/leaderboard" className="text-text-muted hover:text-text">
              Leaderboard
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-text-muted font-mono">
            {user?.username} {user?.is_admin && <span className="text-accent">(admin)</span>}
          </span>
          <button onClick={logout} className="text-wrong hover:underline">
            Log out
          </button>
        </div>
      </header>
      <main className="p-6 max-w-4xl mx-auto">{children}</main>
    </div>
  );
}
