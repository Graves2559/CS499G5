// Domain rules for files and folders: pure functions on plain data. No React, no network.
import type { FileEntry } from "../types";

export const DEFAULT_ENTRIES: FileEntry[] = [
  { id: "input", parentId: null, name: "Input", kind: "folder", description: "Uploaded files and source text" },
  { id: "output", parentId: null, name: "Output", kind: "folder", description: "Files and text after Run" },
];

// The Favorites folder is virtual (like StorageManager's): it lists favorited files, holds nothing itself,
// and nothing can be added to or created inside it.
export const FAVORITES_ID = "favorites";
export const FAVORITES_FOLDER: FileEntry = { id: FAVORITES_ID, parentId: null, name: "Favorites", kind: "folder", description: "Your favorite files" };

export type SortMetric = "name" | "date" | "favorite";

// Same rules as Sorter.py: folders first, then files by the chosen metric (name, date modified, favorite).
// Descending reverses the metric; ties are always broken by name.
export function sortEntries(list: FileEntry[], metric: SortMetric, descending: boolean): FileEntry[] {
  const direction = descending ? -1 : 1;
  const modified = (entry: FileEntry) => Date.parse(entry.dateModified ?? "") || 0;
  return [...list].sort((a, b) => {
    if (a.kind !== b.kind) return a.kind === "folder" ? -1 : 1;
    let result = 0;
    if (metric === "name") result = a.name.localeCompare(b.name);
    else if (a.kind === "file" && metric === "date") result = modified(a) - modified(b);
    else if (a.kind === "file" && metric === "favorite") result = Number(!!b.favorite) - Number(!!a.favorite);
    return result !== 0 ? result * direction : a.name.localeCompare(b.name);
  });
}

const sameName = (a: string, b: string) => a.toLowerCase() === b.toLowerCase();

// "pic.png" -> "pic (2).png" when the folder already has a pic.png.
export function uniqueName(entries: FileEntry[], parentId: string | null, name: string): string {
  const taken = (candidate: string) => entries.some(entry => entry.parentId === parentId && sameName(entry.name, candidate));
  if (!taken(name)) return name;
  const dot = name.lastIndexOf(".");
  const [base, extension] = dot > 0 ? [name.slice(0, dot), name.slice(dot)] : [name, ""];
  let count = 2;
  while (taken(`${base} (${count})${extension}`)) count++;
  return `${base} (${count})${extension}`;
}

// Returns an error message, or null when the name is fine. `exceptId` is the item being renamed.
export function nameProblem(entries: FileEntry[], parentId: string | null, exceptId: string | null, name: string): string | null {
  if (!name || /[\\/]/.test(name)) return "Enter a name without slashes.";
  if (entries.some(entry => entry.parentId === parentId && entry.id !== exceptId && sameName(entry.name, name))) return "An item with this name already exists in this folder.";
  return null;
}

export function bytesOf(entry: FileEntry): number {
  return entry.file?.size ?? (entry.text !== undefined ? new Blob([entry.text]).size : entry.size ?? 0);
}

export function formatBytes(bytes: number): string {
  return bytes < 1024 ? `${bytes} B` : bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function typeLabel(entry: FileEntry): string {
  const mime = entry.file?.type || entry.mimeType || "";
  return entry.kind === "folder" ? "Folder" : mime === "application/pdf" ? "PDF" : mime.startsWith("image/") ? "Image" : "Text";
}

export function itemsIn(entries: FileEntry[], folderId: string): FileEntry[] {
  return folderId === FAVORITES_ID ? entries.filter(entry => entry.kind === "file" && entry.favorite) : entries.filter(entry => entry.parentId === folderId);
}
