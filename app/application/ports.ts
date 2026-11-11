// Ports: what the application layer needs from the outside world. The infrastructure layer implements them
// (infrastructure/api.ts); the hooks here depend only on these interfaces, never on fetch or a URL.
import type { FileEntry } from "../types";

export interface AuthGateway {
  me(): Promise<string | null>;
  login(username: string, password: string): Promise<string>;
  register(username: string, email: string, password: string): Promise<string>;
  logout(): Promise<void>;
}

export interface FilesGateway {
  listEntries(): Promise<FileEntry[]>;
  createFolder(folder: { id: string; parentId: string | null; name: string; description: string }): Promise<void>;
  updateEntry(id: string, changes: { name?: string; description?: string; favorite?: boolean }): Promise<void>;
  // Creates the file, or replaces its content when the id already exists.
  putFile(id: string, parentId: string, name: string, content: Blob): Promise<void>;
  fileContent(id: string): Promise<Blob>;
}
