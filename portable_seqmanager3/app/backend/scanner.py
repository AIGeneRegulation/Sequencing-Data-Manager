from __future__ import annotations
import hashlib, os, time, json, re, shlex
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import psutil  # type: ignore
except Exception:
    psutil = None

# ---------- Normalization & bio sets ----------
BIO_CONTAINERS = {"GZIP", "BGZF"}
BIO_LOGICAL = {"BAM", "CRAM", "BCF", "VCF", "SAM", "FASTQ", "FASTA"}

def _norm_container(s: str) -> str:
    s = (s or "").upper()
    return {"GZ": "GZIP", "GZIP": "GZIP", "BGZ": "BGZF", "BGZF": "BGZF"}.get(s, s)

# ---------- Policy knobs (conservative defaults) ----------
PREFER_SRA_OVER_FASTQ = False   # if True, keep SRA and mark FASTQ erasable; else keep FASTQ and mark SRA erasable
ALLOW_SAM_REGEN = True          # allow suggesting deletion of .sam when .bam/.cram exist (SAM can be re-emitted)

# ---------- Data classes ----------
@dataclass(frozen=True)
class FileMeta:
    path: str
    size: int
    mtime_ns: int
    header_type: str              # bytes-derived container or concrete type
    ext_full: str                 # e.g. "fastq.gz"
    ext_container: str            # GZIP | BGZF | "" (none)
    ext_logical: str              # FASTQ | VCF | BAM | ... | ""

@dataclass
class ScanStats:
    wall_clock_s: float
    cpu_avg: Optional[float]
    cpu_peak: Optional[float]
    peak_rss_mb: Optional[int]

# ---------- Helpers ----------
_TOKEN_RE = re.compile(r"(?:^|[_\-\.])(r1|r2|read1|read2|paired|unpaired|trimmed|sorted|unsorted|collated)$", re.I)

def _base_stem(p: Path, ext_full_upper: str) -> str:
    """Derive a stable sample key by stripping multi-part extensions and common processing tokens."""
    name = p.name
    for suf in p.suffixes[::-1]:
        if suf: name = name[: -len(suf)]
    parts = re.split(r"[\.\-_]+", name)
    parts = [w for w in parts if w and not _TOKEN_RE.match(w)]
    return ".".join(parts).lower()

def _has(m: dict, kind: str) -> bool:
    return (m.get("header_type") == kind) or (m.get("extension_logical") == kind)

def _is_container(m: dict, kinds: Tuple[str, ...]) -> bool:
    return (m.get("extension_container") or "").upper() in kinds

def shlex_quote(s: str) -> str:
    return shlex.quote(s)

