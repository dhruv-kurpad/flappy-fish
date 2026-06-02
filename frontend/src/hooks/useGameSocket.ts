import { useCallback, useEffect, useRef, useState } from 'react';
import type { GameFrame, GameOverMsg } from '../types';

interface UseGameSocketResult {
  frame: GameFrame | null;
  gameOver: GameOverMsg | null;
  connected: boolean;
  sendInput: (msg: { type: string }) => void;
}

export function useGameSocket(playerName: string, active: boolean): UseGameSocketResult {
  const wsRef = useRef<WebSocket | null>(null);
  const [frame, setFrame] = useState<GameFrame | null>(null);
  const [gameOver, setGameOver] = useState<GameOverMsg | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!active) return;

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws/game?player_name=${encodeURIComponent(playerName)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data as string);
      if (msg.type === 'frame') {
        setFrame(msg as GameFrame);
      } else if (msg.type === 'game_over') {
        setGameOver(msg as GameOverMsg);
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
      setConnected(false);
    };
  }, [active, playerName]);

  const sendInput = useCallback((msg: { type: string }) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  return { frame, gameOver, connected, sendInput };
}
