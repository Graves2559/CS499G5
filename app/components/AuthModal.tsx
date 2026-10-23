import type { Dispatch, SetStateAction, RefObject } from "react";
import { X } from "lucide-react";

type AuthModalProps = {
  dialogRef: RefObject<HTMLDialogElement | null>;
  authMode: "signin" | "signup";
  setAuthMode: Dispatch<SetStateAction<"signin" | "signup">>;
  authNotice: string;
  setAuthNotice: Dispatch<SetStateAction<string>>;
};

export default function AuthModal({ dialogRef, authMode, setAuthMode, authNotice, setAuthNotice }: AuthModalProps) {
  return (<dialog ref={dialogRef} className="auth-dialog" aria-labelledby="auth-title" onClick={e => { if (e.target === e.currentTarget) { const bounds = e.currentTarget.getBoundingClientRect(); if (e.clientX < bounds.left || e.clientX > bounds.right || e.clientY < bounds.top || e.clientY > bounds.bottom) dialogRef.current?.close(); } }}>
      <button className="close-dialog" aria-label="Close sign-in dialog" onClick={() => dialogRef.current?.close()}><X size={20} /></button>
      <h2 id="auth-title">{authMode === "signin" ? "Sign in" : "Create an account"}</h2>
      <form onSubmit={e => e.preventDefault()}>
        <label htmlFor="auth-username">Username or email</label><input id="auth-username" type="text" autoComplete="username" placeholder="Enter your username or email" />
        <label htmlFor="auth-password">Password</label><input id="auth-password" type="password" autoComplete={authMode === "signin" ? "current-password" : "new-password"} placeholder="Enter your password" />
        <button className="run-button auth-submit" type="button" onClick={() => setAuthNotice("Account registration and sign-in are not connected yet.")}>{authMode === "signin" ? "Sign in" : "Sign up"}</button>
      </form>
      <p className="auth-notice" role="status">{authNotice}</p>
      <p className="auth-switch">{authMode === "signin" ? "Don't have an account? " : "Already have an account? "}<button onClick={() => { setAuthMode(authMode === "signin" ? "signup" : "signin"); setAuthNotice(""); }}>{authMode === "signin" ? "Sign up" : "Sign in"}</button></p>
      <div className="auth-divider"><span>or</span></div>
      <button className="google-signin" type="button" onClick={() => setAuthNotice("Google sign-in is not connected yet.")}><span aria-hidden="true" className="google-mark">G</span>Continue with Google</button>
    </dialog>);
}
