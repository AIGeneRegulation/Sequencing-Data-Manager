# Sequencing Data Manager

A portable web app and CLI that scans storage for sequencing data, **classifies files by header bytes**, finds **exact duplicates** safely, flags **header/extension mismatches**, and suggests **erasable intermediates** with ready-to-run regeneration commands.

- Backend: FastAPI (Python 3.11)
- Frontend: single HTML/JS page (no framework)
- Container: Dockerfile + docker-compose
- Runs on macOS/Linux/Windows

##  Features

- **Header-based typing**: BAM (`BAM\x01`), CRAM, BCF/VCF signatures, SAM prologues, FASTQ/FASTA markers, GZIP/BGZF.
- **Exact dedup**: size → sampled 3×64 KiB MD5 (candidate filter) → streamed **SHA-256** confirmation.
- **Mismatch report**: flags misleading filenames; ignores non-bio files unless you opt in.
- **Erasable intermediates**: conservative suggestions (e.g., SAM when BAM/CRAM exist; BAM when CRAM exists; SRA vs FASTQ; trimmed FASTQ if raw+manifest), with commands to regenerate.
- **Progress UI**: live status, ETA, KPIs, tables (filterable), CSV/JSON export.

##  Requirements

- Python 3.11+ (or Docker)
- pip (to run locally)

##  Quick start

1) Clone this repo
git clone https://github.com/AIGeneRegulation/Sequencing-Data-Manager.git
cd Sequencing-Data-Manager

2) Point DATA_PATH at the folder you want to scan (must be shared in Docker Desktop on macOS)
export DATA_PATH="$HOME/datasets"   # use an absolute path under /Users on macOS
mkdir -p "$DATA_PATH"

3) Build & run
docker compose up --build -d

4) Open the UI
http://localhost:5000
In the "Root path" box, use /data (or /data/subfolder), which maps to $DATA_PATH inside the container.

## Without docker

1) Clone
git clone https://github.com/AIGeneRegulation/Sequencing-Data-Manager.git
cd Sequencing-Data-Manager

2) Create venv and install deps
python -m venv .venv
source .venv/bin/activate                # Windows: .venv\Scripts\activate
pip install -r requirements.txt

3) Run the app
uvicorn app.backend.main:app --reload --port 5000

4) Open the UI
http://localhost:5000
Enter the full local path you want to scan (e.g., /Users/you/project/data)

## CLI

prints JSON to stdout or writes to a file with --json
python -m app.backend.scanner /path/to/scan --json result.json


