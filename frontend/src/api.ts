export async function register(
  name: string,
  pwd: string,
): Promise<{ code: number; message?: string }> {
  const res = await fetch(
    `/auth/register?name=${encodeURIComponent(name)}&pwd=${encodeURIComponent(pwd)}`,
  );
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
  return res.json();
}

export async function getLeaderboard(): Promise<{
  success: boolean;
  message?: string;
  players: { username: string; highScore: number }[];
}> {
  const res = await fetch('/leaderboard');
  return res.json();
}
