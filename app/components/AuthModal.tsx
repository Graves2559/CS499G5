import { useState, type Dispatch, type SetStateAction, type RefObject } from "react";
import { X } from "lucide-react";

type AuthModalProps = {
  dialogRef: RefObject<HTMLDialogElement | null>;
  authMode: "signin" | "signup";
  setAuthMode: Dispatch<SetStateAction<"signin" | "signup">>;
  authNotice: string;
  setAuthNotice: Dispatch<SetStateAction<string>>;
  onSignIn: (username: string, password: string) => Promise<void>;
  onSignUp: (username: string, email: string, password: string) => Promise<void>;
};

export default function AuthModal({ dialogRef, authMode, setAuthMode, authNotice, setAuthNotice, onSignIn, onSignUp }: AuthModalProps) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (authMode === "signup" && password !== confirm) { setAuthNotice("The passwords do not match."); return; }
    setBusy(true); setAuthNotice("");
    try {
      if (authMode === "signup") await onSignUp(username.trim(), email.trim(), password);
      else await onSignIn(username.trim(), password);
      setPassword(""); setConfirm("");
    }
    catch (failure) { setAuthNotice(failure instanceof Error ? failure.message : "Something went wrong."); }
    finally { setBusy(false); }
  }

  return (<dialog ref={dialogRef} className="auth-dialog" aria-labelledby="auth-title" onClick={e => { if (e.target === e.currentTarget) { const bounds = e.currentTarget.getBoundingClientRect(); if (e.clientX < bounds.left || e.clientX > bounds.right || e.clientY < bounds.top || e.clientY > bounds.bottom) dialogRef.current?.close(); } }}>
      <button className="close-dialog" aria-label="Close sign-in dialog" onClick={() => dialogRef.current?.close()}><X size={20} /></button>
      <h2 id="auth-title">{authMode === "signin" ? "Sign in" : "Create an account"}</h2>
      <form onSubmit={submit}>
        <label htmlFor="auth-username">{authMode === "signin" ? "Username or email" : "Username"}</label><input id="auth-username" type="text" autoComplete="username" placeholder={authMode === "signin" ? "Enter your username or email" : "Choose a username"} value={username} onChange={e => setUsername(e.target.value)} required />
        {authMode === "signup" && <><label htmlFor="auth-email">Email</label><input id="auth-email" type="email" autoComplete="email" placeholder="Enter your email" value={email} onChange={e => setEmail(e.target.value)} required /></>}
        <label htmlFor="auth-password">Password</label><input id="auth-password" type="password" autoComplete={authMode === "signin" ? "current-password" : "new-password"} placeholder="Enter your password" value={password} onChange={e => setPassword(e.target.value)} required />
        {authMode === "signup" && <><label htmlFor="auth-confirm">Confirm password</label><input id="auth-confirm" type="password" autoComplete="new-password" placeholder="Enter your password again" value={confirm} onChange={e => setConfirm(e.target.value)} aria-invalid={confirm !== "" && confirm !== password} required /></>}
        {authMode === "signup" && <small className="muted-copy">At least 8 characters with an uppercase letter, a lowercase letter, a number and a symbol.</small>}
        <button className="run-button auth-submit" type="submit" disabled={busy}>{authMode === "signin" ? "Sign in" : "Sign up"}</button>
      </form>
      <p className="auth-notice" role="status">{authNotice}</p>
      <p className="auth-switch">{authMode === "signin" ? "Don't have an account? " : "Already have an account? "}<button onClick={() => { setAuthMode(authMode === "signin" ? "signup" : "signin"); setAuthNotice(""); setConfirm(""); }}>{authMode === "signin" ? "Sign up" : "Sign in"}</button></p>
      <div className="auth-divider"><span>or</span></div>
      <button className="google-signin" type="button" onClick={() => { window.location.href = "/api/auth/google/start"; }}><span aria-hidden="true" className="google-mark">G</span>Continue with Google</button>
    </dialog>);
}
