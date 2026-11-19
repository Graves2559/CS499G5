import { useEffect, useRef, useState } from "react";
import { Plus, X, FileText, Download, Folder, FolderPlus, MoreHorizontal, Pencil, ChevronRight, ArrowLeft, Star, ArrowUp, ArrowDown } from "lucide-react";
import type { FileEntry } from "../types";
import type { Files } from "../application/useFiles";
import { FAVORITES_FOLDER, FAVORITES_ID, bytesOf, formatBytes, itemsIn, nameProblem, sortEntries, typeLabel, type SortMetric } from "../domain/files";
import { saveDownload } from "../infrastructure/download";

export default function FilesView({ files }: { files: Files }) {
  const { entries, signedIn } = files;
  const [folderId, setFolderId] = useState<string | null>(null);
  const [sortMetric, setSortMetric] = useState<SortMetric>("name");
  const [descending, setDescending] = useState(false);
  const [menu, setMenu] = useState<{ id: string; x: number; y: number } | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const editorDialog = useRef<HTMLDialogElement>(null);
  const contextMenu = useRef<HTMLDivElement>(null);
  const menuTrigger = useRef<HTMLElement | null>(null);
  const withFavorites = [FAVORITES_FOLDER, ...entries];
  const inFavorites = folderId === FAVORITES_ID;
  const currentFolder = withFavorites.find(entry => entry.id === folderId);
  const menuEntry = withFavorites.find(entry => entry.id === menu?.id);
  const editingEntry = entries.find(entry => entry.id === editId);
  const protectedFolder = editId === "input" || editId === "output";
  const listed = inFavorites ? itemsIn(entries, FAVORITES_ID) : withFavorites.filter(entry => entry.parentId === folderId);
  const visibleEntries = sortEntries(listed, sortMetric, descending);
  const ancestors: FileEntry[] = [];
  let parent = currentFolder;
  while (parent) { ancestors.unshift(parent); parent = withFavorites.find(entry => entry.id === parent?.parentId); }

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
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanName = name.trim();
    const problem = nameProblem(entries, editingEntry ? editingEntry.parentId : folderId, editId, cleanName);
    if (problem) { setError(problem); return; }
    try {
      if (editingEntry) await files.updateDetails(editingEntry, cleanName, description);
      else await files.createFolder(folderId, cleanName, description);
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Could not save to the server."); return; }
    editorDialog.current?.close();
  }
  async function toggleFavorite(entry: FileEntry) {
    setMenu(null); setNotice("");
    try { await files.toggleFavorite(entry); }
    catch (failure) { setNotice(failure instanceof Error ? failure.message : "Could not update the favorite."); }
  }
  function modifiedText(entry: FileEntry) {
    return entry.dateModified ? `Modified ${new Date(entry.dateModified).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}` : "";
  }
  async function download(entry: FileEntry) {
    setMenu(null);
    try { saveDownload(await files.contentOf(entry), entry.name); }
    catch (failure) { setNotice(failure instanceof Error ? failure.message : "Could not download this file."); }
  }
  function fileSize(entry: FileEntry) {
    return entry.kind === "folder" ? `${itemsIn(entries, entry.id).length} items` : formatBytes(bytesOf(entry));
  }
  const fileType = typeLabel;

  return <section className="files-view" aria-label="Files browser">
    <header className="files-heading"><h1>Files</h1><button className="pill primary-pill" disabled={inFavorites} title={inFavorites ? "Folders cannot be created in Favorites" : undefined} onClick={() => edit()}><FolderPlus size={17} />New folder</button></header>
    <div className="files-toolbar"><nav aria-label="Folder path"><button onClick={() => { setFolderId(null); setMenu(null); }}>Files</button>{ancestors.map(folder => <span key={folder.id}><ChevronRight size={14} /><button onClick={() => { setFolderId(folder.id); setMenu(null); }}>{folder.name}</button></span>)}</nav>
      <div className="sort-controls"><label htmlFor="files-sort">Sort by</label>
        <select id="files-sort" value={sortMetric} onChange={e => setSortMetric(e.target.value as SortMetric)}><option value="name">Name</option><option value="date">Date modified</option><option value="favorite">Favorite</option></select>
        <button className="icon-button" aria-label={descending ? "Sorted descending. Switch to ascending" : "Sorted ascending. Switch to descending"} title={descending ? "Descending" : "Ascending"} onClick={() => setDescending(current => !current)}>{descending ? <ArrowDown size={16} /> : <ArrowUp size={16} />}</button></div>
      {folderId && <button className="pill" onClick={() => { setFolderId(currentFolder?.parentId ?? null); setMenu(null); }}><ArrowLeft size={14} />Back</button>}</div>
    <div className="file-list" onScroll={() => setMenu(null)}>
      <div className="file-list-head"><span>Name</span><span>Type</span><span>Size / items</span><span /></div>
      {visibleEntries.map(entry => <div key={entry.id} className="file-row" onContextMenu={e => { e.preventDefault(); openMenu(entry, e.clientX, e.clientY, e.currentTarget.querySelector<HTMLButtonElement>(".file-name")!); }}>
        <button className="file-name" onClick={() => entry.kind === "folder" ? (setFolderId(entry.id), setMenu(null)) : edit(entry)}>{entry.kind === "folder" ? (entry.id === FAVORITES_ID ? <Star size={24} /> : <Folder size={24} />) : <FileText size={22} />}<span><strong>{entry.name}{entry.favorite && <Star className="fav-star" size={14} fill="currentColor" aria-label="Favorite" />}</strong>{entry.description && <small>{entry.description}</small>}{entry.kind === "file" && modifiedText(entry) && <small>{modifiedText(entry)}</small>}</span></button>
        <span className="file-type">{fileType(entry)}</span><span className="file-size">{fileSize(entry)}</span>
        <button className="icon-button" aria-label={`Actions for ${entry.name}`} aria-haspopup="menu" onClick={e => { const rect = e.currentTarget.getBoundingClientRect(); openMenu(entry, rect.right - 200, rect.bottom + 4, e.currentTarget); }}><MoreHorizontal size={20} /></button>
      </div>)}
      {!visibleEntries.length && <div className="files-empty"><Folder size={38} strokeWidth={1.2} /><h3>This folder is empty</h3><p>{inFavorites ? "Open a file's ••• menu and choose Add to favorites." : folderId === "input" ? "Uploaded images, PDFs, and submitted text appear here." : folderId === "output" ? "Run an input to save its result here." : "Create a folder to start organizing."}</p>{!inFavorites && <button className="pill" onClick={() => edit()}><Plus size={15} />New folder</button>}</div>}
    </div>
    <p className="files-footnote">Right-click an item or use its ••• menu to edit details. {signedIn ? "Files and folders are saved to your account." : "Files and folders are temporary and clear on refresh. Sign in to save them."}</p>
    {notice && <p className="upload-error" role="alert">{notice}</p>}
    {menu && menuEntry && <div className="file-context-menu" role="menu" aria-label={`Actions for ${menuEntry.name}`} ref={contextMenu} style={{ left: menu.x, top: menu.y }} onKeyDown={e => {
      const buttons = Array.from(e.currentTarget.querySelectorAll<HTMLButtonElement>("button"));
      const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
      if (e.key === "Escape") { setMenu(null); menuTrigger.current?.focus(); }
      if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); buttons[(index + (e.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length]?.focus(); }
      if (e.key === "Tab") setMenu(null);
    }}>
      {menuEntry.kind === "folder" && <button role="menuitem" onClick={() => { setFolderId(menuEntry.id); setMenu(null); }}><Folder size={16} />Open folder</button>}
      {menuEntry.id !== FAVORITES_ID && <button role="menuitem" onClick={() => edit(menuEntry)}><Pencil size={16} />Edit details</button>}
      {menuEntry.kind === "file" && <button role="menuitem" onClick={() => toggleFavorite(menuEntry)}><Star size={16} fill={menuEntry.favorite ? "currentColor" : "none"} />{menuEntry.favorite ? "Remove from favorites" : "Add to favorites"}</button>}
      {menuEntry.kind === "file" && <button role="menuitem" onClick={() => download(menuEntry)}><Download size={16} />Download</button>}
    </div>}
    <dialog ref={editorDialog} className="auth-dialog file-editor" aria-labelledby="file-editor-title" onCancel={() => setError("")}>
      <button className="close-dialog" aria-label="Close file details" onClick={() => editorDialog.current?.close()}><X size={20} /></button>
      <h2 id="file-editor-title">{editId ? "Edit details" : "New folder"}</h2>
      <form onSubmit={submit}><label htmlFor="entry-name">Name</label><input id="entry-name" autoFocus value={name} maxLength={120} readOnly={protectedFolder} onChange={e => setName(e.target.value)} required />{protectedFolder && <p className="muted-copy">The Input and Output folder names are fixed.</p>}<label htmlFor="entry-description">Description <span className="optional-label">(optional)</span></label><textarea id="entry-description" value={description} maxLength={300} onChange={e => setDescription(e.target.value)} />{error && <p className="upload-error" role="alert">{error}</p>}<div className="dialog-actions"><button className="pill" type="button" onClick={() => editorDialog.current?.close()}>Cancel</button><button className="run-button" type="submit">{editId ? "Save changes" : "Create folder"}</button></div></form>
    </dialog>
  </section>;
}
