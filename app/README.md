# ClosedAI Frontend

A React + TypeScript frontend, bundled and served by [Vite](https://vite.dev/).

> `package.json`, `vite.config.ts`, and `index.html` live at the **repository root** (`CS499G5/`), not inside this `app/` folder — run all commands below from the repo root, not from `app/`.

## Requirements

- Node.js >= 22.13.0

## Installation

### macOS

```bash
# from the repo root (e.g., CS499G5)
node -v   # confirm >= 22.13.0; install via https://nodejs.org or `brew install node` if needed
npm install
npm install --save-dev kill-port
```

### Linux

```bash
# from the repo root (e.g., CS499G5)
node -v   # confirm >= 22.13.0
npm install
npm install --save-dev kill-port
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
npm install --save-dev kill-port
```

## Running the Program

### Development (hot-reload)

```bash
npm run dev
```

Starts the Vite dev server at `http://127.0.0.1:5173` with instant hot-module-reload — edits to `.tsx`/`.css` files show up in the browser immediately, no manual rebuild needed. This works the same way on macOS, Linux, and Windows.

> npm automatically runs `predev` immediately before `dev`, so every `npm run dev` kills whatever's on port 5173 first, then starts Vite fresh — no manual `lsof`/`kill` step needed, and it's cross-platform (works the same on macOS, Linux, and Windows).

### Production build + preview

```bash
npm run build
npm start
```

`npm run build` bundles the app into `dist/`; `npm start` (an alias for `vite preview`) serves that built output at `http://127.0.0.1:5173`.

If port 5173 is already in use (e.g., a previous run didn't shut down cleanly):

```bash
lsof -ti :5173 | xargs kill
```

> **Windows:** use `netstat -ano | findstr :5173` to find the PID, then `taskkill /PID <pid> /F`.
