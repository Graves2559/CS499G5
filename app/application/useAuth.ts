import { useEffect, useState } from "react";
import type { AuthGateway } from "./ports";

// Who is signed in, and the actions to change that. The server owns the session (an HttpOnly cookie).
export function useAuth(gateway: AuthGateway) {
  const [user, setUser] = useState<string | null>(null);
  const [redirectError, setRedirectError] = useState("");

  useEffect(() => {
    gateway.me().then(setUser).catch(() => {});
    // Google sign-in sends the browser back here with ?auth_error=... when it fails
    const failure = new URLSearchParams(window.location.search).get("auth_error");
    if (failure) {
      window.history.replaceState(null, "", window.location.pathname);
      setRedirectError(failure);
    }
  }, [gateway]);

  return {
    user,
    redirectError,
    async signIn(username: string, password: string) { setUser(await gateway.login(username, password)); },
    async signUp(username: string, email: string, password: string) { setUser(await gateway.register(username, email, password)); },
    async signOut() { await gateway.logout().catch(() => {}); setUser(null); },
  };
}
