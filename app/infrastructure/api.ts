// Infrastructure: the only code that talks to the server (fetch, URLs, status codes). It implements the gateway
// ports of the application layer, so nothing else needs to know how the server is reached.
import type { FileEntry } from "../types";
import type { AuthGateway, FilesGateway } from "../application/ports";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(path, { credentials: "same-origin", ...init });
  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try { const body = await response.json(); if (typeof body.detail === "string") message = body.detail; } catch { /* not JSON */ }
    throw new ApiError(response.status, message);
  }
  return response;
}

const json = (body: unknown): RequestInit => ({ headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api: AuthGateway & FilesGateway = {
  async me() { return (await (await request("/api/me")).json()).username ?? null; },
  async login(username, password) {
    return (await (await request("/api/login", { method: "POST", ...json({ username, password }) })).json()).username;
  },
  async logout() { await request("/api/logout", { method: "POST" }); },
  async register(username, email, password) {
    return (await (await request("/api/register", { method: "POST", ...json({ username, email, password }) })).json()).username;
  },
  async listEntries(): Promise<FileEntry[]> { return (await request("/api/entries")).json(); },
  async createFolder(folder) { await request("/api/folders", { method: "POST", ...json(folder) }); },
  async updateEntry(id, changes) {
    await request(`/api/entries/${encodeURIComponent(id)}`, { method: "PATCH", ...json(changes) });
  },
  async putFile(id, parentId, name, content) {
    const form = new FormData();
    form.append("parentId", parentId);
    form.append("name", name);
    form.append("file", content, name);
    await request(`/api/files/${encodeURIComponent(id)}`, { method: "PUT", body: form });
  },
  async fileContent(id) { return (await request(`/api/files/${encodeURIComponent(id)}/content`)).blob(); },
};
