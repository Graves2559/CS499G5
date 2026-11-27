import { useEffect, useState } from "react";
import type { AuthGateway } from "./ports";

// Who is signed in, and the actions to change that. The server owns the session (an HttpOnly cookie).
export function useAuth(gateway: AuthGateway) {
  const [user, setUser] = useState<string | null>(null);

  useEffect(() => {
    gateway.me().then(setUser).catch(() => {});
  }, [gateway]);

  return {
    user,
    async signIn(username: string, password: string) { setUser(await gateway.login(username, password)); },
    async signUp(username: string, email: string, password: string) { setUser(await gateway.register(username, email, password)); },
    async signOut() { await gateway.logout().catch(() => {}); setUser(null); },
  };
}
