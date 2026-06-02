import type { LoggedInPlayer } from '../types';

interface Props {
  player: LoggedInPlayer | null;
  onPlay: () => void;
  onAuth: (mode: 'login' | 'register') => void;
  onLeaderboard: () => void;
  onLogout: () => void;
}

export function MainMenu({ player, onPlay, onAuth, onLeaderboard, onLogout }: Props) {
  return (
    <div className="menu-screen">
      <pre className="title-art">{`
  _____ _                         _____ _     _
 |  ___| | __ _ _ __  _ __  _   _|  ___(_)___| |__
 | |_  | |/ _\` | '_ \\| '_ \\| | | | |_  | / __| '_ \\
 |  _| | | (_| | |_) | |_) | |_| |  _| | \\__ \\ | | |
 |_|   |_|\\__,_| .__/| .__/ \\__, |_|   |_|___/_| |_|
                |_|   |_|    |___/
      `}</pre>
      <pre className="fish-art">{'  ><((((º>'}</pre>

      {player ? (
        <div className="menu-player-info">
          <span className="menu-greeting">Welcome, <strong>{player.username}</strong></span>
          <span className="menu-hs">High Score: {player.highScore}</span>
        </div>
      ) : (
        <p className="menu-hint">Log in to save your score to the leaderboard.</p>
      )}

      <div className="menu-options">
        <button className="menu-btn primary" onClick={onPlay}>
          ▶  Play Game
        </button>
        <button className="menu-btn" onClick={onLeaderboard}>
          🏆  Leaderboard
        </button>
        {player ? (
          <button className="menu-btn" onClick={onLogout}>
            Log Out
          </button>
        ) : (
          <>
            <button className="menu-btn" onClick={() => onAuth('login')}>
              Log In
            </button>
            <button className="menu-btn" onClick={() => onAuth('register')}>
              Register
            </button>
          </>
        )}
      </div>

      <p className="menu-controls">
        <strong>SPACE</strong> — flap &nbsp;|&nbsp; <strong>Q / ESC</strong> — quit to menu
        &nbsp;|&nbsp; <strong>Click</strong> — flap
      </p>
    </div>
  );
}
