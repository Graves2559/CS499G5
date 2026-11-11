import { useEffect, useState } from "react";
import type { FileEntry } from "../types";
import { DEFAULT_ENTRIES, uniqueName } from "../domain/files";
import type { FilesGateway } from "./ports";

// The user's folders and files. Signed in, the server keeps them (and this hook mirrors them); signed out,
// they are temporary and live only in this page. Components call these actions and never touch the network.
export function useFiles(gateway: FilesGateway, signedIn: boolean, reportError: (message: string) => void) {
  const [entries, setEntries] = useState<FileEntry[]>(DEFAULT_ENTRIES);

  useEffect(() => {
    if (!signedIn) { setEntries(DEFAULT_ENTRIES); return; }
    let cancelled = false;
    gateway.listEntries().then(list => { if (!cancelled) setEntries(list); }).catch(() => {});
    return () => { cancelled = true; };
  }, [gateway, signedIn]);

  const message = (failure: unknown, fallback: string) => failure instanceof Error ? failure.message : fallback;

  // When signed in, the server keeps the file. If saving fails, the local copy is dropped and the error is shown.
  function saveToServer(id: string, parentId: string, name: string, content: Blob, removeOnFail: boolean) {
    if (!signedIn) return;
    gateway.putFile(id, parentId, name, content).catch(failure => {
      if (removeOnFail) setEntries(current => current.filter(entry => entry.id !== id));
      reportError(message(failure, "Could not save to the server."));
    });
  }

  return {
    entries,
    signedIn,

    storeFile(parentId: string, file: File) {
      if (entries.some(entry => entry.parentId === parentId && entry.file === file)) return;
      const id = crypto.randomUUID();
      const name = uniqueName(entries, parentId, file.name);
      setEntries(current => [...current, { id, parentId, name, kind: "file", description: "", file, dateModified: new Date().toISOString() }]);
      saveToServer(id, parentId, name, file, true);
    },

    storeText(parentId: string, value: string) {
      const id = `${parentId}-text`;
      const name = parentId === "input" ? "input.txt" : "summary.txt";
      const now = new Date().toISOString();
      setEntries(current => current.some(entry => entry.id === id)
        ? current.map(entry => entry.id === id ? { ...entry, text: value, dateModified: now } : entry)
        : [...current, { id, parentId, name, kind: "file", description: "", text: value, dateModified: now }]);
      saveToServer(id, parentId, name, new Blob([value], { type: "text/plain" }), false);
    },

    // The actions below throw an Error with a message to show when the server refuses.
    async createFolder(parentId: string | null, name: string, description: string) {
      const id = crypto.randomUUID();
      if (signedIn) await gateway.createFolder({ id, parentId, name, description });
      setEntries(current => [...current, { id, parentId, name, kind: "folder", description }]);
    },

    async updateDetails(entry: FileEntry, name: string, description: string) {
      const protectedFolder = entry.id === "input" || entry.id === "output";
      if (signedIn) await gateway.updateEntry(entry.id, { name: protectedFolder ? undefined : name, description });
      setEntries(current => current.map(item => item.id !== entry.id ? item : {
        ...item,
        name: protectedFolder ? item.name : name,
        description,
        dateModified: item.kind === "file" && (item.name !== name || item.description !== description) ? new Date().toISOString() : item.dateModified,
      }));
    },

    async toggleFavorite(entry: FileEntry) {
      const favorite = !entry.favorite;
      if (signedIn) await gateway.updateEntry(entry.id, { favorite });
      setEntries(current => current.map(item => item.id === entry.id ? { ...item, favorite } : item));
    },

    async contentOf(entry: FileEntry): Promise<Blob> {
      return entry.file ?? (entry.text !== undefined ? new Blob([entry.text], { type: "text/plain" }) : gateway.fileContent(entry.id));
    },
  };
}

export type Files = ReturnType<typeof useFiles>;
