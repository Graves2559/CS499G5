# ClosedAI Frontend

A React + TypeScript frontend, bundled with [rolldown](https://rolldown.rs/) into static files and served by a small Node.js static file server.

> `package.json` and the build scripts live at the **repository root** (`CS499G5/`), not inside this `app/` folder — run all commands below from the repo root, not from `app/`.

## Requirements

- Node.js >= 22.13.0

## Installation

### macOS

```bash
# from the repo root (e.g., CS499G5)
node -v   # confirm >= 22.13.0; install via https://nodejs.org or `brew install node` if needed
npm install
```

### Linux

```bash
# from the repo root (e.g., CS499G5)
node -v   # confirm >= 22.13.0
npm install
```

> If your distro's package manager only has an older Node version, install a current one via [nvm](https://github.com/nvm-sh/nvm):
> ```bash
> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
> nvm install 22
> ```

### Windows

**PowerShell / Command Prompt:**
```powershell
# from the repo root (e.g., CS499G5)
node -v   # confirm >= 22.13.0; install via https://nodejs.org if needed
npm install
```

## Running the Program

Build the static bundle, then serve it:

```bash
npm run build
npm start
```

This builds the app into `dist/` and serves it at `http://127.0.0.1:5173`.

> The `npm run dev` script (`start msedge ... && node scripts/preview-static.mjs`) is **Windows-only** — it shells out to `start`, a Windows `cmd.exe` builtin, to auto-launch Microsoft Edge. On macOS/Linux, use `npm run build && npm start` instead and open `http://127.0.0.1:5173` manually in any browser.
