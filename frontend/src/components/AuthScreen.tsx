import { useState, type FormEvent } from 'react';
import * as api from '../api';
import type { LoggedInPlayer } from '../types';

interface Props {
  initialMode: 'login' | 'register';
  onSuccess: (player: LoggedInPlayer) => void;
  onBack: () => void;
}

const DB_ASLEEP_MSG = 'Databass is asleep, float around while the guppys wake him up';

const REGISTER_MSGS: Record<number, string> = {
  0: 'Registered successfully!',
  '-1': 'Username already taken.',
  '-2': 'Username cannot be empty.',
  '-3': 'Password cannot be empty.',
  '-99': DB_ASLEEP_MSG,
} as unknown as Record<number, string>;

const LOGIN_MSGS: Record<number, string> = {
  '-1': 'Wrong username or password.',
  '-2': 'Username cannot be empty.',
  '-99': DB_ASLEEP_MSG,
} as unknown as Record<number, string>;

export function AuthScreen({ initialMode, onSuccess, onBack }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'register') {
        const res = await api.register(username, password);
        if (res.code !== 0) {
          setError(res.message ?? REGISTER_MSGS[res.code] ?? `Error code ${res.code}`);
          return;
        }
        // Auto-login after register
        const loginRes = await api.login(username, password);
        if (loginRes.code !== 0) {
          setError('Registered but login failed — please log in manually.');
          setMode('login');
          return;
        }
        onSuccess({ username: loginRes.username!, highScore: loginRes.highScore ?? 0 });
      } else {
        const res = await api.login(username, password);
        if (res.code !== 0) {
          setError(res.message ?? LOGIN_MSGS[res.code] ?? `Error code ${res.code}`);
          return;
        }
        onSuccess({ username: res.username!, highScore: res.highScore ?? 0 });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="menu-screen">
      <h2 className="auth-title">{mode === 'login' ? 'Log In' : 'Register'}</h2>

      <div className="auth-tabs">
        <button
          className={`auth-tab${mode === 'login' ? ' active' : ''}`}
          onClick={() => { setMode('login'); setError(''); }}
        >
          Log In
        </button>
        <button
          className={`auth-tab${mode === 'register' ? ' active' : ''}`}
          onClick={() => { setMode('register'); setError(''); }}
        >
          Register
        </button>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Username
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="auth-error">{error}</p>}
        <button type="submit" className="menu-btn primary" disabled={loading}>
          {loading ? 'Loading…' : mode === 'login' ? 'Log In' : 'Register'}
        </button>
      </form>

      <button className="menu-btn back-btn" onClick={onBack}>
        Back
      </button>
    </div>
  );
}