class SequencingFileScanner:
    """
    Scans a directory tree, classifies files by header signatures, and finds exact duplicates via:
      - size prefilter
      - sampled MD5 of 3×64 KiB windows (first/middle/last) for candidate buckets
      - full-file SHA-256 streaming verification (exact duplicates only)
    Also emits a bio-focused mismatch report and suggests erasable intermediates with regeneration commands.
    """

    def __init__(self, strict: bool = True, chunk_size_bytes: int = 4 * 1024 * 1024, include_non_bio_mismatches: bool = False):
        self.strict = strict
        self.chunk = int(chunk_size_bytes)
        self._cb = None
        self._cancel = False
        self.include_non_bio_mismatches = include_non_bio_mismatches

    # -------- progress ----------
    def set_progress_callback(self, cb): self._cb = cb
    def request_cancel(self): self._cancel = True
    def _emit(self, stage: str, scanned: int, total: int, path: Optional[str] = None):
        if not self._cb: return
        try:
            self._cb({"stage": stage, "scanned": scanned, "total": total, "path": path})
        except Exception:
            pass

    # -------- extension parsing ----------
    @staticmethod
    def _normalize_extensions(p: Path) -> Tuple[str, str, str]:
        """
        Returns (ext_full, ext_container, ext_logical)
          ext_full: dotted suffixes lowercased, e.g. "fastq.gz", "vcf.bgzf", "bam"
          ext_container: "GZIP" | "BGZF" | "" (none)
          ext_logical: "FASTQ" | "VCF" | "FASTA" | "SAM" | "BAM" | "CRAM" | "BCF" | ""
        """
        suffixes = [s.lstrip(".").lower() for s in p.suffixes]  # e.g. ["fastq","gz"]
        ext_full = ".".join(suffixes)
        container = ""
        logical = ""
        if suffixes:
            last = suffixes[-1]
            if last in ("gz", "gzip"):
                container = "GZIP"
            elif last in ("bgz", "bgzf"):
                container = "BGZF"
            elif last in ("bam", "cram", "bcf", "vcf", "sam", "fastq", "fq", "fasta", "fa"):
                logical_map = {
                    "bam":"BAM","cram":"CRAM","bcf":"BCF","vcf":"VCF",
                    "sam":"SAM","fastq":"FASTQ","fq":"FASTQ","fasta":"FASTA","fa":"FASTA",
                }
                logical = logical_map.get(last, last.upper())
            if container and len(suffixes) >= 2:
                prev = suffixes[-2]
                logical_map = {
                    "bam":"BAM","cram":"CRAM","bcf":"BCF","vcf":"VCF",
                    "sam":"SAM","fastq":"FASTQ","fq":"FASTQ","fasta":"FASTA","fa":"FASTA",
                }
                logical = logical_map.get(prev, logical or "")
        container = _norm_container(container)
        return (ext_full, container, logical)

    # -------- header sniffer ----------
    def sniff_header(self, p: Path) -> str:
        try:
            with p.open("rb") as f:
                head = f.read(1024)
                # GZIP (BGZF is a GZIP variant; not parsing subfields here)
                if len(head) >= 3 and head[0] == 0x1F and head[1] == 0x8B and head[2] == 0x08:
                    return "GZIP"
                if head[:4] == b"BAM\x01":
                    return "BAM"
                if head[:4] == b"CRAM":
                    return "CRAM"
                if head[:3] == b"BCF":
                    return "BCF"
                if b"##fileformat=VCF" in head[:256]:
                    return "VCF"
                if head.startswith(b"@HD\t"):
                    return "SAM"
                if head[:1] == b"@":
                    return "FASTQ"
                if head[:1] == b">":
                    return "FASTA"
        except Exception:
            return "UNKNOWN"
        # Read succeeded but no known signature → do not guess from name
        return "UNKNOWN"

    # -------- fingerprints ----------
    def sampled_fingerprint(self, p: Path) -> str:
        S = p.stat().st_size
        h = hashlib.md5()
        with p.open("rb") as f:
            h.update(f.read(65536))
            if S >= 196608:
                mid = S // 2
                f.seek(max(0, mid - 32768))
                h.update(f.read(65536))
            if S >= 65536:
                f.seek(max(0, S - 65536))
                h.update(f.read(65536))
        return h.hexdigest()

    def stream_hash(self, p: Path, algo: str = "sha256") -> str:
        h = hashlib.new(algo)
        with p.open("rb") as f:
            while True:
                chunk = f.read(self.chunk)
                if not chunk: break
                h.update(chunk)
        return h.hexdigest()

    # -------- main ----------
    def scan_directory(self, root: str) -> Dict:
        start = time.perf_counter()
        cpu_samples: List[float] = []
        peak_rss_mb: Optional[int] = None
        proc = psutil.Process(os.getpid()) if psutil else None

        rootp = Path(root).expanduser().resolve()
        if not rootp.exists():
            raise FileNotFoundError(f"Scan root does not exist: {rootp}")

        # count for progress
        total = 0
        for _, _, files in os.walk(rootp):
            total += len(files)

        metas: List[FileMeta] = []
        scanned = 0

        for dirpath, _dirs, files in os.walk(rootp):
            d = Path(dirpath)
            for fn in files:
                if self._cancel: break
                p = (d / fn).resolve()
                try:
                    st = p.stat()
                    header = self.sniff_header(p)
                    ext_full, ext_container, ext_logical = self._normalize_extensions(p)
                    metas.append(FileMeta(
                        path=str(p),
                        size=int(st.st_size),
                        mtime_ns=int(st.st_mtime_ns),
                        header_type=header,
                        ext_full=ext_full.upper(),            # e.g. FASTQ.GZ
                        ext_container=ext_container,          # e.g. GZIP
                        ext_logical=ext_logical,              # e.g. FASTQ
                    ))
                except Exception:
                    pass

                scanned += 1
                if scanned % 100 == 0 or scanned == total:
                    self._emit("classify", scanned, total, str(p))

            if proc:
                try:
                    cpu = proc.cpu_percent(interval=0.0)
                    cpu_samples.append(cpu)
                    rss = int(proc.memory_info().rss // (1024 * 1024))
                    peak_rss_mb = rss if (peak_rss_mb is None or rss > peak_rss_mb) else peak_rss_mb
                except Exception:
                    pass
            if self._cancel: break

        # --- duplicates ---
        self._emit("dedup_tier0", scanned, total)

        by_size: Dict[int, List[FileMeta]] = {}
        for m in metas:
            if m.size > 0:
                by_size.setdefault(m.size, []).append(m)

        by_fp: Dict[Tuple[int, str], List[FileMeta]] = {}
        for size, group in by_size.items():
            if len(group) < 2:
                continue
            for m in group:
                try:
                    fp = self.sampled_fingerprint(Path(m.path))
                except Exception:
                    fp = "ERR"
                by_fp.setdefault((size, fp), []).append(m)

        self._emit("dedup_tier2", scanned, total)
        groups: Dict[str, List[FileMeta]] = {}
        for (_sz, _fp), bucket in by_fp.items():
            if len(bucket) < 2:
                continue
            for m in bucket:
                try:
                    sha = self.stream_hash(Path(m.path), "sha256")
                except Exception:
                    continue
                groups.setdefault(sha, []).append(m)

        dup_out = []
        for sha, group in groups.items():
            if len(group) < 2:
                continue
            paths = sorted(g.path for g in group)
            total_size = group[0].size * len(group)
            dup_out.append({"sha256": sha, "total_size": total_size, "count": len(group), "files": paths})
        dup_out.sort(key=lambda d: (d["total_size"], d["count"]), reverse=True)

        wall = max(0.0, time.perf_counter() - start)
        stats = ScanStats(
            wall_clock_s=wall,
            cpu_avg=(sum(cpu_samples)/max(1,len(cpu_samples))) if cpu_samples else None,
            cpu_peak=(max(cpu_samples) if cpu_samples else None),
            peak_rss_mb=peak_rss_mb,
        )

        # --- mismatches (bio-focused, container-aware) ---
        mismatches = []
        for m in metas:
            header = (m.header_type or "").upper()
            ext_container = _norm_container(m.ext_container)
            ext_logical = (m.ext_logical or "").upper()

            if header in ("UNKNOWN", ""):
                continue  # don't report unknowns as mismatches

            header_is_bio = (header in BIO_LOGICAL) or (header in BIO_CONTAINERS)
            name_is_bio   = (ext_logical in BIO_LOGICAL) or (ext_container in BIO_CONTAINERS)
            if not self.include_non_bio_mismatches and not (header_is_bio or name_is_bio):
                continue  # hide PDFs, DOCX, scripts, etc.

            if header in BIO_CONTAINERS:
                is_mismatch = ext_container not in BIO_CONTAINERS
            else:
                if ext_container in BIO_CONTAINERS:
                    is_mismatch = True
                else:
                    is_mismatch = (header != ext_logical) if header else False

            if is_mismatch:
                mismatches.append({
                    "path": m.path,
                    "extension": m.ext_full,
                    "extension_container": ext_container,
                    "extension_logical": ext_logical,
                    "header_type": header,
                })

        # ---------- Erasable intermediates (conservative) ----------
        files_out: List[dict] = [{
            "path": m.path,
            "size": m.size,
            "header_type": m.header_type,
            "extension": m.ext_full,
            "extension_container": m.ext_container,
            "extension_logical": m.ext_logical,
        } for m in metas]

        by_sample: Dict[str, List[dict]] = {}
        for rec in files_out:
            stem = _base_stem(Path(rec["path"]), rec["extension"])
            by_sample.setdefault(stem, []).append(rec)

        erasable_candidates: List[dict] = []
        for stem, items in by_sample.items():
            has_cram   = any(_has(x, "CRAM") for x in items)
            has_bam    = any(_has(x, "BAM") and not _is_container(x, ("GZIP","BGZF")) for x in items)
            has_bam_any= any(_has(x, "BAM") for x in items)
            has_sam    = any(_has(x, "SAM") for x in items)
            fastqs     = [x for x in items if _has(x, "FASTQ")]
            has_sra    = any(str(x["extension"]).upper().endswith("SRA") for x in items)

            # 1) SAM erasable if BAM or CRAM exist
            if ALLOW_SAM_REGEN and has_sam and (has_bam_any or has_cram):
                for x in items:
                    if _has(x, "SAM"):
                        if has_bam_any:
                            bam = next(y for y in items if _has(y, "BAM"))
                            erasable_candidates.append({
                                "path": x["path"],
                                "reason": "SAM is an intermediate; re-emit from BAM",
                                "fidelity": "content-equivalent (order may differ)",
                                "depends_on": [bam["path"]],
                                "regen_cmd": f"samtools view -h {shlex_quote(bam['path'])} > {shlex_quote(x['path'])}",
                            })
                        else:
                            cram = next(y for y in items if _has(y, "CRAM"))
                            erasable_candidates.append({
                                "path": x["path"],
                                "reason": "SAM is an intermediate; re-emit from CRAM",
                                "fidelity": "content-equivalent (requires reference)",
                                "depends_on": [cram["path"], "<ref.fa>"],
                                "regen_cmd": f"samtools view -h -T <ref.fa> {shlex_quote(cram['path'])} > {shlex_quote(x['path'])}",
                            })

            # 2) Uncompressed BAM erasable if CRAM exists
            if has_bam and has_cram:
                cram = next(y for y in items if _has(y, "CRAM"))
                for b in [x for x in items if _has(x, "BAM") and not _is_container(x, ("GZIP","BGZF"))]:
                    erasable_candidates.append({
                        "path": b["path"],
                        "reason": "BAM superseded by CRAM; reconstructable from CRAM",
                        "fidelity": "content-equivalent (coordinate order preserved if CRAM is sorted)",
                        "depends_on": [cram["path"], "<ref.fa>"],
                        "regen_cmd": f"samtools view -b -T <ref.fa> -o {shlex_quote(b['path'])} {shlex_quote(cram['path'])}",
                    })

            # 3) SRA vs FASTQ(.gz)
            if has_sra and fastqs:
                if PREFER_SRA_OVER_FASTQ:
                    for fq in fastqs:
                        erasable_candidates.append({
                            "path": fq["path"],
                            "reason": "FASTQ re-derivable from retained SRA",
                            "fidelity": "tool-deterministic (fasterq-dump + pigz)",
                            "depends_on": ["<SRA_ACCESSION>"],
                            "regen_cmd": "fasterq-dump --split-files SRRXXXXXX && pigz -p N *.fastq",
                        })
                else:
                    sra = next(x for x in items if str(x["extension"]).upper().endswith("SRA"))
                    erasable_candidates.append({
                        "path": sra["path"],
                        "reason": "SRA redundant when gzipped FASTQ is retained locally",
                        "fidelity": "content-equivalent (tool-dependent container)",
                        "depends_on": [fq["path"] for fq in fastqs],
                        "regen_cmd": "n/a (keep FASTQ as canonical raw layer)",
                    })

            # 4) Trimmed FASTQ erasable if raw FASTQ present (and ideally manifest)
            raw_fq = [fq for fq in fastqs if "trimmed" not in Path(fq["path"]).name.lower()]
            trimmed_fq = [fq for fq in fastqs if "trimmed" in Path(fq["path"]).name.lower()]
            if raw_fq and trimmed_fq:
                manifest = None
                for c in items:
                    if str(c["path"]).lower().endswith(".manifest.json"):
                        manifest = c["path"]; break
                for tfq in trimmed_fq:
                    erasable_candidates.append({
                        "path": tfq["path"],
                        "reason": "Trimmed FASTQ is re-derivable from raw FASTQ with recorded parameters",
                        "fidelity": "content-equivalent given pinned tool and params",
                        "depends_on": [raw_fq[0]["path"]] + ([manifest] if manifest else []),
                        "regen_cmd": "cutadapt <params_from_manifest> -o out.fq.gz raw.fq.gz",
                    })

        return {
            "n_files": len(metas),
            "stats": asdict(stats),
            "mismatches": mismatches,
            "files": files_out,
            "duplicate_groups": dup_out,
            "erasable_candidates": erasable_candidates,
        }

# CLI support
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Portable SeqManager scanner")
    ap.add_argument("root", help="Root directory to scan")
    ap.add_argument("--json", dest="json_out", help="Write JSON result file")
    args = ap.parse_args()
    sc = SequencingFileScanner(strict=True)
    res = sc.scan_directory(args.root)
    s = json.dumps(res, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(s)
        print(f"Wrote {args.json_out}")
    else:
        print(s)
