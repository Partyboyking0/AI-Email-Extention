export interface JwtState {
  token: string;
  expiresAt: number;
}

export async function getJwt(): Promise<JwtState | null> {
  const result = await chrome.storage.local.get("ai-email.jwt");
  return result["ai-email.jwt"] ?? null;
}

export async function ensureJwt(): Promise<JwtState | null> {
  const jwt = await getJwt();
  if (!jwt || jwt.expiresAt < Date.now() + 60_000) return null;
  return jwt;
}

export async function getOrCreateDemoJwt(apiBaseUrl: string): Promise<JwtState> {
  const existing = await ensureJwt();
  if (existing) return existing;

  const response = await fetch(`${apiBaseUrl}/api/auth/demo-token`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Auth failed with ${response.status}`);
  }

  const body = (await response.json()) as { access_token: string; expires_in: number };
  const jwt = {
    token: body.access_token,
    expiresAt: Date.now() + body.expires_in * 1000
  };
  await chrome.storage.local.set({ "ai-email.jwt": jwt });
  return jwt;
}
