
# Installation (one-time)
docker-compose.yml is to allow you to click the button in the Docker application to run it, without having to interact with the terminal to execute the program.

One `docker compose up --build` starts everything:

| Service | Address | Purpose |
|---|---|---|
| wi29-server | http://localhost:8000 | FastAPI server + the built UI |
| UserCredentials (postgres) | localhost:5432 | Users, key records, and a small index of journal entries (metadata + `media_id`) (databases `user_db`, `keyrecord_db`, `indexDB`) |
| IMG_VID_TXT (mongo) | localhost:27018 | Image/text/video content (GridFS, database `UserFiles`) |
| pgadmin | http://localhost:5050 | Postgres web GUI |

## Frontend

1. Install and start **Docker Desktop**. Nothing else needs to be installed to run the stack (no local Postgres or MongoDB).
2. Build the UI (the server image copies the `dist/` folder, which is not committed to git, so the Docker build fails without it):
   1. Go to the **app** folder and follow the README.md instructions (Node.js >= 22.13.0, `npm install`)
   2. From this folder (CS499G5) run: `npm run build`
   3. Re-run `npm run build` whenever the UI changes, then `docker compose up --build`
3. (Optional) To change passwords or ports, copy `backend/Database/.env.example` to `.env` in this folder and edit it. Without it, the defaults below are used.

## Accounts and saved files

- Sign up in the Login dialog (username, email, password and a confirmation), then sign in with your username or email. Passwords need at least 8 characters with an uppercase letter, a lowercase letter, a number and a symbol; they are stored only as hashes. Each user sees only their own files.
- An **admin** account is created the first time the server starts: username `adminUsername`, password `password`. Change it with `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env` before the first start. The server is reachable through a public Cloudflare tunnel, so do not keep the default password when sharing the URL.
- When signed in, folders, uploads and text (Settings → Files) are saved: content in MongoDB, an index row per item in Postgres (`indexDB`). Signed out, files are temporary.
- **Sorting and favorites** (Settings → Files): sort by Name, Date modified or Favorite, ascending or descending (folders always come first, as in `Sorter.py`). Use a file's ••• menu to add it to favorites; favorites show a ★ and are listed in the virtual **Favorites** folder. Only files can be favorites, and nothing can be created in Favorites. Editing a file's name or description updates its date modified; toggling a favorite does not.
- Not connected yet: the "Image & video encryption" setting (files are stored unencrypted), and email verification and password reset.

## Google Setup to use OAuth 

The Login dialog's **Continue with Google** button uses Google's OAuth 2.0 sign-in. It needs your own Google credentials, so it reports "not set up" until you add them:

