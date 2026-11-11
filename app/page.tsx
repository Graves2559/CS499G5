import { useEffect, useRef, useState, type CSSProperties } from "react";
import { Plus, Settings } from "lucide-react";
import type { InputType, OutputType, Preferences } from "./types";
import { uploadProblem } from "./domain/uploads";
import { useFileUrl } from "./hooks/useFileUrl";
import { useAuth } from "./application/useAuth";
import { useFiles } from "./application/useFiles";
import { api } from "./infrastructure/api";
import InputPanel from "./components/InputPanel";
import OutputPanel from "./components/OutputPanel";
import AuthModal from "./components/AuthModal";
import SettingsModal from "./components/SettingsModal";

export default function Home() {
  const [input, setInput] = useState<InputType>("Image");
  const [outputType, setOutputType] = useState<OutputType>("Summary");
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [outputImage, setOutputImage] = useState<File | null>(null);
  const [outputPdf, setOutputPdf] = useState<File | null>(null);
  const imageUrl = useFileUrl(imageFile);
  const [error, setError] = useState("");
  const [word, setWord] = useState("");
  const [status, setStatus] = useState("");
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  const [authNotice, setAuthNotice] = useState("");
  const [preferences, setPreferences] = useState<Preferences>({ encryption: false, lossless: true, background: "#0b0610" });
  const dialog = useRef<HTMLDialogElement>(null);
  const settingsDialog = useRef<HTMLDialogElement>(null);

  // The one place where the application layer is connected to the infrastructure (the server gateway).
  const auth = useAuth(api);
  const files = useFiles(api, !!auth.user, setError);

  useEffect(() => {
    if (!auth.redirectError) return;
    setAuthMode("signin"); setAuthNotice(auth.redirectError); dialog.current?.showModal();
  }, [auth.redirectError]);

  async function signIn(username: string, password: string) { await auth.signIn(username, password); dialog.current?.close(); }
  async function signUp(username: string, email: string, password: string) { await auth.signUp(username, email, password); dialog.current?.close(); }
  async function signOut() {
    await auth.signOut();
    // Clear what the previous user had on screen
    setText(""); setSummary(""); setImageFile(null); setPdfFile(null); setOutputImage(null); setOutputPdf(null);
    setStatus(""); setError("");
  }

  const activeFile = input === "PDF" ? pdfFile : imageFile;
  const canRun = input === "Texts" || !!activeFile;

  function chooseFile(candidate?: File) {
    if (!candidate) return;
    const problem = uploadProblem(input === "PDF" ? "PDF" : "Image", candidate);
    if (problem) { setError(problem); return; }
    if (input === "PDF") setPdfFile(candidate); else setImageFile(candidate);
    files.storeFile("input", candidate);
    setError(""); setStatus("");
  }

  function run() {
    if (input === "Texts") {
      files.storeText("input", text); files.storeText("output", text);
      setSummary(text); setStatus("Text ready. Select Summary in Output to view it.");
    } else if (input === "Image" && imageFile) {
      files.storeFile("output", imageFile);
      setOutputImage(imageFile); setStatus("Image ready. Select Image in Output to view it.");
    } else if (input === "PDF" && pdfFile) {
      files.storeFile("output", pdfFile);
      setOutputPdf(pdfFile); setStatus("PDF ready. Select PDF in Output to view or download it.");
    }
    setWord("");
  }

  return <div className="app-shell" style={{ "--background": preferences.background } as CSSProperties}>
    <header className="topbar">
      <a className="brand" href="/" aria-label="ClosedAI home"><span className="brand-orb" />ClosedAI</a>
      {auth.user
        ? <div className="account"><span className="account-name">{auth.user}</span><button className="pill login" onClick={signOut}>Log out</button></div>
        : <button className="pill login" onClick={() => { setAuthMode("signin"); setAuthNotice(""); setWord(""); dialog.current?.showModal(); }}>Login</button>}
    </header>
    <div className="workspace">
      <aside className="sidebar" aria-label="Recent chats">
        <div className="sidebar-heading"><h2>Recent</h2><button className="pill"><Plus size={13} />New chat</button></div>
      </aside>
      <main className="panels">
        <InputPanel
          input={input}
          text={text}
          activeFile={activeFile}
          imageUrl={imageUrl}
          error={error}
          status={status}
          canRun={canRun}
          onTypeChange={type => { setInput(type); setError(""); setStatus(""); }}
          onTextChange={setText}
          onFileChange={chooseFile}
          onRemoveFile={() => { input === "PDF" ? setPdfFile(null) : setImageFile(null); setError(""); setStatus(""); }}
          onImageError={() => { setError("This image could not be opened. Please choose another image."); setImageFile(null); }}
          onRun={run}
        />
        <OutputPanel
          outputType={outputType}
          setOutputType={setOutputType}
          summary={summary}
          outputImage={outputImage}
          outputPdf={outputPdf}
          word={word}
          setWord={setWord}
        />
      </main>
    </div>
    <button className="settings-launcher pill" onClick={() => { setWord(""); settingsDialog.current?.showModal(); }} aria-haspopup="dialog"><Settings size={19} />Settings</button>
    <SettingsModal
      dialogRef={settingsDialog}
      preferences={preferences}
      onChange={setPreferences}
      files={files}
    />
    <AuthModal
      dialogRef={dialog}
      authMode={authMode}
      setAuthMode={setAuthMode}
      authNotice={authNotice}
      setAuthNotice={setAuthNotice}
      onSignIn={signIn}
      onSignUp={signUp}
    />
  </div>;
}
