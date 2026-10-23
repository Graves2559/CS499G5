# WI29 Server

A small FastAPI backend served over ASGI by uvicorn.

FOR TESTING PURPOSES

For official purposes, use the README.md of the root folder. 

## Requirements

- Python 3.9+
- `fastapi`
- `uvicorn`

## Installation

It's recommended to use a virtual environment so these packages don't get installed globally.

### macOS

```bash
# from the WI29_Server directory
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install fastapi uvicorn
python3 -m pip install pycloudflared

```

### Linux

```bash
# from the WI29_Server directory
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn
```

> On Debian/Ubuntu, if `python3 -m venv` fails with a "venv not found" error, install it first:
> ```bash
> sudo apt install python3-venv
> ```

### Windows

**PowerShell:**
```powershell
# from the WI29_Server directory
python -m venv venv
venv\Scripts\Activate.ps1
pip install fastapi uvicorn
```

**Command Prompt:**
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install fastapi uvicorn
```

> If PowerShell blocks the activation script with an execution-policy error, run:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

## Tunneling Service (Cloudflare)

This server listens on plain HTTP (`0.0.0.0:8000`); [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (`cloudflared`) creates a public HTTPS tunnel to it so it's reachable from outside the local machine/network — unlike ngrok's free tier, it does not show a warning/interstitial page to visitors.

Do not install `cloudflared` through the virtual environment — it is a standalone system binary, not a Python package. Install it in a regular terminal **outside** of your IDE's venv.

### Installation

#### macOS

```bash
brew install cloudflare/cloudflare/cloudflared
```

#### Linux

```bash
# Debian/Ubuntu (apt)
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared
```

> If you're not on a Debian/Ubuntu-based distro, download the binary directly from the [cloudflared releases page](https://github.com/cloudflare/cloudflared/releases) instead.

#### Windows

```powershell
winget install --id Cloudflare.cloudflared
```

> Alternatively, download the `.exe` from the [cloudflared releases page](https://github.com/cloudflare/cloudflared/releases) and place it somewhere on your `PATH`.

### Usage

To easily verify that cloudflare does run, run the **program** [Running the Program](#running-the-program) 
While it is running, open a separate terminal and start a quick tunnel, via:
```bash
cloudflared tunnel --url http://localhost:8000
```

`cloudflared` will print a public forwarding URL, **e.g.**: https://random-words-here.trycloudflare.com

That URL is publicly reachable over HTTPS and forwards traffic to this server on port 8000, with no warning page shown to visitors.

> This quick-tunnel URL is randomly generated and changes every time the tunnel is restarted (likewise, ngrok). For a stable, named URL (e.g. `api.yourdomain.com`), you need a free Cloudflare account and a domain added to it, then run `cloudflared tunnel login`, `cloudflared tunnel create <name>`, configure a `config.yml` pointing at `http://localhost:8000`, and run `cloudflared tunnel run <name>` instead.


## Running the Program
With the virtual environment activated:

```bash
python3 main.py
```

python for Windows

This starts uvicorn, binding to `0.0.0.0:8000` so the server is reachable over the LAN or through the tunneling service.


# No longer used


## Using the Tunneling Service (ngrok)

Ensure that you add into your virtual environment this: python3 -m pip install pyngrok

This server listens on plain HTTP (`0.0.0.0:8000`); [ngrok](https://ngrok.com) creates a public HTTPS tunnel to it so it's reachable from outside the local machine/network.

### Installation

1. Go to [ngrok](https://ngrok.com) and sign up. 
2. Copy your authtoken from the ngrok dashboard.
3. Install ngrok (down below)

    Do not install ngrok through the virtual environment. Make a new terminal **outside** of your IDE (e.g., VSCode, etc.) and do the following below 
4. Register it with the CLI:
   ```bash
   ngrok config add-authtoken <your-token-here>
   ```

#### macOS

```bash
brew install ngrok/ngrok/ngrok
```
This is in the format of: brew install (tap-user)/(tap-repo)/(formula-name)

#### Linux

```bash
# Debian/Ubuntu (apt)
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

> If you're not on a Debian/Ubuntu-based distro, download the binary directly from the [ngrok downloads page](https://ngrok.com/download) instead.

#### Windows

```powershell
choco install ngrok
```

> Alternatively, download the `.zip` from the [ngrok downloads page](https://ngrok.com/download) and extract `ngrok.exe` somewhere on your `PATH`.


### Pyngrok Installation 
> `pyngrok` auto-downloads the `ngrok` binary the first time it runs, and may fail with a `CERTIFICATE_VERIFY_FAILED` error if Python's trusted certificates aren't set up correctly for your OS. If you hit that error, fix it for your OS first:

**macOS** — the python.org installer builds ship their own OpenSSL and don't trust the system CA store by default:
```bash
bash "/Applications/Python 3.11/Install Certificates.command"
```
> Adjust the version number in the path (e.g. `Python 3.12`) to match the Python version you installed.

**Windows** — usually only needed if you're behind a corporate proxy/antivirus doing TLS inspection:
```powershell
python -m pip install --upgrade certifi
```
> If that alone doesn't fix it, install `pip-system-certs` so Python trusts the Windows certificate store directly:
> ```powershell
> python -m pip install pip-system-certs
> ```

**Linux** — make sure the system CA bundle is installed and up to date:
```bash
sudo apt update && sudo apt install --reinstall ca-certificates   # Debian/Ubuntu
# or: sudo dnf reinstall ca-certificates                          # Fedora/RHEL
python3 -m pip install --upgrade certifi
```

