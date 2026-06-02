export interface FrameCell {
  char: string;
  color: string;
}

export type FrameBuffer = FrameCell[][];

export interface GameFrame {
  type: 'frame';
  state: 'waiting' | 'playing' | 'dead';
  buffer: FrameBuffer;
  score: number;
  high_score: number;
}

export interface GameOverMsg {
  type: 'game_over';
  score: number;
  high_score: number;
}

export interface LoggedInPlayer {
  username: string;
  highScore: number;
}

export interface LeaderboardEntry {
  username: string;
  highScore: number;
}
