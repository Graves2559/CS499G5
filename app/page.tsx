import { useRef, useState, type CSSProperties } from "react";
import { Plus, Settings } from "lucide-react";
import type { InputType, OutputType, FileEntry, Preferences } from "./types";
import { useFileUrl } from "./hooks/useFileUrl";
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
  const dialog = useRef<HTMLDialogElement>(null);

  const [preferences, setPreferences] = useState<Preferences>({ encryption: false, lossless: true, background: "#0b0610" });
  const [entries, setEntries] = useState<FileEntry[]>([
    { id: "input", parentId: null, name: "Input", kind: "folder", description: "Uploaded files and source text" },
    { id: "output", parentId: null, name: "Output", kind: "folder", description: "Files and text after Run" },
  ]);
  const settingsDialog = useRef<HTMLDialogElement>(null);
  const [authNotice, setAuthNotice] = useState("");

  function storeFile(parentId: string, file: File) {
    setEntries(current => current.some(entry => entry.parentId === parentId && entry.file === file) ? current : [...current, {
      id: crypto.randomUUID(), parentId, name: file.name, kind: "file", description: "", file,
    }]);
  }
  function storeText(parentId: string, value: string) {
    setEntries(current => {
      const id = `${parentId}-text`;
      return current.some(entry => entry.id === id) ? current.map(entry => entry.id === id ? { ...entry, text: value } : entry) : [...current, {
        id, parentId, name: parentId === "input" ? "input.txt" : "summary.txt", kind: "file", description: "", text: value,
      }];
    });
  }
  const activeFile = input === "PDF" ? pdfFile : imageFile;
  const canRun = input === "Texts" || !!activeFile;

  function chooseFile(candidate?: File) {
    if (!candidate) return;
    if (input === "PDF") {
      if (candidate.type !== "application/pdf" && !(candidate.type === "" && /\.pdf$/i.test(candidate.name))) {
        setError("Please choose a PDF file."); return;
      }
      if (candidate.size > 25 * 1024 * 1024) {
        setError("Please choose a PDF no larger than 25MB."); return;
      }
      setPdfFile(candidate);
    } else {
      if (!["image/png", "image/jpeg"].includes(candidate.type)) {
        setError("Please choose a PNG or JPG image."); return;
      }
      if (candidate.size > 10 * 1024 * 1024) {
        setError("Please choose an image no larger than 10MB."); return;
      }
      setImageFile(candidate);
    }
    storeFile("input", candidate);
    setError(""); setStatus("");
  }

  function run() {
    if (input === "Texts") {
      storeText("input", text); storeText("output", text);
      setSummary(text); setStatus("Text ready. Select Summary in Output to view it.");
    } else if (input === "Image" && imageFile) {
      storeFile("output", imageFile);
      setOutputImage(imageFile); setStatus("Image ready. Select Image in Output to view it.");
    } else if (input === "PDF" && pdfFile) {
      storeFile("output", pdfFile);
      setOutputPdf(pdfFile); setStatus("PDF ready. Select PDF in Output to view or download it.");
    }
    setWord("");
  }

  return <div className="app-shell" style={{ "--background": preferences.background } as CSSProperties}>
    <header className="topbar">
      <a className="brand" href="/" aria-label="ClosedAI home"><span className="brand-orb" />ClosedAI</a>
      <button className="pill login" onClick={() => { setAuthMode("signin"); setAuthNotice(""); setWord(""); dialog.current?.showModal(); }}>Login</button>
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
      entries={entries}
      setEntries={setEntries}
    />
    <AuthModal
      dialogRef={dialog}
      authMode={authMode}
      setAuthMode={setAuthMode}
      authNotice={authNotice}
      setAuthNotice={setAuthNotice}
    />
  </div>;
}
