const RATE_LIMIT_MESSAGE = 'Too many requests. Please wait a moment and try again.';

export async function register(
  name: string,
  pwd: string,
): Promise<{ code: number; message?: string }> {
  const res = await fetch(
    `/auth/register?name=${encodeURIComponent(name)}&pwd=${encodeURIComponent(pwd)}`,
  );
  if (res.status === 429) return { code: 429, message: RATE_LIMIT_MESSAGE };
  return res.json();
}

export async function login(
  name: string,
  pwd: string,
): Promise<{
  code: number;
  message?: string;
  username?: string;
  playerId?: number;
  highScore?: number;
}> {
  const res = await fetch(
    `/auth/login?name=${encodeURIComponent(name)}&pwd=${encodeURIComponent(pwd)}`,
  );
  if (res.status === 429) return { code: 429, message: RATE_LIMIT_MESSAGE };
  return res.json();
}

export async function getLeaderboard(): Promise<{
  success: boolean;
  message?: string;
  players: { username: string; highScore: number }[];
}> {
  const res = await fetch('/leaderboard');
  if (res.status === 429) {
    return { success: false, message: RATE_LIMIT_MESSAGE, players: [] };
  }
  return res.json();
}
