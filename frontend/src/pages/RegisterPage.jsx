import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(username, email, password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-bg text-text flex items-center justify-center font-body">
      <form
        onSubmit={handleSubmit}
        className="bg-surface border border-border rounded-lg p-8 max-w-sm w-full"
      >
        <h1 className="font-display text-2xl font-bold mb-6 text-accent">Register</h1>

        <label className="block text-sm text-text-muted mb-1">Username</label>
        <input
          className="w-full bg-bg border border-border rounded px-3 py-2 mb-4 font-mono text-sm outline-none focus:border-accent"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
        />

        <label className="block text-sm text-text-muted mb-1">Email</label>
        <input
          type="email"
          className="w-full bg-bg border border-border rounded px-3 py-2 mb-4 font-mono text-sm outline-none focus:border-accent"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <label className="block text-sm text-text-muted mb-1">Password</label>
        <input
          type="password"
          className="w-full bg-bg border border-border rounded px-3 py-2 mb-4 font-mono text-sm outline-none focus:border-accent"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="text-wrong text-sm font-mono mb-4">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-accent text-bg font-medium rounded px-3 py-2 disabled:opacity-50"
        >
          {submitting ? "Creating account..." : "Register"}
        </button>

        <p className="text-text-muted text-sm mt-4 text-center">
          Already have an account?{" "}
          <Link to="/login" className="text-accent">
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}
