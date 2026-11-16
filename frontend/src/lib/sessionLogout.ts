export type LogoutOutcome = "revoked" | "unconfirmed" | "local";

/** Local sign-out always completes; remote revocation must be acknowledged. */
export async function requestSessionLogout(
  token: string | null,
  refreshToken: string | null
): Promise<LogoutOutcome> {
  // No access credential means we cannot authenticate a revocation request.
  if (!token) return refreshToken ? "unconfirmed" : "local";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch("/api/v1/auth/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(refreshToken ? { refresh_token: refreshToken } : {}),
      signal: controller.signal,
      keepalive: true,
    });
    return response.ok ? "revoked" : "unconfirmed";
  } catch {
    return "unconfirmed";
  } finally {
    clearTimeout(timeout);
  }
}

export function logoutLocation(path: "/login" | "/admin/login", outcome: LogoutOutcome) {
  return outcome === "unconfirmed" ? `${path}?revocation=unconfirmed` : path;
}
