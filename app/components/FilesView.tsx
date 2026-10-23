import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { Plus, X, FileText, Download, Folder, FolderPlus, MoreHorizontal, Pencil, ChevronRight, ArrowLeft } from "lucide-react";
import type { FileEntry } from "../types";
import { saveDownload } from "../utils/download";

export default function FilesView({ entries, setEntries }: {
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
