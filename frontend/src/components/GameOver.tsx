interface Props {
  score: number;
  highScore: number;
  onPlayAgain: () => void;
  onMenu: () => void;
}

export function GameOver({ score, highScore, onPlayAgain, onMenu }: Props) {
  const isNewRecord = score >= highScore && score > 0;

  return (
    <div className="menu-screen gameover-screen">
      <pre className="fish-art dead-fish">{'><(((*>'}</pre>
      <h2 className="gameover-title">GAME OVER</h2>

      <div className="gameover-scores">
        <div className="gameover-score-row">
          <span>Score</span>
          <span className="gameover-score-val">{score}</span>
        </div>
        <div className="gameover-score-row">
          <span>High Score</span>
          <span className={`gameover-score-val${isNewRecord ? ' new-record' : ''}`}>
            {highScore}
            {isNewRecord && ' (new record)'}
          </span>
        </div>
      </div>

      <div className="menu-options">
        <button className="menu-btn primary" onClick={onPlayAgain}>
          Play Again
        </button>
        <button className="menu-btn" onClick={onMenu}>
          Menu
        </button>
      </div>
    </div>
  );
}
