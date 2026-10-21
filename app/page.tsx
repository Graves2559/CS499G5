import { useEffect, useRef, useState, type CSSProperties, type Dispatch, type SetStateAction } from "react";
import { Plus, Upload, ChevronDown, X, FileText, Download, Settings, Folder, FolderPlus, MoreHorizontal, Pencil, ChevronRight, ArrowLeft, BookOpen } from "lucide-react";

type InputType = "Image" | "Texts" | "PDF";
type OutputType = "Summary" | "Image" | "PDF";

function useFileUrl(file: File | null) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    if (!file) { setUrl(""); return; }
    const nextUrl = URL.createObjectURL(file);
    setUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [file]);
  return file ? url : "";
}

type FileEntry = {
  id: string;
  parentId: string | null;
  name: string;
  kind: "folder" | "file";
  description: string;
  file?: File;
  text?: string;
};

type Preferences = {
  encryption: boolean;
  lossless: boolean;
  background: string;
};

function saveDownload(content: Blob, name: string) {
  const url = URL.createObjectURL(new Blob([content], { type: "application/octet-stream" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

function SettingsContent({ preferences, onChange, entries, setEntries }: {
  preferences: Preferences;
  onChange: Dispatch<SetStateAction<Preferences>>;
  entries: FileEntry[];
  setEntries: Dispatch<SetStateAction<FileEntry[]>>;
}) {
  const [section, setSection] = useState("General");
  const [billingNotice, setBillingNotice] = useState("");
  const sections = ["General", "Files", "Appearance", "Performance", "Payment"];
  return <div className="settings-layout">
    <nav className="settings-nav" aria-label="Settings sections">

      {sections.map(name => <button key={name} type="button" aria-current={section === name ? "page" : undefined} onClick={() => setSection(name)}>{name}</button>)}
    </nav>
    <section className={`settings-content${section === "Files" ? " files-settings-content" : ""}`} aria-label={`${section} settings`}>
      {section === "Files" && <FilesView entries={entries} setEntries={setEntries} />}
      {section === "General" && <>
        <h3>General</h3>
        <p className="muted-copy">Encryption and conversion are not connected yet.</p>
        <div className="preference-row"><div><label htmlFor="image-video-encryption">Image &amp; video encryption</label></div><input id="image-video-encryption" className="preference-checkbox" type="checkbox" checked={preferences.encryption} onChange={e => onChange(current => ({ ...current, encryption: e.target.checked }))} /></div>
        <div className="preference-row"><div><label htmlFor="lossless-conversion">Lossless format conversion</label></div><input id="lossless-conversion" className="preference-checkbox" type="checkbox" checked={preferences.lossless} onChange={e => onChange(current => ({ ...current, lossless: e.target.checked }))} /></div>
      </>}
      {section === "Appearance" && <>
        <h3>Background color</h3>
        <div className="color-options">{[{ name: "Midnight", color: "#0b0610" }, { name: "Charcoal", color: "#15171c" }, { name: "Ocean", color: "#071d2a" }, { name: "Plum", color: "#29142c" }].map(({ name, color }) => <button key={name} aria-pressed={preferences.background === color} onClick={() => onChange(current => ({ ...current, background: color }))}><span style={{ background: color }} />{name}</button>)}</div>
        <label className="custom-color">Custom color <input type="color" aria-label="Custom background color" value={preferences.background} onChange={e => onChange(current => ({ ...current, background: e.target.value }))} /><span>{preferences.background.toUpperCase()}</span></label>
        <p className="muted-copy section-space">Changes reset on refresh.</p>
      </>}
      {section === "Performance" && <>
        <h3>Performance</h3><p className="muted-copy">Token usage is not connected yet.</p>
        <div className="token-counts"><div><span>Input tokens</span><strong>—</strong></div><div><span>Output tokens</span><strong>—</strong></div><div><span>Total tokens</span><strong>—</strong></div></div>
        <h4>Recent token usage</h4><div className="table-scroll"><table className="details-table"><thead><tr><th>Request</th><th>Input</th><th>Output</th><th>Total</th></tr></thead><tbody><tr><td colSpan={4} className="table-empty">No token usage recorded.</td></tr></tbody></table></div>
      </>}
      {section === "Payment" && <>
        <h3>Payment</h3>
        <div className="payment-method"><div><h4>Current payment method</h4><p>No payment method added.</p></div><button className="pill" onClick={() => setBillingNotice("Payments are not connected yet.")}>Add payment method</button></div>
        {billingNotice && <p className="status-note" role="status">{billingNotice}</p>}
        <h4 className="section-space">Billing history</h4><div className="table-scroll"><table className="details-table"><thead><tr><th>Date</th><th>Description</th><th>Amount</th><th>Status</th></tr></thead><tbody><tr><td colSpan={4} className="table-empty">No billing history yet.</td></tr></tbody></table></div>
      </>}
    </section>
  </div>;
}

function FilesView({ entries, setEntries }: {
  entries: FileEntry[];
  setEntries: Dispatch<SetStateAction<FileEntry[]>>;
}) {
  const [folderId, setFolderId] = useState<string | null>(null);
  const [menu, setMenu] = useState<{ id: string; x: number; y: number } | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const editorDialog = useRef<HTMLDialogElement>(null);
  const contextMenu = useRef<HTMLDivElement>(null);
  const menuTrigger = useRef<HTMLElement | null>(null);
  const currentFolder = entries.find(entry => entry.id === folderId);
  const menuEntry = entries.find(entry => entry.id === menu?.id);
  const editingEntry = entries.find(entry => entry.id === editId);
  const protectedFolder = editId === "input" || editId === "output";
  const visibleEntries = entries.filter(entry => entry.parentId === folderId).sort((a, b) => (a.kind === b.kind ? a.name.localeCompare(b.name) : a.kind === "folder" ? -1 : 1));
  const ancestors: FileEntry[] = [];
  let parent = currentFolder;
  while (parent) { ancestors.unshift(parent); parent = entries.find(entry => entry.id === parent?.parentId); }

  useEffect(() => {
    if (!menu) return;
    contextMenu.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const close = (event: PointerEvent) => { if (!contextMenu.current?.contains(event.target as Node)) setMenu(null); };
    document.addEventListener("pointerdown", close);
    const onResize = () => setMenu(null);
    window.addEventListener("resize", onResize);
    return () => { document.removeEventListener("pointerdown", close); window.removeEventListener("resize", onResize); };
  }, [menu]);

  function openMenu(entry: FileEntry, x: number, y: number, trigger: HTMLElement) {
    menuTrigger.current = trigger;
    setMenu({ id: entry.id, x: Math.max(8, Math.min(x, window.innerWidth - 220)), y: Math.max(8, Math.min(y, window.innerHeight - 160)) });
  }
  function edit(entry?: FileEntry) {
    setMenu(null); setEditId(entry?.id ?? null); setName(entry?.name ?? ""); setDescription(entry?.description ?? ""); setError("");
    editorDialog.current?.showModal();
  }
  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanName = name.trim();
    const targetParent = editingEntry ? editingEntry.parentId : folderId;
    if (!cleanName || /[\\/]/.test(cleanName)) { setError("Enter a name without slashes."); return; }
    if (entries.some(entry => entry.parentId === targetParent && entry.id !== editId && entry.name.toLowerCase() === cleanName.toLowerCase())) { setError("An item with this name already exists in this folder."); return; }
    if (editId) setEntries(current => current.map(entry => entry.id === editId ? { ...entry, name: protectedFolder ? entry.name : cleanName, description } : entry));
    else setEntries(current => [...current, { id: crypto.randomUUID(), parentId: folderId, name: cleanName, kind: "folder", description }]);
    editorDialog.current?.close();
  }
  function fileSize(entry: FileEntry) {
    if (entry.kind === "folder") return `${entries.filter(item => item.parentId === entry.id).length} items`;
    const bytes = entry.file?.size ?? new Blob([entry.text ?? ""]).size;
    return bytes < 1024 ? `${bytes} B` : bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return <section className="files-view" aria-label="Files browser">
    <header className="files-heading"><h1>Files</h1><button className="pill primary-pill" onClick={() => edit()}><FolderPlus size={17} />New folder</button></header>
    <div className="files-toolbar"><nav aria-label="Folder path"><button onClick={() => { setFolderId(null); setMenu(null); }}>Files</button>{ancestors.map(folder => <span key={folder.id}><ChevronRight size={14} /><button onClick={() => { setFolderId(folder.id); setMenu(null); }}>{folder.name}</button></span>)}</nav>{folderId && <button className="pill" onClick={() => { setFolderId(currentFolder?.parentId ?? null); setMenu(null); }}><ArrowLeft size={14} />Back</button>}</div>
    <div className="file-list" onScroll={() => setMenu(null)}>
      <div className="file-list-head"><span>Name</span><span>Type</span><span>Size / items</span><span /></div>
      {visibleEntries.map(entry => <div key={entry.id} className="file-row" onContextMenu={e => { e.preventDefault(); openMenu(entry, e.clientX, e.clientY, e.currentTarget.querySelector<HTMLButtonElement>(".file-name")!); }}>
        <button className="file-name" onClick={() => entry.kind === "folder" ? (setFolderId(entry.id), setMenu(null)) : edit(entry)}>{entry.kind === "folder" ? <Folder size={24} /> : <FileText size={22} />}<span><strong>{entry.name}</strong>{entry.description && <small>{entry.description}</small>}</span></button>
        <span className="file-type">{entry.kind === "folder" ? "Folder" : entry.file?.type === "application/pdf" ? "PDF" : entry.file?.type.startsWith("image/") ? "Image" : "Text"}</span><span className="file-size">{fileSize(entry)}</span>
        <button className="icon-button" aria-label={`Actions for ${entry.name}`} aria-haspopup="menu" onClick={e => { const rect = e.currentTarget.getBoundingClientRect(); openMenu(entry, rect.right - 200, rect.bottom + 4, e.currentTarget); }}><MoreHorizontal size={20} /></button>
      </div>)}
      {!visibleEntries.length && <div className="files-empty"><Folder size={38} strokeWidth={1.2} /><h3>This folder is empty</h3><p>{folderId === "input" ? "Uploaded images, PDFs, and submitted text appear here." : folderId === "output" ? "Run an input to save its result here." : "Create a folder to start organizing."}</p><button className="pill" onClick={() => edit()}><Plus size={15} />New folder</button></div>}
    </div>
    <p className="files-footnote">Right-click an item or use its ••• menu to edit details. Files and folders are temporary and clear on refresh.</p>
    {menu && menuEntry && <div className="file-context-menu" role="menu" aria-label={`Actions for ${menuEntry.name}`} ref={contextMenu} style={{ left: menu.x, top: menu.y }} onKeyDown={e => {
      const buttons = Array.from(e.currentTarget.querySelectorAll<HTMLButtonElement>("button"));
      const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
      if (e.key === "Escape") { setMenu(null); menuTrigger.current?.focus(); }
      if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); buttons[(index + (e.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length]?.focus(); }
      if (e.key === "Tab") setMenu(null);
    }}>
      {menuEntry.kind === "folder" && <button role="menuitem" onClick={() => { setFolderId(menuEntry.id); setMenu(null); }}><Folder size={16} />Open folder</button>}
      <button role="menuitem" onClick={() => edit(menuEntry)}><Pencil size={16} />Edit details</button>
      {menuEntry.kind === "file" && <button role="menuitem" onClick={() => { saveDownload(menuEntry.file ?? new Blob([menuEntry.text ?? ""], { type: "text/plain" }), menuEntry.name); setMenu(null); }}><Download size={16} />Download</button>}
    </div>}
    <dialog ref={editorDialog} className="auth-dialog file-editor" aria-labelledby="file-editor-title" onCancel={() => setError("")}>
      <button className="close-dialog" aria-label="Close file details" onClick={() => editorDialog.current?.close()}><X size={20} /></button>
      <h2 id="file-editor-title">{editId ? "Edit details" : "New folder"}</h2>
      <form onSubmit={submit}><label htmlFor="entry-name">Name</label><input id="entry-name" autoFocus value={name} maxLength={120} readOnly={protectedFolder} onChange={e => setName(e.target.value)} required />{protectedFolder && <p className="muted-copy">The Input and Output folder names are fixed.</p>}<label htmlFor="entry-description">Description <span className="optional-label">(optional)</span></label><textarea id="entry-description" value={description} maxLength={300} onChange={e => setDescription(e.target.value)} />{error && <p className="upload-error" role="alert">{error}</p>}<div className="dialog-actions"><button className="pill" type="button" onClick={() => editorDialog.current?.close()}>Cancel</button><button className="run-button" type="submit">{editId ? "Save changes" : "Create folder"}</button></div></form>
    </dialog>
  </section>;
}

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
  const outputImageUrl = useFileUrl(outputImage);
  const outputPdfUrl = useFileUrl(outputPdf);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [word, setWord] = useState("");
  const [status, setStatus] = useState("");
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  const picker = useRef<HTMLInputElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);

  const [preferences, setPreferences] = useState<Preferences>({ encryption: false, lossless: true, background: "#0b0610" });
  const [entries, setEntries] = useState<FileEntry[]>([
    { id: "input", parentId: null, name: "Input", kind: "folder", description: "Uploaded files and source text" },
    { id: "output", parentId: null, name: "Output", kind: "folder", description: "Files and text after Run" },
  ]);
  const settingsDialog = useRef<HTMLDialogElement>(null);
  const [authNotice, setAuthNotice] = useState("");
  const [defineNotice, setDefineNotice] = useState("");

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

  function downloadPdf() {
    if (outputPdf) saveDownload(outputPdf, outputPdf.name);
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
        <section className="panel" aria-labelledby="input-title">
          <div className="panel-heading"><h1 id="input-title">Input</h1><div className="select-wrap"><select aria-label="Input type" value={input} onChange={e => { setInput(e.target.value as InputType); setError(""); setDragging(false); setStatus(""); }}><option>Image</option><option>Texts</option><option>PDF</option></select><ChevronDown size={16} /></div></div>
          <div className="input-body">
            <input key={input} ref={picker} className="file-picker" type="file" accept={input === "PDF" ? "application/pdf,.pdf" : "image/png,image/jpeg"} aria-label={input === "PDF" ? "Choose a PDF" : "Choose an image"} onChange={e => { chooseFile(e.target.files?.[0]); e.target.value = ""; }} />
            {input === "Texts" ? <textarea className="text-input" aria-label="Text to copy" value={text} onChange={e => setText(e.target.value)} placeholder="Type or paste your text here..." /> : <div className={`image-area${dragging ? " dragging" : ""}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false); }} onDrop={e => { e.preventDefault(); setDragging(false); chooseFile(e.dataTransfer.files[0]); }}>
              {activeFile ? <>
                {input === "Image" ? <img className="image-preview" src={imageUrl || undefined} alt={`Preview of ${activeFile.name}`} onError={() => { setError("This image could not be opened. Please choose another image."); setImageFile(null); }} /> : <div className="pdf-input-card"><FileText size={44} strokeWidth={1.3} /><span>{activeFile.name}</span><small>Click Run, then select PDF in Output.</small></div>}
                <div className="image-details"><span>{activeFile.name}</span><div><button className="pill" onClick={() => picker.current?.click()}>Replace</button><button className="pill" onClick={() => { input === "PDF" ? setPdfFile(null) : setImageFile(null); setError(""); setStatus(""); }}>Remove</button></div></div>
              </> : <button className="dropzone" onClick={() => picker.current?.click()}><Upload size={20} strokeWidth={1.5} /><span>Drop {input === "PDF" ? "a PDF" : "an image"} here, or click to browse</span><small>{input === "PDF" ? "PDF up to 25MB" : "PNG, JPG up to 10MB"}</small></button>}
            </div>}
            {error && <p role="alert" className="upload-error">{error}</p>}
            <p className="run-status" role="status">{status}</p>
            <div className="actions"><button className="run-button" disabled={!canRun} onClick={run}>Run</button></div>
          </div>
        </section>
        <section className="panel output-panel" aria-labelledby="output-title">
          <div className="panel-heading"><h2 id="output-title">Output</h2><div className="select-wrap"><select aria-label="Output type" value={outputType} onChange={e => { setOutputType(e.target.value as OutputType); setWord(""); }}><option>Summary</option><option>Image</option><option>PDF</option></select><ChevronDown size={16} /></div></div>
          <div className="output-body result-body">
            {outputType === "Summary" ? <>
              <div className="summary-layout">
                <textarea className="text-input summary-text" aria-label="Summary output" readOnly value={summary}
                  placeholder="Enter text on the left and click Run."
                  onBlur={e => { if (!(e.relatedTarget instanceof Element) || !e.relatedTarget.closest(".definition-side")) setWord(""); }}
                  onSelect={e => {
                    const field = e.currentTarget;
                    setWord(field.value.slice(field.selectionStart, field.selectionEnd).trim());
                    setDefineNotice("");
                  }} />
                {word && <aside className="definition-side" aria-label="Definition panel">
                  <h3><BookOpen size={16} />Define</h3>
                  <p className="selected-word">{word}</p>
                  <button className="pill" onMouseDown={e => e.preventDefault()} onClick={() => setDefineNotice("Definitions are not connected yet.")}>Define</button>
                  {defineNotice && <p className="muted-copy" role="status">{defineNotice}</p>}
                </aside>}
              </div>
            </> : outputType === "Image" && outputImage && outputImageUrl ? <><div className="output-media"><img src={outputImageUrl} alt={`Output: ${outputImage.name}`} /></div><p className="output-filename">{outputImage.name}</p></> : outputType === "PDF" && outputPdf && outputPdfUrl ? <>
              <object className="pdf-viewer" data={outputPdfUrl} type="application/pdf" aria-label={`PDF preview: ${outputPdf.name}`}><p>This browser cannot preview this PDF. Use Download PDF below.</p></object>
              <div className="pdf-download"><span>{outputPdf.name}</span><button className="pill" type="button" onClick={downloadPdf}><Download size={15} />Download PDF</button></div>
            </> : <div className="media-empty empty-state"><span className="empty-icon"><Plus size={20} strokeWidth={1.5} /></span><p>Upload {outputType === "PDF" ? "a PDF" : "an image"} on the left,<br />then click Run to show it here.</p></div>}
          </div>
        </section>
      </main>
    </div>
    <button className="settings-launcher pill" onClick={() => { setWord(""); settingsDialog.current?.showModal(); }} aria-haspopup="dialog"><Settings size={19} />Settings</button>
    <dialog ref={settingsDialog} className="settings-dialog" aria-labelledby="settings-title" onClick={e => {
      if (e.target !== e.currentTarget) return;
      const rect = e.currentTarget.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) settingsDialog.current?.close();
    }}>
      <header className="settings-header"><h2 id="settings-title">Settings</h2><button className="icon-button" aria-label="Close settings" onClick={() => settingsDialog.current?.close()}><X size={21} /></button></header>
      <SettingsContent preferences={preferences} onChange={setPreferences} entries={entries} setEntries={setEntries} />
    </dialog>
    <dialog ref={dialog} className="auth-dialog" aria-labelledby="auth-title" onClick={e => { if (e.target === e.currentTarget) { const bounds = e.currentTarget.getBoundingClientRect(); if (e.clientX < bounds.left || e.clientX > bounds.right || e.clientY < bounds.top || e.clientY > bounds.bottom) dialog.current?.close(); } }}>
      <button className="close-dialog" aria-label="Close sign-in dialog" onClick={() => dialog.current?.close()}><X size={20} /></button>
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
    </dialog>
  </div>;
}
