import { useEffect, useState } from 'react';
import { getLeaderboard } from '../api';
import type { LeaderboardEntry } from '../types';

interface Props {
  onBack: () => void;
}

const PAGE_SIZE = 10;
const MEDALS = ['🥇', '🥈', '🥉'];

export function Leaderboard({ onBack }: Props) {
  const [players, setPlayers] = useState<LeaderboardEntry[]>([]);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getLeaderboard()
      .then((data) => {
        if (data.success) {
          setPlayers(data.players);
        } else {
          setError(data.message ?? 'Could not load leaderboard.');
        }
      })
      .catch(() => setError('Could not reach server.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = search
    ? players.filter((p) => p.username.toLowerCase().includes(search.toLowerCase()))
    : players;

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const page_ = Math.min(page, Math.max(0, totalPages - 1));
  const visible = filtered.slice(page_ * PAGE_SIZE, page_ * PAGE_SIZE + PAGE_SIZE);

  return (
    <div className="menu-screen leaderboard-screen">
      <h2 className="lb-title">🏆 Leaderboard</h2>

      <input
        className="lb-search"
        type="text"
        placeholder="Search player…"
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(0); }}
      />

      {loading && <p className="lb-status">Loading…</p>}
      {error && <p className="lb-status lb-error">{error}</p>}

      {!loading && !error && (
        <>
          <table className="lb-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Player</th>
                <th>High Score</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((p, i) => {
                const rank = page_ * PAGE_SIZE + i;
                return (
                  <tr key={p.username} className={rank < 3 ? 'lb-top' : ''}>
                    <td>{MEDALS[rank] ?? rank + 1}</td>
                    <td>{p.username}</td>
                    <td>{p.highScore}</td>
                  </tr>
                );
              })}
              {visible.length === 0 && (
                <tr>
                  <td colSpan={3} style={{ textAlign: 'center', color: '#888' }}>
                    No players found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="lb-pagination">
              <button
                className="menu-btn"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page_ === 0}
              >
                ← Prev
              </button>
              <span>
                Page {page_ + 1} / {totalPages}
              </span>
              <button
                className="menu-btn"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page_ >= totalPages - 1}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      <button className="menu-btn back-btn" onClick={onBack}>
        ← Back
      </button>
    </div>
  );
}