1. In the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) create an **OAuth client ID** of type **Web application** (configure the OAuth consent screen first [PenAI, Redirect URL: http://localhost:8000/api/auth/google/callback]; then, go to Client and make the OAuth Client. Then, go to Audience and scroll below  "Testing" and add the Google accounts allowed to sign in as test users).
2. Put the credentials in a `.env` file next to `docker-compose.yml` (never commit it; `.env` is git-ignored).
   That is, (1) cp backend/Database/.env.example .env (2) open -e .env (3) and then put your clientID and credentials
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```
3. `docker compose up -d --build`, open http://localhost:8000 and use the button.

Behaviour: the first Google sign-in creates an account (username from the Google first name, made unique if taken; no password, so it can only sign in with Google). A Google account whose email already belongs to a password account is refused, with a message to sign in with that password. Sign-up does not verify emails yet, so linking by email automatically would let someone who registered another person's email take over their Google sign-in. Only emails that Google reports as verified are accepted. Each attempt is bound to the browser that started it (`state` cookie) and uses PKCE.

**Using it through the public Cloudflare tunnel:** Google only accepts redirect URIs you registered in advance, and the quick tunnel started by `main.py` gets a new random URL every time, so the sign-in only works on `http://localhost:8000` for now. For a public address, set up a Cloudflare *named* tunnel with a fixed hostname, register `https://your-hostname/api/auth/google/callback` in the Google console and set `GOOGLE_REDIRECT_URI` to that same URL in `.env`.

## Connecting to the databases

| | Postgres | MongoDB |
|---|---|---|
| From your computer | `localhost:5432`, user `postgres`, password `changeme` | `mongodb://localhost:27018` (MongoDB Compass) |
| From inside Docker | `postgres:5432` | `mongo:27017` |

- Postgres connection string: `postgresql://postgres:changeme@localhost:5432/<user_db | keyrecord_db | indexDB>`
- pgAdmin login: `admin@example.com` / `changeme`. The server **UserCredentials** is already registered; enter the Postgres password (`changeme`) when asked.
- In MongoDB Compass, name the connection **IMG_VID_TXT**. The database is **UserFiles**.
- MongoDB uses port **27018** on your computer, so it does not collide with a locally installed MongoDB on 27017. Connecting a GUI to 27017 shows your local database, not the Docker one.


# Run

1. [Terminal] (go to the directory of (in this case) CS499G5) (related: cd, ls)
2. [Terminal] run: docker compose up --build

Stop with `docker compose down` (keeps the data) or `docker compose down -v` (also deletes the Postgres, Mongo and pgAdmin data).


# Architecture

The backend follows clean architecture: source code dependencies only point inward.

```
backend/
  CommonErrors/    shared kernel: the errors every layer can raise (no HTTP knowledge)
  UserLogin/       accounts
    domain/          User entity, account rules (valid username/email, password strength)
    application/     UserManager (register, authenticate, Google sign-in) + Ports (UserRepository, PasswordHasher)
    infrastructure/  UserDatabaseAdapter (Postgres), ScryptPasswordHasher
  WI29_Server/     files, sessions, HTTP
    domain/          Folder / FileEntry, naming and file-type rules, size limit
    application/     FileService, AuthService, GoogleSignIn + Ports (repositories, content store, sessions, Google)
    infrastructure/  Postgres repositories, MongoDB content store, in-memory sessions/limiters, Google client, Settings
    interface/       FastAPI routers, request schemas, the error-to-HTTP-status mapping
    Container.py     composition root: the only place that builds the concrete classes
    httpAPI.py       builds the FastAPI app from the container; main.py starts uvicorn + the Cloudflare tunnel
```

- **domain** imports nothing from the other layers and does no I/O; **application** imports only the domain, the shared `CommonErrors` and the ports it defines (it reaches another context such as accounts through a port, never by importing its classes); **infrastructure** and **interface** implement/consume those ports and never import each other; only `Container.py` builds concrete infrastructure. `backend/tests/test_architecture.py` fails if an import breaks any of this.
- Use cases are tested against small in-memory fakes (`backend/tests/Fakes.py`), with no database: from the `backend` folder run `python -m pytest tests` (needs `pytest`). Swapping Postgres, MongoDB or Google means writing a new class for a port and changing `Container.py`.
- Business rules live in the use cases, not in the routes: for example, every sign-in gives the user their default folders (the `onSignedIn` hook that `Container.py` passes to `AuthService`), and listing files creates any that are missing.
- Frontend (`app/`), same direction of dependencies:
  - `domain/`: pure rules (sorting, unique names, upload checks); `types.ts` holds the shared data types.
  - `application/`: `ports.ts` (the `AuthGateway` / `FilesGateway` interfaces) and the hooks `useAuth` / `useFiles` (state and use cases). They never call `fetch`.
  - `infrastructure/`: `api.ts` (the only code that calls the server, implements the gateways) and `download.ts`.
  - `components/` and `hooks/useFileUrl.ts`: rendering only; components never import `infrastructure/api`.
  - `page.tsx` is the composition point: it passes `api` into the hooks.
  - `npm run check:architecture` fails on any import that points the wrong way.
- Errors: the application raises `CommonErrors.Errors` types; `interface/ErrorHandlers.py` is the one place that picks the HTTP status (e.g. duplicate username/email is **409**).

# Notes

- The schema is in `backend/Database/init/`. Postgres only runs these files on an **empty** volume. After editing them, run `docker compose down -v`, then `docker compose up --build`. This deletes the stored data.
- Content in Mongo is linked to Postgres by `index_entries.media_id` (= the GridFS file `_id`). See `backend/WI29_Server/infrastructure/MongoContentStore.py` and `PostgresFileRepositories.py`.
- If port 5432, 27018 or 5050 is already used on your computer, change it in `.env` (`POSTGRES_PORT`, `MONGO_PORT`, `PGADMIN_PORT`) or stop the other program. Port 8000 is set in `docker-compose.yml`.
- The default passwords (`changeme`) are for local development only.


# PROBLEMS AND SOLUTIONS

1. If your docker doesn't appear, try on the terminal: open -a Docker

