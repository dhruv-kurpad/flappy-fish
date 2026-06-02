import { useEffect, useRef } from 'react';
import type { GameFrame } from '../types';

const CELL_W = 9;
const CELL_H = 18;
const BG = '#001133';

interface Props {
  frame: GameFrame | null;
  onFlap: () => void;
  onQuit: () => void;
}

export function GameCanvas({ frame, onFlap, onQuit }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault();
        onFlap();
      } else if (e.code === 'Escape' || e.key === 'q' || e.key === 'Q') {
        onQuit();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onFlap, onQuit]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !frame) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const buf = frame.buffer;
    const rows = buf.length;
    const cols = buf[0]?.length ?? 0;

    if (canvas.width !== cols * CELL_W) canvas.width = cols * CELL_W;
    if (canvas.height !== rows * CELL_H) canvas.height = rows * CELL_H;

    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = `${CELL_H - 2}px "Courier New", monospace`;
    ctx.textBaseline = 'top';

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = buf[r][c];
        if (cell.char !== ' ') {
          ctx.fillStyle = cell.color;
          ctx.fillText(cell.char, c * CELL_W, r * CELL_H);
        }
      }
    }

    if (frame.state === 'waiting') {
      const text = ' PRESS SPACE BAR TO BEGIN ';
      const tw = text.length * CELL_W;
      const tx = (canvas.width - tw) / 2;
      const ty = canvas.height / 2 - CELL_H;
      ctx.fillStyle = 'rgba(0,0,51,0.75)';
      ctx.fillRect(tx - 6, ty - 4, tw + 12, CELL_H + 8);
      ctx.fillStyle = '#00FFFF';
      ctx.fillText(text, tx, ty);
    }
  }, [frame]);

  return (
    <canvas
      ref={canvasRef}
      onClick={onFlap}
      style={{ display: 'block', cursor: 'pointer', imageRendering: 'pixelated' }}
    />
  );
}
