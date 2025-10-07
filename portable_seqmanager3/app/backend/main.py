from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pathlib import Path
import os, json, threading, queue, time, uuid

from .scanner import SequencingFileScanner

app = FastAPI()

# Serve the tiny UI
@app.get("/", response_class=HTMLResponse)
def index():
    here = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return HTMLResponse(here.read_text())

_jobs = {}  # job_id -> {"queue": q, "result": dict|None}

@app.post("/api/scan/start")
async def api_scan_start(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    root = (payload or {}).get("root") or os.environ.get("SCAN_ROOT", "/data")
    strict = bool((payload or {}).get("strict", True))

    # If SCAN_ROOT is set, enforce scanning under it (Docker mode). Otherwise allow any path (local mode).
    scan_root_env = os.environ.get("SCAN_ROOT")
    if scan_root_env:
        allowed = Path(scan_root_env).resolve()
        rp = Path(root).expanduser().resolve()
        if not str(rp).startswith(str(allowed)):
            return JSONResponse({"error": f"root must be under {allowed}"}, status_code=400)
    else:
        rp = Path(root).expanduser().resolve()

    job_id = uuid.uuid4().hex
    q: "queue.Queue[dict|None]" = queue.Queue(maxsize=256)
    _jobs[job_id] = {"queue": q, "result": None}

    def progress_cb(msg: dict):
        try: q.put_nowait(msg)
        except Exception: pass

    def run():
        try:
            sc = SequencingFileScanner(strict=strict)
            sc.set_progress_callback(progress_cb)
            result = sc.scan_directory(str(rp))
            _jobs[job_id]["result"] = result
            q.put_nowait({"stage": "done", "result": result})
        except Exception as e:
            q.put_nowait({"stage": "error", "error": str(e)})
        finally:
            q.put_nowait(None)  # sentinel

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}

@app.get("/api/scan/stream/{job_id}")
def api_scan_stream(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        return JSONResponse({"error": "unknown job_id"}, status_code=404)
    q = job["queue"]

    def gen():
        while True:
            item = q.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
            time.sleep(0.01)

    return StreamingResponse(gen(), media_type="text/event-stream")

@app.get("/api/scan/result/{job_id}")
def api_scan_result(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        return JSONResponse({"error": "unknown job_id"}, status_code=404)
    if job["result"] is None:
        return JSONResponse({"status": "running"}, status_code=202)
    return JSONResponse(job["result"])
