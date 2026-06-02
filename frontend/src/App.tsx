import { useCallback, useEffect, useState } from 'react';
import { AuthScreen } from './components/AuthScreen';
import { GameCanvas } from './components/GameCanvas';
import { GameOver } from './components/GameOver';
import { Leaderboard } from './components/Leaderboard';
import { MainMenu } from './components/MainMenu';
import { useGameSocket } from './hooks/useGameSocket';
import type { LoggedInPlayer } from './types';
import './App.css';

type Screen = 'menu' | 'auth' | 'leaderboard' | 'game' | 'gameover';

function Game({
  playerName,
  onGameOver,
  onQuit,
}: {
  playerName: string;
  onGameOver: (score: number, highScore: number) => void;
  onQuit: () => void;
}) {
  const { frame, gameOver, connected, sendInput } = useGameSocket(playerName, true);

  useEffect(() => {
    if (gameOver) {
      onGameOver(gameOver.score, gameOver.high_score);
    }
  }, [gameOver, onGameOver]);

  const handleFlap = useCallback(() => sendInput({ type: 'flap' }), [sendInput]);
  const handleQuit = useCallback(() => {
    sendInput({ type: 'quit' });
    onQuit();
  }, [sendInput, onQuit]);

  if (!connected && !frame) {
    return (
      <div className="menu-screen">
        <p className="connecting-msg">Connecting to game server…</p>
        <p className="connecting-sub">
          Make sure the Python server is running:<br />
          <code>cd src &amp;&amp; uvicorn game_server:app --port 8765</code>
        </p>
        <button className="menu-btn back-btn" onClick={onQuit}>← Back</button>
      </div>
    );
  }

  return (
    <div className="game-wrapper">
      <GameCanvas frame={frame} onFlap={handleFlap} onQuit={handleQuit} />
    </div>
  );
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('menu');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [player, setPlayer] = useState<LoggedInPlayer | null>(null);
  const [gameKey, setGameKey] = useState(0);
  const [lastResult, setLastResult] = useState<{ score: number; highScore: number } | null>(null);

  const handleGameOver = useCallback(
    (score: number, highScore: number) => {
      setLastResult({ score, highScore });
      if (player) {
        setPlayer((p) => (p ? { ...p, highScore: Math.max(p.highScore, highScore) } : p));
      }
      setScreen('gameover');
    },
    [player],
  );

  return (
    <div className="app">
      {screen === 'menu' && (
        <MainMenu
          player={player}
          onPlay={() => {
            setGameKey((k) => k + 1);
            setScreen('game');
          }}
          onAuth={(mode) => {
            setAuthMode(mode);
            setScreen('auth');
          }}
          onLeaderboard={() => setScreen('leaderboard')}
          onLogout={() => setPlayer(null)}
        />
      )}

      {screen === 'auth' && (
        <AuthScreen
          initialMode={authMode}
          onSuccess={(p) => {
            setPlayer(p);
            setScreen('menu');
          }}
          onBack={() => setScreen('menu')}
        />
      )}

      {screen === 'leaderboard' && <Leaderboard onBack={() => setScreen('menu')} />}

      {screen === 'game' && (
        <Game
          key={gameKey}
          playerName={player?.username ?? ''}
          onGameOver={handleGameOver}
          onQuit={() => setScreen('menu')}
        />
      )}

      {screen === 'gameover' && lastResult && (
        <GameOver
          score={lastResult.score}
          highScore={lastResult.highScore}
          onPlayAgain={() => {
            setGameKey((k) => k + 1);
            setScreen('game');
          }}
          onMenu={() => setScreen('menu')}
        />
      )}
    </div>
  );
}
