# Installation Instructions

## Requirements
- Python 3.10 or newer (the code uses `X | None` type hints)
- MongoDB running on `localhost:27017` (the address is set in `Database.py`)
- Python packages: `pymongo` and `pillow`

## 1. Install Python
**Windows:** Download Python 3.10+ from https://www.python.org/downloads/ and tick **"Add python.exe to PATH"** during setup.

**macOS:**
```bash
brew install python
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```
On Fedora, use `sudo dnf install python3`.

## 2. Install and start MongoDB
The **EASIEST** way on any system is Docker (https://docs.docker.com/get-docker/):
```bash
docker run -d --name mongo -p 27017:27017 mongo
```
Or install it natively:

**Windows:** Install MongoDB Community Server from https://www.mongodb.com/try/download/community. Choose "Run as a Service" in the installer so it starts automatically.

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```
For macos, [Without Docker]
1. Change your directory to mongodb-macos-x86_64-enterprise--8.3.8 (you may need to dig around)
2. change directory: cd bin
3. start the server: ./mongod --dbpath ~/data/db

**Linux:** Follow the official guide for your distribution: https://www.mongodb.com/docs/manual/administration/install-on-linux/. Then:
```bash
sudo systemctl start mongod
```

## 3. Set up the project
Open a terminal in the `WI7` folder.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pymongo pillow
```

**Windows (PowerShell):**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install pymongo pillow
```
In Command Prompt, activate with `.venv\Scripts\activate.bat` instead. If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.


## 4. Running the DB server

Make a new terminal, outside of this IDE, such that the directory is global. Go ahead and run this:

### MacOS

1. Change directory to something like mongodb-macos-x86_64-enterprise--8.3.8 (based on OS)
2. Go to the bin folder of said folder
3. Start the server: ./mongod --dbpath ~/data/db

### Linux

If MongoDB was installed via a package manager (see step 2), it runs as a service:
```bash
sudo systemctl start mongod
sudo systemctl status mongod    # confirm it is "active (running)"
```
To start it automatically on boot: `sudo systemctl enable mongod`.

If you downloaded the MongoDB tarball instead (no service):
1. Change directory to the extracted folder, e.g. `mongodb-linux-x86_64-...`
2. Go to the `bin` folder
3. Create the data folder once: `mkdir -p ~/data/db`
4. Start the server: `./mongod --dbpath ~/data/db`

### Windows

If you chose "Run as a Service" during installation, MongoDB is already running. Check from PowerShell (as Administrator):
```powershell
Get-Service MongoDB
Start-Service MongoDB    # only if it is not running
```

If you did not install it as a service:
1. Open Command Prompt or PowerShell
2. Change directory to the MongoDB bin folder, e.g. `cd "C:\Program Files\MongoDB\Server\8.0\bin"` (the version number may differ)
3. Create the data folder once: `mkdir C:\data\db`
4. Start the server: `.\mongod.exe --dbpath C:\data\db`

Leave this terminal open while using the program.

## 5. Running the program
On Windows use `python` or `py` in place of `python3`.

```bash
python3 main.py --a --i file1.pdf file2.txt    # add one or more files
python3 main.py --r --i file1.pdf              # retrieve and display
python3 main.py --d --i file1.pdf              # delete
python3 main.py --l                            # list the first 50 filenames
```

For further details of how to use this program, refer to the main.py's argument letters.



## Settings
- `config.py`: `TEST_MODE` (print progress and show retrieved files) and `LIST_LIMIT` (how many filenames `--l` lists).
- `Database.py`: `MONGODB_URI`, `DB_NAME`, `COLLECTION_NAME`.

## Troubleshooting
- **"ServerSelectionTimeoutError" or connection refused:** MongoDB isn't running. Start it (step 2) and check that port 27017 is free.
- **`python3` not found on Windows:** use `py` or `python`.
- **Linux, nothing opens for `--r`:** install a desktop viewer and `xdg-utils` (`sudo apt install xdg-utils`). Files open with `xdg-open`.